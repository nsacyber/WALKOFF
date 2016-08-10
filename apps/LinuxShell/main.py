from core import app
import paramiko, json

class Main(app.App):
    def __init__(self, name=None, device=None):
        app.App.__init__(self, name, device)

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.config.ip, self.config.port, self.config.username, self.config.password)

    def execScript(self, args={}):
        return

    def execCommand(self, args=[]):
        result = []
        if "command" in args:
            for cmd in args["command"]:
                stdin, stdout, stderr = self.ssh.exec_command(cmd)
                output = stdout.read()
                result.append(output)

        return str(result)



    def shutdown(self):
        if self.ssh:
            print "SSH Connection Closed"
            self.ssh.close()
        return