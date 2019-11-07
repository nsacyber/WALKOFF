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


class MitreAttack(AppBase):
    __version__ = "1.0.0"
    app_name = "mitre_attack"

    def __init__(self, redis, logger):
        super().__init__(redis, logger)

    async def set_timestamp(self):
        timestamp = '{:%Y-%m-%d_%H-%M-%S}'.format(datetime.datetime.now())
        return timestamp

    async def account_manipulation(self, hosts, username, password, transport,
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
                    # This script returns events regarding account objects being changed
                    # as well as account names being changed

                    script = "Get-WinEvent -LogName security | Where-Object {$_.ID -eq 4738 -or $_.ID -eq 4781}"

                    ps = PS(pool)
                    ps.add_script(script)
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

    async def scheduled_tasks(self, hosts, username, password, transport, server_cert_validation,
                                               message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
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

                    script = """
                    wevtutil sl  Microsoft-Windows-TaskScheduler/Operational  /e:true
                    
                    Get-WinEvent -LogName  'Microsoft-Windows-TaskScheduler/Operational' | Where-Object  $_.Id -eq 106 
                    -or ($_.Id -eq 140) -or $_.Id -eq 141  } | Format-Table TimeCreated,Id,LevelDisplayName,Message
                    """

                    ps = PS(pool)
                    ps.add_script(script)
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

    async def pass_the_hash_one(self, hosts, username, password, transport, server_cert_validation,
                              message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
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
                    # This script searches event logs for successful logons,
                    # Logon attmepts, and failed logon attempts

                    script = "Get-WinEvent -LogName security | Where-Object {$_.ID -eq 4624 -or $_.ID -eq 4648 -or $_.ID -eq 4625} | Format-Table TimeCreated,Id,LevelDisplayName,Message"

                    ps = PS(pool)
                    ps.add_script(script)
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

    async def modify_existing_service(self, hosts, username, password, transport, server_cert_validation,
                              message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
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
                    # This script searches event logs for successful logons,
                    # Logon attmepts, and failed logon attempts

                    script = "Get-ChildItem ‘HKLM:\SYSTEM\CurrentControlSet\Services' -Recurse"

                    ps = PS(pool)
                    ps.add_script(script)
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

    async def accessibility_features(self, hosts, username, password, transport, server_cert_validation,
                              message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
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
                    # This script searches event logs for successful logons,
                    # Logon attmepts, and failed logon attempts

                    script =  "Get-ChildItem ‘HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options' -Recurse"
                    ps = PS(pool)
                    ps.add_script(script)
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
    asyncio.run(MitreAttack.run())
