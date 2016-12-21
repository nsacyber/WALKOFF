from core import config
from jinja2 import Template

class Argument():
    def __init__(self, key=None, value=None, type="string"):
        self.key = key
        self.type = type
        self.value = value

    def __call__(self):
        return self.value

    def template(self, steps):
        t = Template(self.value)
        self.value = t.render(steps=steps)

    def __repr__(self):
        output={}
        output["key"] = self.key
        output["value"] = self.value
        output["type"] = self.type
        return str(output)

    def validate(self, action=None, io="input"):
        return any(x["name"] == self.key and x["type"] == self.type for x in config.functionConfig[action]["args"])







