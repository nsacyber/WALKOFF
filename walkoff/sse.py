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
        formatted = 'id: {}\n'.format(event_id)
        if self.event:
            formatted += 'event: {}\n'.format(self.event)
        if retry is not None:
            formatted += 'retry: {}\n'.format(retry)
        if self.data:
            formatted += 'data: {}\n'.format(data)
        return formatted + '\n'


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

    def push(self, event=''):
        """Decorator to use to over a function which pushes data to the SSE stream.

        This function should return data formatted in the way it should appear to the client. If the stream should push
        JSON, then the function should return a `dict` (do not use json.dumps())

        Args:
            event (str, optional): The default event to use on this stream. This can be overwritten by returning a
                `tuple` of (data, event) from the decorated function. If no event is specified, no event will be appended
                to the Server-Sent Event

        Returns:
            (func): The decorated function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                response = func(*args, **kwargs)
                self._publish_response(response, event)
                return response
            return wrapper

        return decorator

    def _publish_response(self, response, default_event):
        """Publish a response to the SSE stream

        Args:
            response: The data from the SSE push function. If a tuple is returned, the second element is the event to
                use in the SSE stream instead of the event passed into this function
            default_event (str): The default event to use for this SSE stream.
        """
        if isinstance(response, tuple):
            self.publish(response[0], event=response[1])
        else:
            self.publish(response, event=default_event)

    def publish(self, data, **kwargs):
        """Publishes some data to the stream

        Args:
            data: The data to publish

        Keyword Args:
            event (str): The event associated with this data
        """
        self.cache.register_callbacks()
        response = {'data': data, 'event': kwargs.get('event', '')}
        self.cache.publish(self.channel, response)

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
        return Response(self.send(retry=retry, **kwargs),
                        mimetype='text/event-stream', headers=stream_headers)

    def unsubscribe(self, **kwargs):
        """Unsubscribe from and close this stream
        """
        self.cache.publish(self.channel, unsubscribe_message)

    def subscribe(self, **kwargs):
        """Subscribes to a given channel

        Args:
            **kwargs: Unused

        Returns:
            (DiskSubscription): The subscription for this channel
        """
        return self.cache.subscribe(self.channel)

    def send(self, retry=None, **kwargs):
        """Sends data through the SSE stream to the client.

        This function is primarily used by the `stream` function to generate the Response object

        Args:
            retry (int): The time in milliseconds the client should wait to retry to connect to this SSE stream if the
                connection is broken. Default is 3 seconds (3000 milliseconds)

        Yields:
            (str): The string to push through the SSE stream to the client
        """
        channel_queue = self.subscribe(**kwargs)

        event_id = 0
        for response in channel_queue.listen():
            data, event = response['data'], response['event']
            sse = SseEvent(event, data)
            event_id += 1
            yield sse.format(event_id, retry=retry)


class FilteredSseStream(SseStream):
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
        super(FilteredSseStream, self).__init__(channel, cache)

    def _publish_response(self, response, default_event):
        """Publish a response to the filtered SSE stream.

        Args:
            response (tuple): Can either take the form of (data, subchannel(s)) or (data, subchannel(s), event).
                The data should be formatted in the way it should appear to the client. If the stream should push JSON,
                then the function should return a `dict` (do not use json.dumps()). The subchannels to push the data to
                can be an identifier or an iterable of identifiers to publish to the subchannel or subchannels.  The
                subchannel identifier should be something which can be quickly converted to a string. If a `tuple` of
                (data, subchannel(s), event) is returned, then that event is used instead of the default_event argument.
            default_event (str): The default event to use on this stream. This can be overwritten by returning a
                `tuple` of (data, subchannel, event) from the decorated function. If no event is specified, then no
                even will be appended to the Server-Sent Event
        """
        if len(response) > 2:
            self.publish(response[0], subchannels=response[1], event=response[2])
        else:
            self.publish(response[0], subchannels=response[1], event=default_event)

    def publish(self, data, **kwargs):
        self.cache.register_callbacks()
        subchannels = kwargs.get('subchannels', [])
        data = {'data': data, 'event': kwargs.get('event', '')}
        if not isinstance(subchannels, string_types) and isinstance(subchannels, collections.Iterable):
            for subchannel in subchannels:
                self.cache.publish(self.create_subchannel_name(subchannel), data)
        else:
            self.cache.publish(self.create_subchannel_name(subchannels), data)

    def create_subchannel_name(self, subchannel):
        """Creates a unique name for a subchannel

        Args:
            subchannel: The subchannel whose name should be created.

        Returns:
            str: The name of the subchannel
        """
        return '{0}.{1}'.format(self.channel, subchannel)

    def subscribe(self, **kwargs):
        return self.cache.subscribe(self.create_subchannel_name(kwargs.get('subchannel', '')))

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
        return Response(self.send(retry=retry, subchannel=subchannel),
                        mimetype='text/event-stream', headers=stream_headers)

    def unsubscribe(self, subchannel):
        """Unsubscribe from and close this stream

        Args:
            subchannel: The subchannel id
        """
        self.cache.publish(self.create_subchannel_name(subchannel), unsubscribe_message)


def create_interface_channel_name(interface, channel):
    """Creates a unique channel name for an SSE stream for an interface.

    This is used to avoid name collisions between interfaces

    Args:
        interface (str): The name of the interface
        channel (str): The name of the channel

    Returns:

    """
    return '{0}::{1}'.format(interface, channel)


class InterfaceSseStream(SseStream):
    """An SSE Stream used for interfaces

    Attributes:
        interface (str): The name of the interface

    Args:
        interface (str): The name of the interface
        channel (str): The name of the channel
        cache (optional): The cache object used for this SSE stream
    """
    def __init__(self, interface, channel, cache=None):
        super(InterfaceSseStream, self).__init__(create_interface_channel_name(interface, channel), cache=cache)
        self.interface = interface


class FilteredInterfaceSseStream(FilteredSseStream):
    """A filtered SSE Stream used for interfaces

    Attributes:
        interface (str): The name of the interface

    Args:
        interface (str): The name of the interface
        channel (str): The name of the channel
        cache (optional): The cache object used for this SSE stream
    """
    def __init__(self, interface, channel, cache=None):
        super(FilteredInterfaceSseStream, self).__init__(create_interface_channel_name(interface, channel), cache=cache)
        self.interface = interface
