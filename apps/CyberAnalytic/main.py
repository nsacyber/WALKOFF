from server.appdevice import App
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
                print(proc.name())
                if 'at.exe' in proc.exe():
                    suspicious_pids.append(threat_pid("at.exe", proc.name(), proc.pid))
                elif 'schtasks.exe' in proc.exe():
                    suspicious_pids.append(threat_pid("schtask.exe", proc.name(), proc.pid))
                elif 'cmd.exe' in proc.exe():
                    print("found one")
                    #if proc.parent() and "explorer.exe" not in proc.parent().exe():
                    #    suspicious_pids.append(threat_pid("cmd.exe", proc.name(), proc.pid))
                    suspicious_pids.append(threat_pid("cmd.exe", proc.name(), proc.pid))

    def begin_monitoring(self, args={}):
        if not self.is_running:
            print("spawning")
            gevent.spawn(self.__monitor_processes)

    def get_exe_pids(self, args={}):
        return json.dumps(suspicious_pids)

    def get_exe_pids_by_name(self, args={}):
        if args["name"]:
            return [ x for x in suspicious_pids if x.name == args["name"] ]
        else:
            return []
