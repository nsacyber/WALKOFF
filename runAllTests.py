import unittest

from tests import testLoadWorkflow as ttw
from tests import testWorkflowManipulation as twm
from tests import testSimpleWorkflow as tsw
from tests import testExecutionRuntime as ter
from tests import testExecutionModes as tem
from tests import testExecutionEvents as tee
from tests import testTriggers as ttr
from tests import testServer as tsv
from tests import testUsersAndRoles as tur
from tests import testCaseSubscriptions as tcs
from tests import testCaseDatabase as tdb

loadWorkflow = unittest.TestLoader().loadTestsFromTestCase(ttw.TestLoadWorkflow)
manipulateWorkflow = unittest.TestLoader().loadTestsFromTestCase(twm.TestWorkflowManipulation)
executeWorkflow = unittest.TestLoader().loadTestsFromTestCase(tsw.TestSimpleWorkflow)
executionRuntime = unittest.TestLoader().loadTestsFromTestCase(ter.TestExecutionRuntime)
executionModes = unittest.TestLoader().loadTestsFromTestCase(tem.TestExecutionModes)
executionEvents = unittest.TestLoader().loadTestsFromTestCase(tee.TestExecutionEvents)
triggers = unittest.TestLoader().loadTestsFromTestCase(ttr.TestTriggers)
login = unittest.TestLoader().loadTestsFromTestCase(tsv.TestTriggers)
usersAndRoles = unittest.TestLoader().loadTestsFromTestCase(tur.TestUsersAndRoles)
caseSubs = unittest.TestLoader().loadTestsFromTestCase(tcs.TestCaseSubscriptions)
caseDb = unittest.TestLoader().loadTestsFromTestCase(tdb.TestCaseDatabase)
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(loadWorkflow)
    unittest.TextTestRunner(verbosity=2).run(manipulateWorkflow)
    unittest.TextTestRunner(verbosity=2).run(executeWorkflow)
    unittest.TextTestRunner(verbosity=2).run(executionRuntime)
    unittest.TextTestRunner(verbosity=2).run(executionModes)
    unittest.TextTestRunner(verbosity=2).run(executionEvents)
    unittest.TextTestRunner(verbosity=2).run(caseSubs)
    unittest.TextTestRunner(verbosity=2).run(caseDb)
    unittest.TextTestRunner(verbosity=2).run(triggers)
    unittest.TextTestRunner(verbosity=2).run(login)
    unittest.TextTestRunner(verbosity=2).run(usersAndRoles)

