from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
from core import config
from os import sep
"""
Let's you use PyCallGraph as a decorator
"""


def callgraph(enabled=False):
    def argwrapper(func):
        def callwrapper(*args, **kwargs):
            if callwrapper.already_called or not enabled:
                return func(*args, **kwargs)
            callwrapper.already_called = True
            graphviz = GraphvizOutput()
            graphviz.output_file = config.profileVisualizationsPath + ('%s.png' % str(func.__name__))
            with PyCallGraph(output=graphviz):
                result = func(*args, **kwargs)
            return result

        callwrapper.already_called = False
        return callwrapper

    return argwrapper
