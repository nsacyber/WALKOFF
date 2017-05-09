import json
import os
from flask import Blueprint, request, Response, current_app
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
from gevent.event import Event, AsyncResult
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED

cases_page = Blueprint('cases_page', __name__)


@cases_page.route('/export', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def export_cases():
    form = forms.ExportCaseForm(request.form)
    filename = form.filename.data if form.filename.data else core.config.paths.default_case_export_path
    try:
        with open(filename, 'w') as cases_file:
            cases_file.write(json.dumps(case_subscription.subscriptions_as_json()))
        current_app.logger.debug('Cases successfully exported to {0}'.format(filename))
        return json.dumps({"status": "success"})
    except (OSError, IOError) as e:
        current_app.logger.error('Error exporting cases to {0}'.format(filename))
        return json.dumps({"status": "error writing to file"})


@cases_page.route('/<string:case_name>', methods=['DELETE'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def delete_case(case_name):
    delete_cases([case_name])
    case = running_context.CaseSubscription.query.filter_by(name=case_name).first()
    if case:
        running_context.db.session.delete(case)
        running_context.db.session.commit()
        current_app.logger.debug('Case deleted {0}'.format(case_name))
    return json.dumps(case_subscription.subscriptions_as_json())


@cases_page.route('/<string:case_name>/events', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def get_events(case_name):
    result = case_database.case_db.case_events_as_json(case_name)
    return json.dumps(result)


def convert_ancestry(ancestry):
    if len(ancestry) >= 3:
        ancestry[1] = construct_workflow_name_key(ancestry[1], ancestry[2])
        del ancestry[2]
    return ancestry

__scheduler_event_conversion = {'Scheduler Start': EVENT_SCHEDULER_START,
                                'Scheduler Shutdown': EVENT_SCHEDULER_SHUTDOWN,
                                'Scheduler Paused': EVENT_SCHEDULER_PAUSED,
                                'Scheduler Resumed': EVENT_SCHEDULER_RESUMED,
                                'Job Added': EVENT_JOB_ADDED,
                                'Job Removed': EVENT_JOB_REMOVED,
                                'Job Executed': EVENT_JOB_EXECUTED,
                                'Job Error': EVENT_JOB_ERROR}


def convert_scheduler_events(events):
    return [__scheduler_event_conversion[event] for event in events if event in __scheduler_event_conversion]


def convert_to_event_names(events):
    result = []
    for event in events:
        for key in __scheduler_event_conversion:
            if __scheduler_event_conversion[key] == event:
                result.append(key)
    return result


@cases_page.route('/<string:case_name>/subscriptions', methods=['PUT'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def add_subscription(case_name):
    if request.get_json():
        data = request.get_json()
        if 'ancestry' in data:
            events = data['events'] if 'events' in data else []
            if len(data['ancestry']) == 1 and events:
                events = convert_scheduler_events(events)
            converted_ancestry = convert_ancestry(data['ancestry'])
            case_subscription.add_subscription(case_name, converted_ancestry, events)
            running_context.CaseSubscription.update(case_name)
            running_context.db.session.commit()
            current_app.logger.debug('Subscription added for {0} to {1}'.format(converted_ancestry, events))
            return json.dumps(case_subscription.subscriptions_as_json())
        else:
            current_app.logger.error('malformed json received in add_subscription: {0}'.format(data))
            return json.dumps({"status": "Error: malformed JSON"})
    else:
        current_app.logger.error('No JSON received in add_subscription')
        return json.dumps({"status": "Error: no JSON in request"})


@cases_page.route('/<string:case_name>/subscriptions', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def read_subscription(case_name):
    if case_name in core.case.subscription.subscriptions:
        result = core.case.subscription.subscriptions[case_name].as_json(names=True)
        return json.dumps(result)


@cases_page.route('/<string:case_name>/subscriptions', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def update_subscription(case_name):
    if request.form:
        f = forms.EditSubscriptionForm(request.form)
        data = {"ancestry": f.ancestry.data, "events": f.events.data}
    else:
        data = request.get_json()

    if data:
        if 'ancestry' in data and 'events' in data:
            data['ancestry'] = convert_ancestry(data['ancestry'])
            if len(data['ancestry']) == 1 and data['events']:
                data['events'] = convert_scheduler_events(data['events'])
            success = case_subscription.edit_subscription(case_name,
                                                          data['ancestry'],
                                                          data['events'])
            running_context.CaseSubscription.update(case_name)
            running_context.db.session.commit()
            if success:
                current_app.logger.info('Edited subscription {0} to {1}'.format(data['ancestry'], data['events']))
                return json.dumps(case_subscription.subscriptions_as_json())
            else:
                current_app.logger.error('Error occurred while editing subscription {0} to {1}'.format(data['ancestry'],
                                                                                                       data['events']))
                return json.dumps({"status": "Error occurred while editing subscription"})
        else:
            current_app.logger.error('malformed json received in edit_subscription: {0}'.format(data))
            return json.dumps({"status": "Error: malformed JSON"})
    else:
        current_app.logger.error('No JSON received in edit_subscription')
        return json.dumps({"status": "Error: no JSON in request"})


@cases_page.route('/<string:case_name>/subscriptions', methods=['DELETE'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def delete_subscription(case_name):
    if request.get_json():
        data = request.get_json()
        if 'ancestry' in data:
            converted_ancestry = convert_ancestry(data['ancestry'])
            case_subscription.remove_subscription_node(case_name, converted_ancestry)
            running_context.CaseSubscription.update(case_name)
            running_context.db.session.commit()
            current_app.logger.debug('Deleted subscription {0}'.format(converted_ancestry))
            return json.dumps(case_subscription.subscriptions_as_json())
        else:
            current_app.logger.error('malformed json received in delete_subscription: {0}'.format(data))
            return json.dumps({"status": "Error: malformed JSON"})
    else:
        current_app.logger.error('No JSON received in delete_subscription')
        return json.dumps({"status": "Error: no JSON in request"})


@cases_page.route('/subscriptions/', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def display_subscriptions():
    return json.dumps(case_subscription.subscriptions_as_json())


__case_event_json = AsyncResult()
__sync_signal = Event()


def __case_event_stream():
    while True:
        data = __case_event_json.get()
        yield 'data: %s\n\n' % data
        __sync_signal.wait()


def __push_to_case_stream(sender, **kwargs):
    out = {'name': sender.name,
           'ancestry': sender.ancestry}
    if 'data' in kwargs:
        out['data'] = kwargs['data']
    __case_event_json.set(json.dumps(out))
    __sync_signal.set()
    __sync_signal.clear()


def setup_case_stream():
    from blinker import NamedSignal
    import core.case.callbacks as callbacks
    signals = [getattr(callbacks, field) for field in dir(callbacks) if (not field.startswith('__')
                                                                             and isinstance(getattr(callbacks, field),
                                                                                           NamedSignal))]
    for signal in signals:
        signal.connect(__push_to_case_stream)


@cases_page.route('/events', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def stream_workflow():
    return Response(__case_event_stream(), mimetype='text/event-stream')