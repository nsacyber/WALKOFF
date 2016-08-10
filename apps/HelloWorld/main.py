from core import app

#There is an associated Hello world test workflow which can be executed

class Main(app.App):
    def __init__(self, name=None, device=None):
        #The parent app constructor looks for a device configuration and returns that as a dictionary called self.config
        app.App.__init__(self, name, device)
        #Functions and Variables that are designed to exist across functions go here
        self.introMessage = {"message":"I SAY THIS BEFORE EVERY FUNCTION: HELLO WORLD"}

    #Every function in Main is an action that can be taken
    #Every function needs to define an args argument which recieves a dictionary of input parameters
    def helloWorld(self, args={}):
        #LOOK AT YOUR CONSOLE WHEN EXECUTING
        print self.introMessage

        return self.introMessage

    #Example using arguments
    #Repeats back the contents of the call argument
    def repeatBackToMe(self, args={}):
        print "REPEATING: " + args["call"]

        return "REPEATING: " + args["call"]

    def shutdown(self):
        print "SHUTTING DOWN"
        return