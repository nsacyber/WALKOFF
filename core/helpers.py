import importlib

def returnCytoscapeData(steps):
    output = []
    for step in steps:
        node = {"group": "nodes", "data": {"id": steps[step]["name"]}}
        output.append(node)
        for next in steps[step].conditionals:
            edgeId = str(steps[step]["name"]) + str(next["name"])
            if next["name"] in steps:
                node = {"group": "edges", "data": {"id": edgeId, "source": steps[step]["name"], "target": next["name"]}}
            output.append(node)
    return output


def import_lib(dir, module_name):
    module = None
    try:
        module = importlib.import_module('.'.join('core', dir, module_name))
    except ImportError:
        pass
    finally:
        return module
