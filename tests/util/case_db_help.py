from walkoff.events import WalkoffEvent


def setup_subscriptions_for_action(workflow_ids, action_ids, action_events=None, workflow_events=None):
    action_events = action_events if action_events is not None else [WalkoffEvent.ActionExecutionSuccess.signal_name]
    workflow_events = workflow_events if workflow_events is not None else []
    subs = {str(workflow_id): workflow_events for workflow_id in workflow_ids} \
        if isinstance(workflow_ids, list) else {str(workflow_ids): workflow_events}
    for action_id in action_ids:
        subs[str(action_id)] = action_events
