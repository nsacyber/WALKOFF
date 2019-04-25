import os, sys

import logging

import asyncio
import asyncssh

from pathlib import Path

from walkoff_app_sdk.app_base import AppBase
logger = logging.getLogger("apps")


class SSH(AppBase):
    """
    Initialize the Linux Shell App, which includes initializing the SSH client given the host address, port, username, and
    password for the remote server
    """
    __version__ = "1.0.0"
    app_name = "ssh"

    def __init__(self, redis, logger, console_logger=None):
        super().__init__(redis, logger, console_logger)


    async def exec_command(self, args, host, port, username, password):
        """ Use SSH client to execute commands on the remote server and produce an array of command outputs
        Input:
            args: A string array of commands
        Output:
            result: A String array of the command outputs
        """
        # known_hosts = None -> disables known_hosts check
        async with asyncssh.connect(host=host,  port=port, username=username, password=password, known_hosts=None) as conn:
            result = []
            for cmd in args:
                temp = await conn.run(cmd)
                output = temp.stdout
                result.append(output)
        
        return str(result), 'Success'


    # async def sftp_put(self, src_path, dest_path, src_host, src_port, src_username, src_password, dest_host, dest_port, dest_username, dest_password):
    #     """
    #     Use SSH client to copy a local file to the remote server using sftp
    #     Input:
    #         args: local_path and remote_path of file
    #     Output:
    #         Success/Failure
    #     """

    #     async with asyncssh.connect(host=src_host,  port=src_port, username=src_username, password=src_password, known_hosts=None) as conn:
    #         async with asyncssh.connect(host=dest_host,  port=dest_port, username=dest_username, password=dest_password, tunnel=conn, known_hosts=None) as tunneled_conn:
    #             # grab remote file, place in container
    #             async with conn.start_sftp_client() as sftp:
    #                 result = await sftp.get(src_path)

    #             # copy grabbed file to desired location
    #             async with tunneled_conn.start_sftp_client() as sftp2:
    #                 result2 = await sftp2.put("hannah_was_here.txt", dest_path)

    #     return "Success"


    async def sftp_copy(self, src_path, dest_path, src_host, src_port, src_username, src_password, dest_host, dest_port, dest_username, dest_password):
        """
        Use SSH client to copy a remote file to local using sftp
        Use SSH client to Copy remote files to a new location. 
           This method copies one or more files or directories on the
           remote system to a new location. Either a single source path
           or a sequence of source paths to copy can be provided.
        Input:
            args: local_path and remote_path of file
        Output:
            Success/Failure
        """

        curr_dir = os.getcwd()
        temp_dir = os.path.join(curr_dir, r'temp_data')
        os.makedirs(temp_dir)

        async with asyncssh.connect(host=src_host,  port=src_port, username=src_username, password=src_password, known_hosts=None) as conn:
            async with asyncssh.connect(host=dest_host,  port=dest_port, username=dest_username, password=dest_password, tunnel=conn, known_hosts=None) as tunneled_conn:
                # grab remote file, place in container
                async with conn.start_sftp_client() as sftp:
                    result = await sftp.get(src_path, temp_dir)

                spliced_path = src_path.split('/')
                file_name = spliced_path[len(spliced_path) - 1]

                # copy grabbed file to desired location
                async with tunneled_conn.start_sftp_client() as sftp2:
                    result2 = await sftp2.put(temp_dir + "/" + file_name, dest_path)

        # clearning up temp file
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        os.rmdir(temp_dir)

        return "Success"


    async def run_shell_script(self, path, host, port, username, password):
        """ Use SSH client to execute a shell script on the remote server and produce an array of command outputs
        Input:
            args: local filepath of the shell script
        Output:
            result: A String array of the command outputs
        """
        async with asyncssh.connect(host=host,  port=port, username=username, password=password, known_hosts=None) as conn:
            result = []
            script = open(local_path, "r").read()
            cmd = "eval " + script
            temp = await conn.run(cmd)
            output = temp.stdout
            result.append(output)

        return str(result), 'Success'


    # def block_ips(self, ips, host, port, username, password):
    #     output = ""
    #     for ip in ips:
    #         self.exec_command(["iptables -A INPUT -s {} -j DROP".format(ip)], host, port, username, password)
    #         output = output + ("Blocking IP {}".format(ip))
    #     return True, 'Success'

    # async def shutdown(self, host, port, username, password):
    #     """
    #     Close the SSH connection if there is a SSH connection
    #     """
    #     try:
    #         async with asyncssh.connect(host=host,  port=port, username=username, password=password, known_hosts=None) as conn:
    #             conn.close()
    #             await conn.wait_closed()
    #             return True, "SSH Connection Closed"
    #     except:
    #         return False, "Unable to Close SSH Connection"


if __name__ == "__main__":
    asyncio.run(SSH.run())
    # asyncio.get_event_loop().run_until_complete(SSH.run())
