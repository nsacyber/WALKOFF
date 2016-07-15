from core import app
import paramiko
import os, socket, sys

class Main(app.App):
    def __init__(self, name=None, device=None):
        app.App.__init__(self, name, device)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def secureCopy(self, args={}):
        try:
            self.sock.connect((self.config.ip, self.config.port))
            t = paramiko.Transport(self.sock)
            t.start_client()
            t.auth_password(self.config.username, self.config.password)

            scp_channel = t.open_session()
            lf = file(args["localPath"], 'rb')

            scp_channel.exec_command("scp -v -t %s\n"
                                     % args["remotePath"])

            print '/'.join(args["remotePath"].split('/')[:-1])
            scp_channel.send('C%s %d %s\n'
                             %(oct(os.stat(args["localPath"]).st_mode)[-4:],
                               os.stat(args["localPath"])[6],
                               args["remotePath"].split('/')[-1]))

            scp_channel.sendall(lf.read())

            lf.close()
            scp_channel.close()
            t.close()
            self.sock.close()
        except Exception as e:
            print e
            return "UNSUCCESSFUL"
        return "SUCCESS"


    def shutdown(self):
        return