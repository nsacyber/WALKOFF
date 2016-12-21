import unittest, os

from tests import testLoadWorkflow as ttw
from tests import testWorkflowManipulation as twm
from tests import testSimpleWorkflow as tsw

loadWorkflow = unittest.TestLoader().loadTestsFromTestCase(ttw.TestLoadWorkflow)
manipulateWorkflow = unittest.TestLoader().loadTestsFromTestCase(twm.TestWorkflowManipulation)
executeWorkflow = unittest.TestLoader().loadTestsFromTestCase(tsw.TestSimpleWorkflow)

unittest.TextTestRunner(verbosity=2).run(loadWorkflow)
unittest.TextTestRunner(verbosity=2).run(manipulateWorkflow)
unittest.TextTestRunner(verbosity=2).run(executeWorkflow)