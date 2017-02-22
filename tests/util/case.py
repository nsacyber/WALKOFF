from core.case.subscription import *


def construct_case1():
    '''
    Assumes case where the possible events are as follows:
    controller: a,b,c
    workflow: d,e,f
    step: 1,2,3
    next_step: 4,5,6
    flag: u,v,w
    filter: x,y,z
    Constructs a specific case of roughly 3 events per execution level subscribed to combinations of events
    :return:
    '''

    global_subs = GlobalSubscriptions(controller='a', next_step=[4, 5], flag='*', filter='x')

    filter_subs1 = Subscription(events=['y', 'z'], disabled='x')
    filter_subs2 = Subscription(disabled='*')
    filter_subs3 = Subscription(events='y')
    filter1_acceptance = {'events': ['y', 'z'], 'rejected': ['x'],
                          'subs': {}}  # simplified structure to use for testing
    filter2_acceptance = {'events': [], 'rejected': ['x', 'y', 'z'], 'subs': {}}
    filter3_acceptance = {'events': ['x', 'y'], 'rejected': ['z'], 'subs': {}}

    flag_subs1 = Subscription(events='*', disabled='v', subscriptions={'filter1': filter_subs1})
    flag_subs2 = Subscription(disabled=['u', 'w'], subscriptions={'filter2': filter_subs2,
                                                                  'filter3': filter_subs3})
    flag_subs3 = Subscription(events='w', disabled='v')
    flag_subs4 = Subscription()
    flag1_acceptance = {'events': ['u', 'w'], 'rejected': ['v'], 'subs': {'filter1': filter1_acceptance}}
    flag2_acceptance = {'events': ['v'], 'rejected': ['u', 'w'], 'subs': {'filter2': filter2_acceptance,
                                                                          'filter3': filter3_acceptance}}
    flag3_acceptance = {'events': ['u', 'w'], 'rejected': ['v'], 'subs': {}}
    flag4_acceptance = {'events': ['u', 'v', 'w'], 'rejected': [], 'subs': {}}

    next_subs1 = Subscription(subscriptions={'flag1': flag_subs1})
    next_subs2 = Subscription(disabled=5, subscriptions={'flag2': flag_subs2, 'flag3': flag_subs3})
    next_subs3 = Subscription(events=6, disabled=4, subscriptions={'flag4': flag_subs4})
    next1_acceptance = {'events': [4, 5], 'rejected': [6], 'subs': {'flag1': flag1_acceptance}}
    next2_acceptance = {'events': [4], 'rejected': [5, 6], 'subs': {'flag2': flag2_acceptance,
                                                                    'flag3': flag3_acceptance}}
    next3_acceptance = {'events': [5, 6], 'rejected': [4], 'subs': {'flag4': flag4_acceptance}}

    step_subs1 = Subscription(events=[1, 2], subscriptions={'next1': next_subs1})
    step_subs2 = Subscription(subscriptions={'next2': next_subs2, 'next3': next_subs3})
    step_subs3 = Subscription(events=3, disabled=1)
    step1_acceptance = {'events': [1, 2], 'rejected': [3], 'subs': {'next1': next1_acceptance}}
    step2_acceptance = {'events': [], 'rejected': [1, 2, 3], 'subs': {'next2': next2_acceptance,
                                                                      'next3': next3_acceptance}}
    step3_acceptance = {'events': [3], 'rejected': [1, 2], 'subs': {}}

    workflow_subs1 = Subscription(events='d')
    workflow_subs2 = Subscription(events='*', subscriptions={'step1': step_subs1, 'step2': step_subs2})
    workflow_subs3 = Subscription(events='*', disabled='e', subscriptions={'step3': step_subs3})
    workflow1_acceptance = {'events': ['d'], 'rejected': ['e', 'f'], 'subs': {}}
    workflow2_acceptance = {'events': ['d', 'e', 'f'], 'rejected': [], 'subs': {'step1': step1_acceptance,
                                                                                'step2': step2_acceptance}}
    workflow3_acceptance = {'events': ['d', 'f'], 'rejected': ['e'], 'subs': {'step3': step3_acceptance}}

    controller_subs1 = Subscription(events='*', subscriptions={'workflow1': workflow_subs1,
                                                               'workflow2': workflow_subs2})
    controller_subs2 = Subscription(events=['b', 'c'], disabled='a')
    controller_subs3 = Subscription(subscriptions={'workflow3': workflow_subs3})
    controller1_acceptance = {'events': ['a', 'b', 'c'], 'rejected': [], 'subs': {'workflow1': workflow1_acceptance,
                                                                                  'workflow2': workflow2_acceptance}}
    controller2_acceptance = {'events': ['b', 'c'], 'rejected': ['a'], 'subs': {}}
    controller3_acceptance = {'events': ['a'], 'rejected': ['b', 'c'], 'subs': {'workflow3': workflow3_acceptance}}

    case_sub = CaseSubscriptions(subscriptions={'controller1': controller_subs1,
                                                'controller2': controller_subs2,
                                                'controller3': controller_subs3},
                                 global_subscriptions=global_subs)

    event_acceptance = {'controller1': controller1_acceptance,
                        'controller2': controller2_acceptance,
                        'controller3': controller3_acceptance}

    return case_sub, event_acceptance


def construct_case2():
    '''
    Assumes case where the possible events are as follows:
    controller: a,b,c
    workflow: d,e,f
    step: 1,2,3
    next_step: 4,5,6
    flag: u,v,w
    filter: x,y,z
    Constructs a specific case which is simpler than case 1
    :return:
    '''

    global_subs = GlobalSubscriptions(controller='a', next_step=[4, 5], flag='*', filter='x')

    filter_subs1 = Subscription(events='z', disabled='x')
    filter_subs2 = Subscription(disabled='*')
    filter1_acceptance = {'events': ['z'], 'rejected': ['x', 'y'],
                          'subs': {}}  # simplified structure to use for testing
    filter2_acceptance = {'events': [], 'rejected': ['x', 'y', 'z'], 'subs': {}}

    flag_subs1 = Subscription(events='*', disabled='v', subscriptions={'filter1': filter_subs1,
                                                                       'filter2': filter_subs2, })
    flag_subs2 = Subscription(disabled=['w'])
    flag1_acceptance = {'events': ['u', 'w'], 'rejected': ['v'], 'subs': {'filter1': filter1_acceptance,
                                                                          'filter2': filter2_acceptance}}
    flag2_acceptance = {'events': ['u', 'v'], 'rejected': ['w'], 'subs': {}}

    next_subs1 = Subscription(disabled=5)
    next_subs2 = Subscription(subscriptions={'flag1': flag_subs1})
    next_subs3 = Subscription(events=6, disabled=4, subscriptions={'flag2': flag_subs2})
    next1_acceptance = {'events': [4], 'rejected': [5, 6], 'subs': {}}
    next2_acceptance = {'events': [4, 5], 'rejected': [6], 'subs': {'flag1': flag1_acceptance}}
    next3_acceptance = {'events': [5, 6], 'rejected': [4], 'subs': {'flag2': flag2_acceptance}}

    step_subs1 = Subscription(events=[2], subscriptions={'next1': next_subs1})
    step_subs2 = Subscription(subscriptions={'next2': next_subs2, 'next3': next_subs3})
    step1_acceptance = {'events': [2], 'rejected': [1, 3], 'subs': {'next1': next1_acceptance}}
    step2_acceptance = {'events': [], 'rejected': [1, 2, 3], 'subs': {'next2': next2_acceptance,
                                                                      'next3': next3_acceptance}}

    workflow_subs1 = Subscription(events='*', subscriptions={'step1': step_subs1, 'step2': step_subs2})
    workflow1_acceptance = {'events': ['d', 'e', 'f'], 'rejected': [], 'subs': {'step1': step1_acceptance,
                                                                                'step2': step2_acceptance}}

    controller_subs1 = Subscription(events='*', subscriptions={'workflow1': workflow_subs1})
    controller1_acceptance = {'events': ['a', 'b', 'c'], 'rejected': [],
                              'subs': {'workflow1': workflow1_acceptance}}

    case_sub = CaseSubscriptions(subscriptions={'controller1': controller_subs1},
                                 global_subscriptions=global_subs)

    event_acceptance = {'controller1': controller1_acceptance}

    return case_sub, event_acceptance


def __visit_node(node, paths, current):
    '''
    Depth first search through subscription tree
    :param node: Current Node
    :param paths: accumulator for all valid ancestries along with accepted and rejected events for each level
    :param current: current ancestry
    :return:
    '''
    paths.append({'ancestry': current, 'events': node['events'], 'rejected': node['rejected']})
    for name, subnode in node['subs'].items():
        current_cpy = list(current)
        current_cpy.append(name)
        __visit_node(subnode, paths, current_cpy)


def all_valid_events(case_acceptance):
    paths = []
    for name, node in case_acceptance.items():
        __visit_node(node, paths, [name])
    return paths
