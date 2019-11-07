import datetime
import asyncio
import logging
import json

from pypsrp.client import Process, SignalCode, WinRS, PowerShell as PS, RunspacePool
from pypsrp.wsman import WSMan

from walkoff_app_sdk.app_base import AppBase

logging.getLogger("urllib3").setLevel(logging.ERROR)


class ObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            json.dumps(obj)
            return super(ObjectEncoder, self).default(obj)
        except:
            try:
                return str(obj)
            except:
                return "Value from returned PowerShell object is not JSON Serializable."


class AdversaryHunting(AppBase):
    __version__ = "1.0.0"
    app_name = "adversary_hunting"

    def __init__(self, redis, logger):
        super().__init__(redis, logger)

    async def set_timestamp(self):
        timestamp = '{:%Y-%m-%d_%H-%M-%S}'.format(datetime.datetime.now())
        return timestamp

    async def run_script(self, wsman, script):
        with RunspacePool(wsman) as pool:
            with open(script, "r") as f:
                script = f.read()
            ps = PS(pool)
            ps.add_script(script)
            ps.invoke()
            this_result = []
            for line in ps.output:
                if type(line) is str:
                    this_result.append(line)
                else:
                    this_result.append({
                        "types": line.types,
                        "adapted_properties": json.loads(json.dumps(line.adapted_properties, cls=ObjectEncoder)),
                        "extended_properties": json.loads(json.dumps(line.extended_properties, cls=ObjectEncoder))
                    })
            self.logger.info(this_result)

            if ps.had_errors:
                return {"stdout": "", "stderr": this_result}
            else:
                return {"stdout": this_result, "stderr": ""}

    async def get_dll_info(self, hosts, username, password, transport,
                           server_cert_validation,
                           message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param shell_type: The type of shell you wish to run (i.e. "powershell")
        :param local_file_name: file name to run specified script from
        :param username: username of the machine you wish to run command on
        :param password: password for the machine you wish to run command on
        :param transport: method of transportation
        :param server_cert_validation: whether or not to verify certificates
        :param message_encryption: When you should encrypt messages

        :return: dict of results with hosts as keys and list of outputs for each specified hosts
        """
        results = {}

        for host in hosts:
            self.logger.info(f"Executing on {host}")
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                results[host] = await self.run_script(wsman, "scripts/Get-DLLInfo.ps1")

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def get_installed_apps(self, hosts, username, password, transport, server_cert_validation,
                                 message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param shell_type: The type of shell you wish to run (i.e. "powershell")
        :param local_file_name: file name to run specified script from
        :param username: username of the machine you wish to run command on
        :param password: password for the machine you wish to run command on
        :param transport: method of transportation
        :param server_cert_validation: whether or not to verify certificates
        :param message_encryption: When you should encrypt messages

        :return: dict of results with hosts as keys and list of outputs for each specified hosts
        """
        results = {}

        for host in hosts:
            self.logger.info(f"Executing on {host}")
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                results[host] = await self.run_script(wsman, "scripts/Get-InstalledApps.ps1")

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def get_netstat(self, hosts, username, password, transport, server_cert_validation,
                          message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param shell_type: The type of shell you wish to run (i.e. "powershell")
        :param local_file_name: file name to run specified script from
        :param username: username of the machine you wish to run command on
        :param password: password for the machine you wish to run command on
        :param transport: method of transportation
        :param server_cert_validation: whether or not to verify certificates
        :param message_encryption: When you should encrypt messages

        :return: dict of results with hosts as keys and list of outputs for each specified hosts
        """
        results = {}

        for host in hosts:
            self.logger.info(f"Executing on {host}")
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                results[host] = await self.run_script(wsman, "scripts/Get-NetStat.ps1")

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def get_network_adapter(self, hosts, username, password, transport, server_cert_validation,
                                  message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param shell_type: The type of shell you wish to run (i.e. "powershell")
        :param local_file_name: file name to run specified script from
        :param username: username of the machine you wish to run command on
        :param password: password for the machine you wish to run command on
        :param transport: method of transportation
        :param server_cert_validation: whether or not to verify certificates
        :param message_encryption: When you should encrypt messages

        :return: dict of results with hosts as keys and list of outputs for each specified hosts
        """
        results = {}

        for host in hosts:
            self.logger.info(f"Executing on {host}")
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                results[host] = await self.run_script(wsman, "scripts/Get-NetworkAdapter.ps1")

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def get_processes(self, hosts, username, password, transport, server_cert_validation,
                            message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param shell_type: The type of shell you wish to run (i.e. "powershell")
        :param local_file_name: file name to run specified script from
        :param username: username of the machine you wish to run command on
        :param password: password for the machine you wish to run command on
        :param transport: method of transportation
        :param server_cert_validation: whether or not to verify certificates
        :param message_encryption: When you should encrypt messages

        :return: dict of results with hosts as keys and list of outputs for each specified hosts
        """
        results = {}

        for host in hosts:
            self.logger.info(f"Executing on {host}")
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                results[host] = await self.run_script(wsman, "scripts/Get-Processes.ps1")

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def get_scheduled_task(self, hosts, username, password, transport, server_cert_validation,
                                 message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param shell_type: The type of shell you wish to run (i.e. "powershell")
        :param local_file_name: file name to run specified script from
        :param username: username of the machine you wish to run command on
        :param password: password for the machine you wish to run command on
        :param transport: method of transportation
        :param server_cert_validation: whether or not to verify certificates
        :param message_encryption: When you should encrypt messages

        :return: dict of results with hosts as keys and list of outputs for each specified hosts
        """
        results = {}

        for host in hosts:
            self.logger.info(f"Executing on {host}")
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                results[host] = await self.run_script(wsman, "scripts/Get-ScheduledTask.ps1")

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def get_services(self, hosts, username, password, transport, server_cert_validation,
                           message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param shell_type: The type of shell you wish to run (i.e. "powershell")
        :param local_file_name: file name to run specified script from
        :param username: username of the machine you wish to run command on
        :param password: password for the machine you wish to run command on
        :param transport: method of transportation
        :param server_cert_validation: whether or not to verify certificates
        :param message_encryption: When you should encrypt messages

        :return: dict of results with hosts as keys and list of outputs for each specified hosts
        """
        results = {}

        for host in hosts:
            self.logger.info(f"Executing on {host}")
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                results[host] = await self.run_script(wsman, "scripts/Get-Services.ps1")

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def get_memory_kansa(self, hosts, username, password, transport, server_cert_validation,
                               message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param shell_type: The type of shell you wish to rsun (i.e. "powershell")
        :param local_file_name: file name to run specified script from
        :param username: username of the machine you wish to run command on
        :param password: password for the machine you wish to run command on
        :param transport: method of transportation
        :param server_cert_validation: whether or not to verify certificates
        :param message_encryption: When you should encrypt messages

        :return: dict of results with hosts as keys and list of outputs for each specified hosts
        """
        results = {}

        for host in hosts:
            self.logger.info(f"Executing on {host}")
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                results[host] = await self.run_script(wsman, "scripts/Kansa/Modules/Memory/Get-Memory.ps1")

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def get_dns_cache_kansa(self, hosts, username, password, transport, server_cert_validation,
                                  message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param shell_type: The type of shell you wish to rsun (i.e. "powershell")
        :param local_file_name: file name to run specified script from
        :param username: username of the machine you wish to run command on
        :param password: password for the machine you wish to run command on
        :param transport: method of transportation
        :param server_cert_validation: whether or not to verify certificates
        :param message_encryption: When you should encrypt messages

        :return: dict of results with hosts as keys and list of outputs for each specified hosts
        """
        results = {}

        for host in hosts:
            self.logger.info(f"Executing on {host}")
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                results[host] = await self.run_script(wsman, "scripts/Kansa/Modules/Net/Get-DNSCache.ps1")

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def get_netstat_kansa(self, hosts, username, password, transport, server_cert_validation,
                                message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param shell_type: The type of shell you wish to rsun (i.e. "powershell")
        :param local_file_name: file name to run specified script from
        :param username: username of the machine you wish to run command on
        :param password: password for the machine you wish to run command on
        :param transport: method of transportation
        :param server_cert_validation: whether or not to verify certificates
        :param message_encryption: When you should encrypt messages

        :return: dict of results with hosts as keys and list of outputs for each specified hosts
        """
        results = {}

        for host in hosts:
            self.logger.info(f"Executing on {host}")
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                results[host] = await self.run_script(wsman, "scripts/Kansa/Modules/Net/Get-Netstat.ps1")

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def get_arp_kansa(self, hosts, username, password, transport, server_cert_validation,
                            message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param shell_type: The type of shell you wish to rsun (i.e. "powershell")
        :param local_file_name: file name to run specified script from
        :param username: username of the machine you wish to run command on
        :param password: password for the machine you wish to run command on
        :param transport: method of transportation
        :param server_cert_validation: whether or not to verify certificates
        :param message_encryption: When you should encrypt messages

        :return: dict of results with hosts as keys and list of outputs for each specified hosts
        """
        results = {}

        for host in hosts:
            self.logger.info(f"Executing on {host}")
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                results[host] = await self.run_script(wsman, "scripts/Kansa/Modules/Net/Get-Arp.ps1")

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def get_proc_dump_kansa(self, hosts, username, password, transport, server_cert_validation,
                                  message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param shell_type: The type of shell you wish to rsun (i.e. "powershell")
        :param local_file_name: file name to run specified script from
        :param username: username of the machine you wish to run command on
        :param password: password for the machine you wish to run command on
        :param transport: method of transportation
        :param server_cert_validation: whether or not to verify certificates
        :param message_encryption: When you should encrypt messages

        :return: dict of results with hosts as keys and list of outputs for each specified hosts
        """
        results = {}

        for host in hosts:
            self.logger.info(f"Executing on {host}")
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                results[host] = await self.run_script(wsman, "scripts/Kansa/Modules/Process/Get-ProcDump.ps1")

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def get_procs_n_modules_kansa(self, hosts, username, password, transport, server_cert_validation,
                                        message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param shell_type: The type of shell you wish to rsun (i.e. "powershell")
        :param local_file_name: file name to run specified script from
        :param username: username of the machine you wish to run command on
        :param password: password for the machine you wish to run command on
        :param transport: method of transportation
        :param server_cert_validation: whether or not to verify certificates
        :param message_encryption: When you should encrypt messages

        :return: dict of results with hosts as keys and list of outputs for each specified hosts
        """
        results = {}

        for host in hosts:
            self.logger.info(f"Executing on {host}")
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                results[host] = await self.run_script(wsman, "scripts/Kansa/Modules/Process/Get-ProcsNModules.ps1")

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def get_procs_wmi_kansa(self, hosts, username, password, transport, server_cert_validation,
                                  message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param shell_type: The type of shell you wish to rsun (i.e. "powershell")
        :param local_file_name: file name to run specified script from
        :param username: username of the machine you wish to run command on
        :param password: password for the machine you wish to run command on
        :param transport: method of transportation
        :param server_cert_validation: whether or not to verify certificates
        :param message_encryption: When you should encrypt messages

        :return: dict of results with hosts as keys and list of outputs for each specified hosts
        """
        results = {}

        for host in hosts:
            self.logger.info(f"Executing on {host}")
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                results[host] = await self.run_script(wsman, "scripts/Kansa/Modules/Process/Get-ProcsWMI.ps1")

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results


if __name__ == "__main__":
    asyncio.run(AdversaryHunting.run())
