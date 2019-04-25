import datetime
import asyncio
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

    async def exec_remote_command(self, hosts, commands, username, password, transport, server_cert_validation,
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
        status = "Success"
        self.logger.info(f"These are the hosts: {hosts}")
        self.logger.info("HOST NUMERO UNO{}".format(hosts[1]))

        for host in hosts:
            results[host] = ""
            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)

                with WinRS(wsman) as shell:
                    process = Process(shell, commands)
                    process.invoke()
                    results[host] = {"stdout": process.stdout.decode(), "stderr": process.stderr.decode()}
                    process.signal(SignalCode.CTRL_C)

                    self.logger.info("Done executing on {}".format(host))
            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results, status

    async def exec_remote_script(self, hosts, executable, arguments, username, password, transport, server_cert_validation,
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
        status = "Success"

        for host in hosts:
            self.logger.info("Executing on {}".format(host))
            results[host] = ""

            try:
                wsman = WSMan(host, ssl=server_cert_validation, auth=transport, encryption=message_encryption,
                              username=username, password=password)
                self.logger.info("EXECUTING2")

                with WinRS(wsman) as shell:
                    # for command in commands:
                    process = Process(shell, executable, arguments)
                    process.begin_invoke()  # start the invocation and return immediately
                    process.poll_invoke()  # update the output stream
                    process.end_invoke()  # finally wait until the process is finished
                    results[host] = {"stdout": process.stdout.decode(), "stderr": process.stderr.decode()}
                    process.signal(SignalCode.CTRL_C)

                    self.logger.info("Done executing on {}".format(hosts))
            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results, status

    #     script = "$t = @'\n{}\n'@".format(script)
    #     script += ';Invoke-Expression $t'


if __name__ == "__main__":

    asyncio.run(PowerShell.run())
