from core.decorators import datafilter


@datafilter
def json_select(json, path):
    working = json
    for path_element in path:
        working = working[path_element]
    print('Selected: {0}'.format(working))
    return working


@datafilter
def list_select(list_in, index):
    return list_in[index]
