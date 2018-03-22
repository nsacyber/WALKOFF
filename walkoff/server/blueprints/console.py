from flask import Blueprint, Response
from walkoff.security import jwt_required_in_query
from walkoff.console.callbacks import console_event_stream

console_page = Blueprint('console', __name__)

@console_page.route('/log', methods=['GET'])
@jwt_required_in_query('access_token')
def stream_console_events():
    return Response(console_event_stream(), mimetype='text/event-stream')



