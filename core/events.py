from blinker import Signal


class Event:
    def __init__(self, callback, name=""):
        self.signal = Signal()
        self.name = name
        self.callback = callback  # needed b/c blinker cannot use weak references for callbacks
        self.signal.connect(callback)

    def send(self, sender):
        self.signal.send(sender)


class EventHandler(object):
    def __init__(self, event_type, shared_log=None):
        self.events = {}
        self.eventlog = [] if shared_log is None else shared_log
        self.event_type = event_type

    def execute_event(self, sender, event):
        self.execute_code(sender, event.code)

    def execute_event_code(self, sender, event_code):
        if event_code in self.events:
            self.events[event_code].send(sender)
            self.eventlog.append({self.event_type: event_code})
        else:
            self.eventlog.append({self.event_type: "Unknown!"})


class EventListener(EventHandler):
    def __init__(self, event_type, shared_log=None):
        EventHandler.__init__(self, event_type, shared_log)

    def callback(self, sender):
        def execution(event):
            self.execute_event_code(sender, event.code)
        return execution

