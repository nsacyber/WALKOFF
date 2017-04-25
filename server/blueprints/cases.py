import json
import os
from flask import Blueprint, request
from flask_security import auth_token_required, roles_accepted
from server.flaskserver import running_context
import core.case.database as case_database
import core.case.subscription as case_subscription
from server import forms
from core.case.subscription import CaseSubscriptions, add_cases, delete_cases, \
    rename_case
import core.config.config
import core.config.paths
from core.helpers import construct_workflow_name_key


cases_page = Blueprint('cases_page', __name__)


@cases_page.route('/', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def display_cases():
    return json.dumps(case_database.case_db.cases_as_json())


@cases_page.route('/import', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def import_cases():
    form = forms.ImportCaseForm(request.form)
    filename = form.filename.data if form.filename.data else core.config.paths.default_case_export_path
    if os.path.isfile(filename):
        try:
            with open(filename, 'r') as cases_file:
                cases_file = cases_file.read()
                cases_file = cases_file.replace('\n', '')
                cases = json.loads(cases_file)
            case_subscription.add_cases(cases)
            for case in cases.keys():
                running_context.db.session.add(running_context.CaseSubscription(name=case))
                running_context.CaseSubscription.update(case)
                running_context.db.session.commit()
            return json.dumps({"status": "success", "cases": case_subscription.subscriptions_as_json()})
        except (OSError, IOError):
            return json.dumps({"status": "error reading file"})
        except ValueError:
            return json.dumps({"status": "file contains invalid JSON"})
    else:
        return json.dumps({"status": "error: file does not exist"})


@cases_page.route('/export', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def export_cases():
    form = forms.ExportCaseForm(request.form)
    filename = form.filename.data if form.filename.data else core.config.paths.default_case_export_path
    try:
        with open(filename, 'w') as cases_file:
            cases_file.write(json.dumps(case_subscription.subscriptions_as_json()))
        return json.dumps({"status": "success"})
    except (OSError, IOError):
        return json.dumps({"status": "error writing to file"})


@cases_page.route('/<string:case_name>/<string:action>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def crud_case(case_name, action):
    if action == 'add':
        case = CaseSubscriptions()
        add_cases({"{0}".format(str(case_name)): case})
        case = running_context.CaseSubscription.query.filter_by(name=case_name).first()
        if not case:
            running_context.db.session.add(running_context.CaseSubscription(name=case_name))
            running_context.db.session.commit()
        return json.dumps(case_subscription.subscriptions_as_json())
    elif action == 'delete':
        delete_cases([case_name])
        case = running_context.CaseSubscription.query.filter_by(name=case_name).first()
        if case:
            running_context.db.session.delete(case)
            running_context.db.session.commit()
        return json.dumps(case_subscription.subscriptions_as_json())
    elif action == 'edit':
        form = forms.EditCaseForm(request.form)
        if form.validate():
            if form.name.data:
                rename_case(case_name, form.name.data)
                case = running_context.CaseSubscription.query.filter_by(name=case_name).first()
                if case:
                    case.name = form.name.data
                    running_context.db.session.commit()
                if form.note.data:
                    case_database.case_db.edit_case_note(form.name.data, form.note.data)
            elif form.note.data:
                case_database.case_db.edit_case_note(case_name, form.note.data)
            return json.dumps(case_database.case_db.cases_as_json())
    else:
        return json.dumps({"status": "Invalid operation {0}".format(action)})


@cases_page.route('/<string:case_name>', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def display_case(case_name):
    case = case_database.case_db.session.query(case_database.Case) \
        .filter(case_database.Case.name == case_name).first()
    if case:
        return json.dumps({'case': case.as_json()})
    else:
        return json.dumps({'status': 'Case with given name does not exist'})


@cases_page.route('/event/<int:event_id>/edit', methods=['POST'])
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


@cases_page.route('/availablesubscriptions', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def display_possible_subscriptions():
    return json.dumps(core.config.config.possible_events)


@cases_page.route('/subscriptions/<string:case_name>/global/edit', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def edit_global_subscription(case_name):
    form = forms.EditGlobalSubscriptionForm(request.form)
    if form.validate():
        global_sub = case_subscription.GlobalSubscriptions(controller=form.controller.data,
                                                           workflow=form.workflow.data,
                                                           step=form.step.data,
                                                           next_step=form.next_step.data,
                                                           flag=form.flag.data,
                                                           filter=form.filter.data)
        success = case_subscription.edit_global_subscription(case_name, global_sub)
        running_context.CaseSubscription.update(case_name)
        running_context.db.session.commit()
        if success:
            return json.dumps(case_subscription.subscriptions_as_json())
        else:
            return json.dumps({"status": "Error: Case name {0} was not found".format(case_name)})
    else:
        return json.dumps({"status": "Error: form invalid"})


def convert_ancestry(ancestry):
    if len(ancestry) >= 3:
        ancestry[1] = construct_workflow_name_key(ancestry[1], ancestry[2])
        del ancestry[2]
    return ancestry


@cases_page.route('/subscriptions/<string:case_name>/subscription/<string:action>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def crud_subscription(case_name, action):
    if action == 'edit':
        if request.form:
            f = forms.EditSubscriptionForm(request.form)
            data = {"ancestry": f.ancestry.data, "events": f.events.data}
        else:
            data = request.get_json()

        if data:
            if 'ancestry' in data and 'events' in data:
                success = case_subscription.edit_subscription(case_name,
                                                              convert_ancestry(data['ancestry']),
                                                              data['events'])
                running_context.CaseSubscription.update(case_name)
                running_context.db.session.commit()
                if success:
                    return json.dumps(case_subscription.subscriptions_as_json())
                else:
                    return json.dumps({"status": "Error occurred while editing subscription"})
            else:
                return json.dumps({"status": "Error: malformed JSON"})
        else:
            return json.dumps({"status": "Error: no JSON in request"})
    elif action == 'add':
        if request.get_json():
            data = request.get_json()
            if 'ancestry' in data:
                events = data['events'] if 'events' in data else []
                case_subscription.add_subscription(case_name, convert_ancestry(data['ancestry']), events)
                running_context.CaseSubscription.update(case_name)
                running_context.db.session.commit()
                return json.dumps(case_subscription.subscriptions_as_json())
            else:
                return json.dumps({"status": "Error: malformed JSON"})
        else:
            return json.dumps({"status": "Error: no JSON in request"})
    elif action == 'delete':
        if request.get_json():
            data = request.get_json()
            if 'ancestry' in data:
                case_subscription.remove_subscription_node(case_name, convert_ancestry(data['ancestry']))
                running_context.CaseSubscription.update(case_name)
                running_context.db.session.commit()
                return json.dumps(case_subscription.subscriptions_as_json())
            else:
                return json.dumps({"status": "Error: malformed JSON"})
        else:
            return json.dumps({"status": "Error: no JSON in request"})
    else:
        return json.dumps({"status": "error: unknown subscription action"})


@cases_page.route('/subscriptions/', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def display_subscriptions():
    return json.dumps(case_subscription.subscriptions_as_json())
