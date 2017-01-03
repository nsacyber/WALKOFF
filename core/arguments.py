from jinja2 import Template
import xml.etree.cElementTree as et

from core import config

class Argument(object):
    def __init__(self, key=None, value=None, format="string"):
        self.key = key
        self.value = value
        self.templated = None
        self.format = type(format).__name__

    def __call__(self):
        return self.value

    def template(self, steps):
        t = Template(self.value)
        return t.render(steps=steps)

    def toXML(self):
        elem = et.Element(self.key)
        elem.text = self.value
        elem.set("format", self.format)
        return elem

    def __repr__(self):
        output={}
        output["key"] = self.key
        output["value"] = self.value
        output["type"] = self.format
        return str(output)

    def validate(self, action=None, io="input"):
        return any(x["name"] == self.key and x["type"] == self.format for x in config.functionConfig[action]["args"])







