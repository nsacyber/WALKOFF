import datetime
import asyncio
import os
from pypsrp.client import Process, SignalCode, WinRS
from pypsrp.wsman import WSMan
from walkoff_app_sdk.app_base import AppBase


class PowerShell(AppBase):
    __version__ = "1.0.0"
    app_name = "power_shell"

    def __init__(self, redis, logger, console_logger=None):
        super().__init__(redis, logger, console_logger)

    async def set_timestamp(self):
        timestamp = '{:%Y-%m-%d_%H-%M-%S}'.format(datetime.utcnow())
        return timestamp

    async def exec_command_prompt_from_file(self, hosts, local_file_name, username, password, transport, server_cert_validation,
                            message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param message_encryption:
        :param password:
        :param username:
        :param hosts: list of hosts to execute on
        :param commands: list of commands to execute
        :return: dict of results with hosts as keys and list of outputs for each
        """

        results = {}
        curr_dir = os.getcwd()
        temp_dir = os.path.join(curr_dir, r'scripts')
        os.chdir(temp_dir)
        curr_dir = os.getcwd()
        local_file_path = os.path.join(curr_dir, local_file_name)

        for host in hosts:
            results[host] = ""
            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                with WinRS(wsman) as shell:
                    script = open(local_file_path, "r").read()
                    process = Process(shell, script)
                    process.invoke()
                    results[host] = {"stdout": process.stdout.decode(), "stderr": process.stderr.decode()}
                    process.signal(SignalCode.CTRL_C)

                    self.logger.info("Done executing on {}".format(host))
            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def exec_command_prompt(self, hosts, commands, username, password, transport, server_cert_validation,
                            message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        :param message_encryption:
        :param password:
        :param username:
        :param hosts: list of hosts to execute on
        :param commands: list of commands to execute
        :return: dict of results with hosts as keys and list of outputs for each
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

    async def exec_powershell_script_from_file(self, hosts, shell_type, local_file_name, username, password, transport, server_cert_validation,
                            message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        Outputs each host's file to a subdirectory of output_directory in output_filename
        :param ca_trust_path:
        :param message_encryption:
        :param password:
        :param username:
        :param hosts: list of hosts to execute on
        :param commands: list of commands to execute
        :return: dict of results with hosts as keys and list of outputs for each
        """
        results = {}
        curr_dir = os.getcwd()
        temp_dir = os.path.join(curr_dir, r'scripts')
        os.chdir(temp_dir)
        curr_dir = os.getcwd()
        local_file_path = os.path.join(curr_dir, local_file_name)

        for host in hosts:
            self.logger.info("Executing on {}".format(host))
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)
                self.logger.info("EXECUTING2")

                with WinRS(wsman) as shell:
                    # for command in commands:
                    script = open(local_file_path, "r").read()

                    process = Process(shell, shell_type, script)
                    process.begin_invoke()  # start the invocation and return immediately
                    process.poll_invoke()  # update the output stream
                    process.end_invoke()  # finally wait until the process is finished
                    results[host] = {"stdout": process.stdout.decode(), "stderr": process.stderr.decode()}
                    process.signal(SignalCode.CTRL_C)

                    self.logger.info("Done executing on {}".format(hosts))
            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def exec_powershell(self, hosts, shell_type, arguments, username, password, transport, server_cert_validation,
                            message_encryption):
        """
        Execute a list of remote commands on a list of hosts.
        Outputs each host's file to a subdirectory of output_directory in output_filename
        :param ca_trust_path:
        :param message_encryption:
        :param password:
        :param username:
        :param hosts: list of hosts to execute on
        :param commands: list of commands to execute
        :return: dict of results with hosts as keys and list of outputs for each
        """
        results = {}

        for host in hosts:
            self.logger.info("Executing on {}".format(host))
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)
                self.logger.info("EXECUTING2")

                with WinRS(wsman) as shell:
                    for arg in arguments:
                        process = Process(shell, shell_type, arg)
                        process.begin_invoke()  # start the invocation and return immediately
                        process.poll_invoke()  # update the output stream
                        process.end_invoke()  # finally wait until the process is finished
                        results[host] = {"stdout": process.stdout.decode(), "stderr": process.stderr.decode()}
                        process.signal(SignalCode.CTRL_C)

            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    #     script = "$t = @'\n{}\n'@".format(script)
    #     script += ';Invoke-Expression $t'


if __name__ == "__main__":

    asyncio.run(PowerShell.run())
