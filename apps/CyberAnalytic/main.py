from apps import App, action
import psutil
import gevent
import json
from collections import namedtuple

threat_pid = namedtuple("thread_pid", ["threat_name", "threat_exe", "pid"])
suspicious_pids = []


class Main(App):

    global suspicious_pids

    def __init__(self, name=None, device=None):
        self.is_running = False
        App.__init__(self, name, device)

    def __monitor_processes(self):
        while True:
            for proc in psutil.process_iter():
                if 'at.exe' in proc.exe():
                    suspicious_pids.append(threat_pid("at.exe", proc.name(), proc.pid))
                elif 'schtasks.exe' in proc.exe():
                    suspicious_pids.append(threat_pid("schtask.exe", proc.name(), proc.pid))
                elif 'cmd.exe' in proc.exe():
                    if proc.parent() and "explorer.exe" not in proc.parent().exe():
                        suspicious_pids.append(threat_pid("cmd.exe", proc.name(), proc.pid))

    @action
    def begin_monitoring(self):
        if not self.is_running:
            gevent.spawn(self.__monitor_processes)
        return "Success"

    @action
    def get_exe_pids(self):
        return json.dumps(suspicious_pids)

    @action
    def get_exe_pids_by_name(self, name):
        return [x for x in suspicious_pids if x.name == name]
