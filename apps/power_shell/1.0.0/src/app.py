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


class PowerShell(AppBase):
    __version__ = "1.0.0"
    app_name = "power_shell"

    def __init__(self, redis, logger, console_logger=None):
        super().__init__(redis, logger, console_logger)

    async def set_timestamp(self):
        timestamp = '{:%Y-%m-%d_%H-%M-%S}'.format(datetime.datetime.now())
        return timestamp

    async def exec_command_prompt_from_file(self, hosts, local_file_name, username, password, transport,
                                            server_cert_validation,
                                            message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
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
            results[host] = ""
            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                with WinRS(wsman) as shell:
                    with open(local_file_name, "r") as f:
                        script = f.read()
                    process = Process(shell, script)
                    process.invoke()
                    results[host] = {"stdout": process.stdout.decode(), "stderr": process.stderr.decode()}
                    process.signal(SignalCode.CTRL_C)

                    self.logger.info(f"Done executing on {host}")
            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def exec_command_prompt(self, hosts, commands, username, password, transport, server_cert_validation,
                                  message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param commands: array of commands in which you want to run on every host
        :param username: username of the machine you wish to run command on
        :param password: password for the machine you wish to run command on
        :param transport: method of transportation
        :param server_cert_validation: whether or not to verify certificates
        :param message_encryption: When you should encrypt messages

        :return: dict of results with hosts as keys and list of outputs for each specified hosts
        """

        results = {}

        for host in hosts:
            results[host] = ""
            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                with WinRS(wsman) as shell:
                    for command in commands:
                        process = Process(shell, command)
                        process.invoke()
                        results[host] = {"stdout": process.stdout.decode(), "stderr": process.stderr.decode()}
                        process.signal(SignalCode.CTRL_C)

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def exec_powershell_script_from_file(self, hosts, shell_type, local_file_name, username, password, transport,
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
                    with open(local_file_name, "r") as f:
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
                    if ps.had_errors:
                        results[host] = {"stdout": "", "stderr": this_result}
                    else:
                        results[host] = {"stdout": this_result, "stderr": ""}

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def exec_powershell_script(self, hosts, shell_type, arguments, username, password, transport,
                                     server_cert_validation,
                                     message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param shell_type: The type of shell you wish to run (i.e. "powershell")
        :param commands: array of commands in which you want to run on every host
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

                with WinRS(wsman) as shell:
                    for arg in arguments:
                        process = Process(shell, shell_type, [arg])
                        process.begin_invoke()  # start the invocation and return immediately
                        process.poll_invoke()  # update the output stream
                        process.end_invoke()  # finally wait until the process is finished
                        results[host] = {"stdout": process.stdout.decode(), "stderr": process.stderr.decode()}
                        process.signal(SignalCode.CTRL_C)

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

if __name__ == "__main__":
    asyncio.run(PowerShell.run())
