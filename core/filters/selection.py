from core.decorators import datafilter
import json


@datafilter
def json_select(json_in, element):
    return json_in[element]


@datafilter
def list_select(list_in, index):
    return json.loads(list_in)[index]
