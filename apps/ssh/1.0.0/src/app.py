import os
import logging
import asyncio

import asyncssh
import shutil

from walkoff_app_sdk.app_base import AppBase

logger = logging.getLogger("apps")


class SSH(AppBase):
    __version__ = "1.0.0"
    app_name = "ssh"

    def __init__(self, redis, logger):
        super().__init__(redis, logger)

    async def exec_local_command(self, command):
        proc = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE,
                                                     stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        return {"stdout": str(stdout), "stderr": str(stderr)}

    async def exec_command(self, hosts, port=None, args=None, username=None, password=None):
        results = {}

        for host in hosts:
            try:
                async with asyncssh.connect(host=host, port=port, username=username, password=password,
                                            known_hosts=None) as conn:
                    for cmd in args:
                        temp = await conn.run(cmd)
                        output = temp.stdout
                        results[host] = {"stdout": output, "stderr": ""}
            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results

    async def sftp_copy(self, src_path, dest_path, src_host, src_port, src_username, src_password, dest_host,
                             dest_port, dest_username, dest_password):

        curr_dir = os.getcwd()
        temp_dir = os.path.join(curr_dir, r'temp_data')
        os.makedirs(temp_dir, exist_ok=True)

        async with asyncssh.connect(host=src_host, port=src_port, username=src_username, password=src_password,
                                    known_hosts=None) as conn:
            async with asyncssh.connect(host=dest_host, port=dest_port, username=dest_username, password=dest_password,
                                        tunnel=conn, known_hosts=None) as tunneled_conn:

                # allowing for ~ (home directory)
                if dest_path[0] == "~":
                    s = list(dest_path)
                    s[0] = "."
                    dest_path = "".join(s)

                if src_path[0] == "~":
                    s = list(src_path)
                    s[0] = "."
                    src_path = "".join(s)

                # grab remote file, place in container
                try:
                    async with conn.start_sftp_client() as sftp:
                        await sftp.mget(src_path, temp_dir)
                except asyncssh.SFTPError as e:
                    try:
                        async with conn.start_sftp_client() as sftp:
                            await sftp.mget(src_path, temp_dir, recurse=True)
                    except Exception as e2:
                        return f"{e2}"

                spliced_path = src_path.split('/')
                file_name = spliced_path[len(spliced_path) - 1]

                # copy grabbed file to desired location
                try:
                    async with tunneled_conn.start_sftp_client() as sftp2:
                        await sftp2.mput(temp_dir + "/" + file_name, dest_path)
                except asyncssh.SFTPError as e:
                    try:
                        async with tunneled_conn.start_sftp_client() as sftp2:
                            await sftp2.mput(temp_dir + "/" + file_name, dest_path, recurse=True)
                    except Exception as e2:
                        return f"{e2}"

        # cleaning up temp file
        try:
            shutil.rmtree(temp_dir)
        except:
            print("Error while deleting container directory.")

        return "Successfully Copied File(s)."


    async def sftp_copy_from_json(self, input):
        try:
            src_path = input.get("src_path")
            dest_path = input.get("dest_path")
            src_host = input.get("src_host")
            src_port = input.get("src_port")
            src_username = input.get("src_username")
            src_password = input.get("src_password")
            dest_host = input.get("dest_host")
            dest_port = input.get("dest_port")
            dest_username = input.get("dest_username")
            dest_password = input.get("dest_password")

        except:
            return "Couldn't get all objects"


        curr_dir = os.getcwd()
        temp_dir = os.path.join(curr_dir, r'temp_data')
        os.makedirs(temp_dir)

        async with asyncssh.connect(host=src_host, port=src_port, username=src_username, password=src_password,
                                    known_hosts=None) as conn:
            async with asyncssh.connect(host=dest_host, port=dest_port, username=dest_username, password=dest_password,
                                        tunnel=conn, known_hosts=None) as tunneled_conn:
                # grab remote file, place in container
                async with conn.start_sftp_client() as sftp:
                    results = await sftp.get(src_path, temp_dir)

                spliced_path = src_path.split('/')
                file_name = spliced_path[len(spliced_path) - 1]

                # copy grabbed file to desired location
                async with tunneled_conn.start_sftp_client() as sftp2:
                    results2 = await sftp2.put(temp_dir + "/" + file_name, dest_path)

        # cleaning up temp file
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        os.rmdir(temp_dir)

        return "Successfully Copied File."

    async def run_shell_script_file(self, local_file_name, hosts, port, username, password):
        results = {}

        curr_dir = os.getcwd()
        temp_dir = os.path.join(curr_dir, r'shared')
        os.chdir(temp_dir)
        curr_dir = os.getcwd()
        local_file_path = os.path.join(curr_dir, local_file_name)

        for host in hosts:
            try:
                async with asyncssh.connect(host=host, port=port, username=username, password=password,
                                            known_hosts=None) as conn:
                    logger.info(f"Local file path -> {local_file_name}")
                    with open(local_file_path, "r") as f:
                        script = f.read()
                    cmd = script
                    temp = await conn.run(cmd)
                    output = temp.stdout
                    results[host] = {"stdout": output, "stderr": ""}
            except Exception as e:
                results[host] = {"stdout": "", "stderr": f"{e}"}

        return results


if __name__ == "__main__":
    asyncio.run(SSH.run())
