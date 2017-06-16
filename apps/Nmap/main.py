from apps import App, action
from libnmap.process import NmapProcess
from libnmap.parser import NmapParser


class Main(App):
    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)
        self.whitelist = []
        self.blacklist = []

    @action
    def add_host_to_whitelist(self, host):
        self.whitelist.append(host)

    @action
    def add_host_to_blacklist(self, host):
        self.blacklist.append(host)

    @action
    def clear_whitelist(self):
        self.whitelist = []

    @action
    def clear_blacklist(self):
        self.blacklist = []

    @action
    def run_scan(self, target, options):
        nmap_proc = NmapProcess(targets=target, options=options)
        nmap_proc.run()

        return nmap_proc.stdout

    @action
    def run_scan_check_whitelist(self, target, options):
        nmap_proc = NmapProcess(targets=target, options=options)
        nmap_proc.run()

        nmap_report_obj = NmapParser.parse(nmap_proc.stdout)

        for host in nmap_report_obj.hosts:
            if host.status == "up" and host.address not in self.whitelist:
                return False

        return True

    @action
    def run_scan_check_blacklist(self, target, options):
        nmap_proc = NmapProcess(targets=target, options=options)
        nmap_proc.run()

        nmap_report_obj = NmapParser.parse(nmap_proc.stdout)

        for host in nmap_report_obj.hosts:
            if host.status == "up" and host.address in self.blacklist:
                return False

        return True

    def shutdown(self):
        print("Nmap Shutting Down")
        return
