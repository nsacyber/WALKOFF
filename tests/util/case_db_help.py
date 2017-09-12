from datetime import datetime
import core.case.subscription as case_subscription
import core.case.database as case_database


def setup_subscriptions_for_step(workflow_uids, step_uids, step_events=None, workflow_events=None):
    step_events = step_events if step_events is not None else ['Function Execution Success']
    workflow_events = workflow_events if workflow_events is not None else []
    subs = {workflow_uid: workflow_events for workflow_uid in workflow_uids} \
        if isinstance(workflow_uids, list) else {workflow_uids: workflow_events}
    for step_uid in step_uids:
        subs[step_uid] = step_events
    case_subscription.set_subscriptions({'case1': subs})


def executed_steps(workflow_uid, start_time, end_time):
    events = [event.as_json()
              for event in case_database.case_db.session.query(case_database.Event). \
                  filter(case_database.Event.originator == workflow_uid).all()]
    out = []
    for event in events:
        if start_time <= datetime.strptime(event['timestamp'], '%Y-%m-%d %H:%M:%S.%f') <= end_time:
            out.append(event)
    return out
