from datetime import datetime

import walkoff.case.database as case_database
import walkoff.case.subscription as case_subscription
from walkoff.events import WalkoffEvent


def setup_subscriptions_for_action(workflow_ids, action_ids, action_events=None, workflow_events=None):
    action_events = action_events if action_events is not None else [WalkoffEvent.ActionExecutionSuccess.signal_name]
    workflow_events = workflow_events if workflow_events is not None else []
    subs = {workflow_id: workflow_events for workflow_id in workflow_ids} \
        if isinstance(workflow_ids, list) else {workflow_ids: workflow_events}
    for action_id in action_ids:
        subs[action_id] = action_events
    case_subscription.set_subscriptions({'case1': subs})


def executed_actions(workflow_id, start_time, end_time):
    events = [event.as_json()
              for event in case_database.case_db.session.query(case_database.Event). \
                  filter(case_database.Event.originator == workflow_id).all()]
    out = []
    for event in events:
        if start_time <= datetime.strptime(event['timestamp'], '%Y-%m-%d %H:%M:%S.%f') <= end_time:
            out.append(event)
    return out
