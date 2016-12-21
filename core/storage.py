

class Storage():
    def __init__(self,data={}):
        self.data = data

    def write(self, key, data):
        self.data[key] = data



    def __repr__(self):
        return str(self.data)