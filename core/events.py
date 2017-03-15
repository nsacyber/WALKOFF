from blinker import Signal


class Event:
    def __init__(self, callback, name=''):
        self.signal = Signal()
        self.name = name
        self.callback = callback(name)  # needed b/c blinker cannot use weak references for callbacks
        self.signal.connect(self.callback)

    def send(self, sender, data=''):
        self.signal.send(sender, data=data)


class EventHandler(object):
    def __init__(self, event_type, shared_log=None, events=None):
        self.events = ({event_name: Event(callback, name=event_name) for event_name, callback in events.items()}
                       if events is not None else {})
        self.eventlog = [] if shared_log is None else shared_log
        self.event_type = event_type

    def add_events(self, events):
        """
        Adds events as dictionary
        where the key is a unique identifier and the value is the callback
        """
        for event_name, callback in events.items():
            self.events[event_name] = Event(callback, name=event_name)

    def execute_event(self, sender, event):
        self.execute_code(sender, event.code)

    def execute_event_code(self, sender, event_code):
        if event_code in self.events:
            self.events[event_code].send(sender)
            self.eventlog.append({self.event_type: event_code})
        else:
            self.eventlog.append({self.event_type: "Unknown!"})

    def __repr__(self):
        return str({'event_type': self.event_type,
                    'events': str(self.events.keys())})


class EventListener(EventHandler):
    def __init__(self, event_type, shared_log=None, events=None):
        EventHandler.__init__(self, event_type, shared_log, events)

    def callback(self, sender):
        def execution(event):
            self.execute_event_code(sender, event.code)
        return execution

