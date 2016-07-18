from core import app
import paramiko

class Main(app.App):
    def __init__(self, name=None, device=None):
        app.App.__init__(self, name, device)

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.config.ip, self.config.port, self.config.username, self.config.password)

    def execScript(self, args={}):
        return

    def execCommand(self, args=[]):
        if "command" in args:
            stdin, stdout, stderr = self.ssh.exec_command(args["command"])
            print "OUTPUT: ", stdout.read()

            return stdout.read()


    def shutdown(self):
        if self.ssh:
            print "SSH Connection Closed"
            self.ssh.close()
        return