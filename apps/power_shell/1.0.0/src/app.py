import datetime
import asyncio
import logging
import json
import os

from pypsrp.client import Client, Process, SignalCode, WinRS, PowerShell as PS, RunspacePool
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

    def __init__(self, redis, logger):
        super().__init__(redis, logger)

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

    async def exec_powershell_script_dependencies(self, hosts, shell_type, arguments, dependency_folder, destination_folder, username, password, transport,
                                                     server_cert_validation,
                                                     message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param hosts: List of host ips to run command on
        :param shell_type: The type of shell you wish to run (i.e. "powershell")
        :param commands: array of commands in which you want to run on every host
        :param dependency_folder: Specifies the local folder to copy
        :param destination_folder: Specifies the destination folder to copy and delete
        :param username: username of the machine you wish to run command on
        :param password: password for the machine you wish to run command on
        :param transport: method of transportation
        :param server_cert_validation: whether or not to verify certificates
        :param message_encryption: When you should encrypt messages

        :return: dict of results with hosts as keys and list of outputs for each specified hosts
        """
        results = {}

        for host in hosts:
            self.logger.info(f"Connecting to {host}")
            results[host] = []

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)
                client = Client(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                self.logger.info(f"Copying to {host}")
                for root, dirs, files in os.walk(dependency_folder):
                    root_folder = destination_folder + "\\" + os.path.basename(root)
                    output, streams, had_errors = client.execute_ps('''
                        $path = "%s"

                        if(!(Test-Path -Path $path )){
                            New-Item -ItemType directory -Path $path
                            Write-Host "New folder created"
                        }''' % root_folder)

                    results[host].append({"stdout": output, "had_errors": had_errors})
                    for file in files:
                        client.copy(os.path.join(root, file), root_folder + "\\" + file)

                self.logger.info(f"Executing on {host}")

                # execute scripts
                with WinRS(wsman) as shell:
                    #Changes directory to dependency root and appends folder removal to end
                    arguments = f"cd {destination_folder};" + '; '.join(arguments) 
                    self.logger.info(f"{arguments}")
                    process = Process(shell, shell_type, [arguments])
                    process.invoke()
                    results[host].append({"stdout": process.stdout.decode(), "stderr": process.stderr.decode()})

                    arguments = f"Remove-Item -Recurse {destination_folder}"
                    self.logger.info(f"Removing from {host}")
                    process = Process(shell, shell_type, [arguments])
                    process.invoke()
                    process.signal(SignalCode.CTRL_C)

            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                results[host].append({"stdout": "", "stderr": f"{e}", "exception": f"{tb}" })

        return results


if __name__ == "__main__":
    asyncio.run(PowerShell.run())
