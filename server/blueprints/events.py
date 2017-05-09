import json
from flask import Blueprint, request
from flask_security import auth_token_required, roles_accepted
from server.flaskserver import running_context
import core.case.database as case_database
from server import forms


events_page = Blueprint('events_page', __name__)

@events_page.route('/<int:event_id>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def edit_event_note(event_id):
    form = forms.EditEventForm(request.form)
    if form.validate():
        if form.note.data:
            valid_event_id = case_database.case_db.session.query(case_database.Event) \
                .filter(case_database.Event.id == event_id).all()
            if valid_event_id:
                case_database.case_db.edit_event_note(event_id, form.note.data)
                return json.dumps(case_database.case_db.event_as_json(event_id))
            else:
                return json.dumps({"status": "invalid event"})
    else:
        return json.dumps({"status": "Invalid form"})

