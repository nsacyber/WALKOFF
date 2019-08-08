from libnmap.process import NmapProcess
from libnmap.parser import NmapParser
import os
import concurrent.futures

import asyncio

from walkoff_app_sdk.app_base import AppBase

import json


class Nmap(AppBase):
    __version__ = "1.0.0"
    app_name = "nmap"

    def __init__(self, redis, logger, console_logger=None):
        super().__init__(redis, logger, console_logger)

    async def run_scan(self, targets, options):
        results = []
        for target in targets:
            nmap_proc = NmapProcess(target, options)

            executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(executor, nmap_proc.run)

            try:
                results.append(nmap_proc.stdout)
            except Exception as e:
                results.append(e)

        return results


    async def get_hosts_from_scan(self, targets, options):
        results = {}

        for target in targets:
            nmap_proc = NmapProcess(targets=target, options=options)
            
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(executor, nmap_proc.run)

            nmap_report_obj = NmapParser.parse(nmap_proc.stdout)

            hosts = {}

            for host in nmap_report_obj.hosts:
                hosts[host.address] = host.status

            results[target] = hosts

        return results

    async def parse_xml_for_linux(self, nmap_arr):
        output = []
        for nmap in nmap_arr:
            try:
                nmap_obj = NmapParser.parse(nmap_data=nmap, data_type='XML')
                for host in nmap_obj.hosts:
                    if host.is_up():
                        try:
                            if host.os_match_probabilities()[0].osclasses[0].osfamily == "Linux":
                                output.append(str(host.address))
                        except Exception as e:
                            self.logger.info(f"Host {host.address} is not a Linux machine")

            except Exception as e:
                return e

        return output

    async def parse_xml_for_windows(self, nmap_arr):
        output = []
        for nmap in nmap_arr:
            try:
                nmap_obj = NmapParser.parse(nmap_data=nmap, data_type='XML')
                for host in nmap_obj.hosts:
                    if host.is_up():
                        try:
                            if host.os_match_probabilities()[0].osclasses[0].osfamily == "Windows":
                                output.append(str(host.address))
                        except Exception as e:
                            self.logger.info(f"Host {host.address} is not a Windows machine")
            except Exception as e:
                return e

        return output

    async def parse_xml_for_linux_from_file(self, nmap_file):
        output = []
        try:
            # moving into files directory to read xml
            curr_dir = os.getcwd()
            temp_dir = os.path.join(curr_dir, r'files')
            os.chdir(temp_dir)
            with open(nmap_file, 'r') as f:
                xml_str = f.read().replace("\n", "")
        except IOError as e:
            return e, 'FileReadError'
        try:
            nmap_obj = NmapParser.parse(nmap_data=xml_str, data_type='XML')
        except Exception as e:
            return e, 'XMLError'

        for host in nmap_obj.hosts:
            if host.is_up():
                try:
                    if host.os_match_probabilities()[0].osclasses[0].osfamily == "Linux":
                        output.append(str(host.address))
                except Exception as e:
                    self.logger.info(f"Host {host.address} is not a Linux machine")
        return output

    async def parse_xml_for_windows_from_file(self, nmap_file):
        output = []
        try:
            # moving into files directory to read xml
            curr_dir = os.getcwd()
            temp_dir = os.path.join(curr_dir, r'files')
            os.chdir(temp_dir)
            with open(nmap_file, 'r') as f:
                xml_str = f.read().replace("\n", "")
        except IOError as e:
            return e, 'FileReadError'

        try:
            nmap_obj = NmapParser.parse(nmap_data=xml_str, data_type='XML')
        except Exception as e:
            return e, 'XMLError'

        for host in nmap_obj.hosts:
            if host.is_up():
                try:
                    if host.os_match_probabilities()[0].osclasses[0].osfamily == "Windows":
                        output.append(str(host.address))
                except Exception as e:
                    self.logger.info(f"Host {host.address} is not a Windows machine")
        return output

    async def xml_to_json(self, nmap_out, is_file=False):
        xml_str = None
        if is_file:
            try:
                # moving into files directory to read xml
                curr_dir = os.getcwd()
                temp_dir = os.path.join(curr_dir, r'files')
                os.chdir(temp_dir)
                with open(nmap_out, 'r') as f:
                    xml_str = f.read().replace("\n", "")
            except IOError as e:
                return e, 'FileReadError'
        else:
            for nmap in nmap_out:
                xml_str = nmap

                try:
                    nmap_obj = NmapParser.parse(nmap_data=xml_str, data_type='XML')
                except Exception as e:
                    return e, 'XMLError'

                ret = []
                for host in nmap_obj.hosts:
                    if host.is_up():
                        ret.append({"name": host.hostnames.pop() if len(host.hostnames) else host.address,
                         "address": host.address,
                         "services": [{"port": service.port,
                                       "protocol": service.protocol,
                                       "state": service.state,
                                       "service": service.service,
                                       "banner": service.banner} for service in host.services]})

                ret = json.dumps(ret)
                ret = json.loads(ret)

        return ret


    async def ports_and_hosts_from_json(self, nmap_json, is_file=False):
        try:
            if is_file:
                # moving into files directory to read json
                curr_dir = os.getcwd()
                temp_dir = os.path.join(curr_dir, r'files')
                os.chdir(temp_dir)
                with open(nmap_json) as j:
                    obj = j
            else:
                obj = nmap_json
        except IOError as e:
            return e, 'FileReadError'
        except (AttributeError, ValueError) as e:
            return e, 'JSONError'

        r = {"ports": [], "hosts": []}
        for host in obj:
            r["hosts"].append(host["address"])
            for svc in host["services"]:
                if svc["protocol"] == "tcp":
                    r["ports"].append("T:" + str(svc["port"]))
                elif svc["protocol"] == "udp":
                    r["ports"].append("U:" + str(svc["port"]))

        r["ports"] = ",".join(r["ports"])
        r["hosts"] = ",".join(r["hosts"])

        return r


if __name__ == "__main__":
    asyncio.run(Nmap.run())
