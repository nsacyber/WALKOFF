from server.appdevice import App
import os, subprocess, signal


class Main(App):

    def __init__(self, name=None, device=None):
        self.curDirPath = os.path.dirname(os.path.realpath(__file__))
        self.greeting = "No greeting provided"
        self.totalNodes = "2"
        App.__init__(self, name, device)

    def create_accounts(self, args={}):
        res = 0
        if args["total_nodes"] and args["total_nodes"] > 2:
            self.totalNodes = str(args["total_nodes"])

        self.terminate_geth_processes()
        res &= self.run_script(["step1-create-accounts.sh", self.totalNodes])
        return res

    def set_up_network(self, args={}):
        res = 0
        res &= self.run_script(["step2-create-genesis-file.sh"])
        res &= self.run_script(["step3-start-miners.sh"])
        res &= self.run_script(["step4-connect-miners.sh", self.totalNodes])
        res &= self.run_script(["step5-deploy-contract.sh", self.totalNodes])
        return res

    def submit_greeting(self, args={}):
        if args["greeting"]:
            self.greeting = args["greeting"]
        return self.run_script(["step6-submit-greeting.sh", self.greeting])

    def run_script(self, args=[]):
        args[0] = self.curDirPath + "/" + args[0] # Full path to the script file
        args.insert(1, self.curDirPath) # Full path to the Ethereum Blockchain directory
        process = subprocess.Popen(args)
        return process.wait()

    def terminate_geth_processes(self, args={}):
        processName = "geth"
        psCmd = subprocess.Popen("ps -A", shell=True, stdout=subprocess.PIPE)
        grepCmd = subprocess.Popen("grep " + processName, shell=True, stdin=psCmd.stdout, stdout=subprocess.PIPE)
        out, err = grepCmd.communicate()
        for line in out.splitlines():
            pid = int(line.split(None, 1)[0])
            os.kill(pid, signal.SIGKILL)