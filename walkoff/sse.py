import walkoff.cache
from functools import wraps
from flask import Response
import json
from walkoff.cache import unsubscribe_message
import collections
from six import string_types

class SseEvent(object):
    """Class which creates and formats Server-Sent Events

    Attributes:
        event (str): The event of this SSE
        data: The data related to this SSE

    Args:
        event (str): The event of this SSE
        data: The data related to this SSE

    """
    def __init__(self, event, data):
        self.event = event
        self.data = data

    @staticmethod
    def __convert_dict(data):
        try:
            return json.dumps(data)
        except TypeError:
            return str(data)

    def format(self, event_id, retry=None):
        """Get this SSE formatted as needed to send to the client

        Args:
            event_id (int): The ID related to this event.
            retry (int): The time in milliseconds the client should wait to retry to connect to this SSE stream if the
                connection is broken. Default is 3 seconds (3000 milliseconds)

        Returns:
            (str): This SSE formatted to be sent to the client
        """
        if isinstance(self.data, dict):
            data = SseEvent.__convert_dict(self.data)
        else:
            data = self.data
        formatted = 'id: {0}\nevent: {1}\n'.format(event_id, self.event, data)
        if retry is not None:
            formatted += 'retry: {}\n'.format(retry)
        return formatted + 'data: {}\n\n'.format(data)


class SseStream(object):
    """A class to help push data across an Server-Sent Event stream.

    Attributes:
        channel (str): The name of the channel to push the events through
        cache (:obj:, optional): The cache to use for this SSE stream. Defaults to the `walkoff.cache.cache` used
            throughout Walkoff
        _default_headers (dict): The default headers to use in the response.

    Args:
        channel (str): The name of the channel to push the events through
        cache (:obj:, optional): The cache to use for this SSE stream. Defaults to the `walkoff.cache.cache` used
            throughout Walkoff
    """
    def __init__(self, channel, cache=None):
        self.channel = channel
        if cache is None:
            self.cache = walkoff.cache.cache
        else:

            self.cache = cache
        self._default_headers = {'Cache-Control': 'no-cache', 'Connection': 'keep-alive'}

    def push(self, event):
        """Decorator to use to over a function which pushes data to the SSE stream.

        This function should return data formatted in the way it should appear to the client. If the stream should push
        JSON, then the function should return a `dict` (do not use json.dumps())

        Args:
            event (str): The default event to use on this stream. This can be overwritten by returning a `tuple` of
                (data, event) from the decorated function.

        Returns:
            (func): The decorated function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                self.cache.register_callbacks()
                response = func(*args, **kwargs)
                if isinstance(response, tuple):
                    response = {'data': response[0], 'event': response[1]}
                else:
                    response = {'data': response, 'event': event}
                self.cache.publish(self.channel, response)
                return response
            return wrapper

        return decorator

    def stream(self, headers=None, retry=None, **kwargs):
        """Returns a response used by Flask to create an SSE stream.

        This function should be called as the return from a Flask view function

        Args:
            headers (dict): The headers to use for this steam. Some default headers are included by in the
                `_default_headers` attribute, but can be overwritten.
            retry (int): The

        Returns:
            (Response): A Flask Response object which creates the SSE stream

        """
        stream_headers = self._default_headers
        if headers:
            stream_headers.update(headers)
        return Response(self.send(retry=retry),
                        mimetype='text/event-stream', headers=stream_headers)

    def unsubscribe(self, **kwargs):
        """Unsubscribe from and close this stream
        """
        self.cache.publish(self.channel, unsubscribe_message)

    def send(self, retry=None, **kwargs):
        """Sends data through the SSE stream to the client.

        This function is primarily used by the `stream` function to generate the Response object

        Args:
            retry (int): The time in milliseconds the client should wait to retry to connect to this SSE stream if the
                connection is broken. Default is 3 seconds (3000 milliseconds)

        Yields:
            (str): The string to push through the SSE stream to the client
        """
        channel_queue = self.cache.subscribe(self.channel)

        event_id = 0
        for response in channel_queue.listen():
            data, event = response['data'], response['event']
            sse = SseEvent(event, data)
            event_id += 1
            yield sse.format(event_id, retry=retry)


class SimpleFilteredSseStream(SseStream):
    """A class to help filter and push data across an Server-Sent Event stream.

    The primary difference between this class and SseStream class is that it creates multiple subchannel constructed
    from the base name of the channel and an identifier created at runtime by the push decorator. The stream is then
    only attached to one subchannel.

    Args:
        channel (str): The base name of the channel to push the events through
        cache (:obj:, optional): The cache to use for this SSE stream. Defaults to the `walkoff.cache.cache` used
            throughout Walkoff
    """
    def __init__(self, channel, cache=None):
        super(SimpleFilteredSseStream, self).__init__(channel, cache)

    def push(self, event):
        """Decorator to use to over a function which pushes data to the SSE stream.

        This function should return data formatted in the way it should appear to the client as well as an identifier or
        an iterable of identifiers to publish to the subchannel or subchannels. If the stream should push JSON, then the
        function should return a `dict` (do not use json.dumps()). The subchannel identifier should be something which
        can be quickly converted to a string. If a `tuple` of (data, subchannel_ids) is returned, then the event passed
        into the decorator will be used. If a `tuple` of (data, subchannel_id, event) is returned, then that event is
        used.

        Args:
            event (str): The default event to use on this stream. This can be overwritten by returning a `tuple` of
                (data, subchannel, event) from the decorated function.

        Returns:
            (func): The decorated function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                self.cache.register_callbacks()
                response = func(*args, **kwargs)
                if len(response) > 2:
                    data = {'data': response[0], 'event': response[2]}
                else:
                    data = {'data': response[0], 'event': event}

                subchannels = response[1]
                if not isinstance(subchannels, string_types) and isinstance(subchannels, collections.Iterable):
                    for subchannel in response[1]:
                        self.cache.publish(self.create_channel_name(subchannel), data)
                else:
                    self.cache.publish(self.create_channel_name(subchannels), data)

                return response
            return wrapper

        return decorator

    def create_channel_name(self, subchannel):
        return '{0}.{1}'.format(self.channel, subchannel)

    def stream(self, subchannel='', headers=None, retry=None):
        """Returns a response used by Flask to create an SSE stream.

        This function should be called as the return from a Flask view function

        Args:
            subchannel: The subchannel id
            headers (dict): The headers to use for this steam. Some default headers are included by in the
                `_default_headers` attribute, but can be overwritten.
            retry (int): The

        Returns:
            (Response): A Flask Response object which creates the SSE stream

        """
        stream_headers = self._default_headers
        if headers:
            stream_headers.update(headers)
        return Response(self.send(subchannel, retry=retry),
                        mimetype='text/event-stream', headers=stream_headers)

    def unsubscribe(self, subchannel):
        """Unsubscribe from and close this stream

        Args:
            subchannel: The subchannel id
        """
        self.cache.publish(self.create_channel_name(subchannel), unsubscribe_message)

    def send(self, subchannel='', retry=None):
        """Sends data through the SSE stream to the client.

        This function is primarily used by the `stream` function to generate the Response object

        Args:
            subchannel: The subchannel id
            retry (int): The time in milliseconds the client should wait to retry to connect to this SSE stream if the
                connection is broken. Default is 3 seconds (3000 milliseconds)

        Yields:
            (str): The string to push through the SSE stream to the client
        """
        channel_queue = self.cache.subscribe(self.create_channel_name(subchannel))

        event_id = 0
        for response in channel_queue.listen():
            data, event = response['data'], response['event']
            sse = SseEvent(event, data)
            event_id += 1
            yield sse.format(event_id, retry=retry)
