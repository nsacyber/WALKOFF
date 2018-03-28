from walkoff.events import WalkoffEvent
from walkoff.security import jwt_required_in_query
from walkoff.sse import SseStream, StreamableBlueprint
import logging

console_stream = SseStream('console_results')
console_page = StreamableBlueprint('console_page', __name__, streams=(console_stream,))


def format_console_data(sender, **kwargs):
    result = {}
    data = kwargs["data"]

    result["workflow"] = sender["name"]
    result["app_name"] = data["app_name"]
    result["action_name"] = data["action_name"]
    result["level"] = logging.getLevelName(data["level"])
    result["message"] = data["message"]
    return result


@WalkoffEvent.ConsoleLog.connect
@console_stream.push('log')
def console_log_callback(sender, **kwargs):
    return format_console_data(sender, **kwargs)


@console_page.route('/log', methods=['GET'])
@jwt_required_in_query('access_token')
def stream_console_events():
    return console_stream.stream()



