from gevent.event import Event
from threading import Condition


class GeventWorkflowInterrupter(object):

    def __init__(self):
        self._pause_resume_event = Event()

    def pause(self, timeout=10):
        self._pause_resume_event.wait(timeout=timeout)
        self._pause_resume_event.clear()

    def resume(self):
        self._pause_resume_event.set()


class SimpleWorkflowInterrupter(object):

    def __int__(self):
        self._pause_resume_event = Condition()

    def pause(self, timeout=10):
        self._pause_resume_event.wait(timeout=timeout)

    def resume(self):
        self._pause_resume_event.notifyAll()
