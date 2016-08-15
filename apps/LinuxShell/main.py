from core import app
import paramiko, json, socket, os

class Main(app.App):
    def __init__(self, name=None, device=None):
        app.App.__init__(self, name, device)

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.config.ip, self.config.port, self.config.username, self.config.password)

    def execScript(self, args={}):
        return

    def execCommand(self, args={}):
        result = []
        if "command" in args:
            for cmd in args["command"]:
                stdin, stdout, stderr = self.ssh.exec_command(cmd)
                output = stdout.read()
                result.append(output)

        return str(result)

    def secureCopy(self, args={}):
        try:
            print os.path.abspath(args['localPath'])

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.config.ip, self.config.port))
            t = paramiko.Transport(sock)
            t.start_client()
            t.auth_password(self.config.username, self.config.password)

            scp_channel = t.open_session()
            lf = file(args["localPath"], 'rb')

            scp_channel.exec_command("scp -v -t %s\n"
                                     % args["remotePath"])
            print args["remotePath"]
            scp_channel.send('C%s %d %s\n'
                             %(oct(os.stat(args["localPath"]).st_mode)[-4:],
                               os.stat(args["localPath"])[6],
                               args["remotePath"].split('/')[-1]))

            scp_channel.sendall(lf.read())

            lf.close()
            scp_channel.close()
            t.close()
            sock.close()

        except Exception as e:
            sock.close()
            print e
            print "UNSUCCESSFUL"
            return "UNSUCCESSFUL"
        return "SUCCESS"


    def shutdown(self):
        if self.ssh:
            print "SSH Connection Closed"
            self.ssh.close()
        return