import unittest

from tests import testLoadWorkflow as ttw
from tests import testWorkflowManipulation as twm
from tests import testSimpleWorkflow as tsw
from tests import testExecutionRuntime as ter
from tests import testExecutionModes as tem

loadWorkflow = unittest.TestLoader().loadTestsFromTestCase(ttw.TestLoadWorkflow)
manipulateWorkflow = unittest.TestLoader().loadTestsFromTestCase(twm.TestWorkflowManipulation)
executeWorkflow = unittest.TestLoader().loadTestsFromTestCase(tsw.TestSimpleWorkflow)
executionRuntime = unittest.TestLoader().loadTestsFromTestCase(ter.TestExecutionRuntime)
executionModes = unittest.TestLoader().loadTestsFromTestCase(tem.TestExecutionModes)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(loadWorkflow)
    unittest.TextTestRunner(verbosity=2).run(manipulateWorkflow)
    unittest.TextTestRunner(verbosity=2).run(executeWorkflow)
    unittest.TextTestRunner(verbosity=2).run(executionRuntime)
    unittest.TextTestRunner(verbosity=2).run(executionModes)