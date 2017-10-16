from core.decorators import transform
import json


@transform
def json_select(json_in, element):
    return json_in[element]


@transform
def list_select(list_in, index):
    return json.loads(list_in)[index]
