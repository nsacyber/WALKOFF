from flask_security import auth_token_required, roles_accepted
import core.case.database as case_database


def edit_event_note(event_id, note):
    from server.context import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        valid_event_id = case_database.case_db.session.query(case_database.Event) \
            .filter(case_database.Event.id == event_id).all()
        if valid_event_id:
            case_database.case_db.edit_event_note(event_id, note['note'])
            return case_database.case_db.event_as_json(event_id)
        else:
            return {"status": "invalid event"}
    return __func()


def get_event(event_id):
    from server.context import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        valid_event_id = case_database.case_db.session.query(case_database.Event) \
            .filter(case_database.Event.id == event_id).all()
        if valid_event_id:
            return case_database.case_db.event_as_json(event_id)
        else:
            return {"status": "invalid event"}
    return __func()