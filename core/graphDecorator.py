from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
from core.config import paths
import os.path


def callgraph(enabled=False):
    """
    Let's you use PyCallGraph as a decorator
    """
    def argwrapper(func):
        def callwrapper(*args, **kwargs):
            if callwrapper.already_called or not enabled:
                return func(*args, **kwargs)
            callwrapper.already_called = True
            graphviz = GraphvizOutput()
            graphviz.output_file = os.path.join(paths.profile_visualizations_path, '{0}.png'.format(func.__name__))
            with PyCallGraph(output=graphviz):
                result = func(*args, **kwargs)
            return result

        callwrapper.already_called = False
        return callwrapper

    return argwrapper
