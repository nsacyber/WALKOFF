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

    def __init__(self, redis, logger, console_logger=None):
        super().__init__(redis, logger, console_logger)

    async def set_timestamp(self):
        timestamp = '{:%Y-%m-%d_%H-%M-%S}'.format(datetime.datetime.now())
        return timestamp

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

                with RunspacePool(wsman) as pool:
                    with open("scripts/Get-DLLInfo.ps1", "r") as f:
                        script = f.read()
                    ps = PS(pool)
                    ps.add_script(script).add_argument("localhost")
                    ps.invoke()
                    this_result = []
                    for line in ps.output:
                        this_result.append({
                            "name": str(line),
                            "adapted_properties": json.loads(json.dumps(line.adapted_properties, cls=ObjectEncoder)),
                            "extended_properties": json.loads(json.dumps(line.extended_properties, cls=ObjectEncoder))
                        })
                    if ps.had_errors:
                        results[host] = {"stdout": "", "stderr": this_result}
                    else:
                        results[host] = {"stdout": this_result, "stderr": ""}

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

                with RunspacePool(wsman) as pool:
                    with open("scripts/Get-InstalledApps.ps1", "r") as f:
                        script = f.read()
                    ps = PS(pool)
                    ps.add_script(script).add_argument("localhost")
                    ps.invoke()
                    this_result = []
                    for line in ps.output:
                        this_result.append({
                            "name": str(line),
                            "adapted_properties": json.loads(json.dumps(line.adapted_properties, cls=ObjectEncoder)),
                            "extended_properties": json.loads(json.dumps(line.extended_properties, cls=ObjectEncoder))
                        })
                    if ps.had_errors:
                        results[host] = {"stdout": "", "stderr": this_result}
                    else:
                        results[host] = {"stdout": this_result, "stderr": ""}

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

                with RunspacePool(wsman) as pool:
                    with open("scripts/Get-NetStat.ps1", "r") as f:
                        script = f.read()
                    ps = PS(pool)
                    ps.add_script(script).add_argument("localhost")
                    ps.invoke()
                    this_result = []
                    for line in ps.output:
                        this_result.append({
                            "name": str(line),
                            "adapted_properties": json.loads(json.dumps(line.adapted_properties, cls=ObjectEncoder)),
                            "extended_properties": json.loads(json.dumps(line.extended_properties, cls=ObjectEncoder))
                        })
                    if ps.had_errors:
                        results[host] = {"stdout": "", "stderr": this_result}
                    else:
                        results[host] = {"stdout": this_result, "stderr": ""}

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

                with RunspacePool(wsman) as pool:
                    with open("scripts/Get-NetworkAdapter.ps1", "r") as f:
                        script = f.read()
                    ps = PS(pool)
                    ps.add_script(script).add_argument("localhost")
                    ps.invoke()
                    this_result = []
                    for line in ps.output:
                        this_result.append({
                            "name": str(line),
                            "adapted_properties": json.loads(json.dumps(line.adapted_properties, cls=ObjectEncoder)),
                            "extended_properties": json.loads(json.dumps(line.extended_properties, cls=ObjectEncoder))
                        })
                    if ps.had_errors:
                        results[host] = {"stdout": "", "stderr": this_result}
                    else:
                        results[host] = {"stdout": this_result, "stderr": ""}

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

                with RunspacePool(wsman) as pool:
                    with open("scripts/Get-Processes.ps1", "r") as f:
                        script = f.read()
                    ps = PS(pool)
                    ps.add_script(script).add_argument("localhost")
                    ps.invoke()
                    this_result = []
                    for line in ps.output:
                        this_result.append({
                            "name": str(line),
                            "adapted_properties": json.loads(json.dumps(line.adapted_properties, cls=ObjectEncoder)),
                            "extended_properties": json.loads(json.dumps(line.extended_properties, cls=ObjectEncoder))
                        })
                    if ps.had_errors:
                        results[host] = {"stdout": "", "stderr": this_result}
                    else:
                        results[host] = {"stdout": this_result, "stderr": ""}

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

                with RunspacePool(wsman) as pool:
                    with open("scripts/Get-ScheduledTask.ps1", "r") as f:
                        script = f.read()
                    ps = PS(pool)
                    ps.add_script(script).add_argument("localhost")
                    ps.invoke()
                    this_result = []
                    for line in ps.output:
                        this_result.append({
                            "name": str(line),
                            "adapted_properties": json.loads(json.dumps(line.adapted_properties, cls=ObjectEncoder)),
                            "extended_properties": json.loads(json.dumps(line.extended_properties, cls=ObjectEncoder))
                        })
                    if ps.had_errors:
                        results[host] = {"stdout": "", "stderr": this_result}
                    else:
                        results[host] = {"stdout": this_result, "stderr": ""}

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

                with RunspacePool(wsman) as pool:
                    with open("scripts/Get-Services.ps1", "r") as f:
                        script = f.read()
                    ps = PS(pool)
                    ps.add_script(script).add_argument("localhost")
                    ps.invoke()
                    this_result = []
                    for line in ps.output:
                        this_result.append({
                            "name": str(line),
                            "adapted_properties": json.loads(json.dumps(line.adapted_properties, cls=ObjectEncoder)),
                            "extended_properties": json.loads(json.dumps(line.extended_properties, cls=ObjectEncoder))
                        })
                    if ps.had_errors:
                        results[host] = {"stdout": "", "stderr": this_result}
                    else:
                        results[host] = {"stdout": this_result, "stderr": ""}

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results


if __name__ == "__main__":
    asyncio.run(AdversaryHunting.run())
