import unittest
from tests import testBenchmarks as tel

workflowExecutionLoads = unittest.TestLoader().loadTestsFromTestCase(tel.TestExecutionLoads)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(workflowExecutionLoads)
