import walkoff.cache
from functools import wraps
from flask import Response


class SseEvent(object):
    def __init__(self, event, data):
        self.event = event
        self.data = data

    def format(self, event_id):
        return 'id: {0}\nevent: {1}\ndata{2}\n\n'.format(event_id, self.event, self.data)


class SseStream(object):

    def __init__(self, channel, cache=None):
        self.channel = channel
        if cache is None:
            self.cache = walkoff.cache.cache
        else:
            self.cache = cache

    def push(self, event=''):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                response = func(*args, **kwargs)
                if isinstance(response, tuple):
                    response = {'data': response[0], 'event': response[1]}
                else:
                    response = {'data': response, 'event': event}
                self.cache.publish(self.channel, response)

            return wrapper

        return decorator

    def stream(self, send_filter=None):
        return Response(self.send(send_filter), mimetype='text/event-stream')

    def send(self, send_filter):
        channel_queue = self.cache.subscribe(self.channel)
        with_filter = send_filter is not None
        event_id = 0
        for event, data in channel_queue.listen():
            sse = SseEvent(event, data)
            if with_filter:
                result = send_filter(sse)
                if result:
                    event_id += 1
                    yield result.format(event_id)
            else:
                event_id += 1
                yield sse.format(event_id)
