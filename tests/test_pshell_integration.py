import unittest

from pyscan import StaticPositioner, function_value, scan

from tests.helpers.mock_pshell_function import MockPShellFunction


class PshellIntegration(unittest.TestCase):

    def test_pshell_function(self):

        pshell_test = MockPShellFunction(script_name="test/DataLink.py",
                                         parameters={"scan_start": 0,
                                                     "scan_stop": 10,
                                                     "scan_steps": 10},
                                         scan_in_background=False)

        result = pshell_test.read()

        self.assertIsNotNone(pshell_test.read())

        self.assertTrue(isinstance(result, dict))

        self.assertEqual(1, len(result))

    def test_pshell_function_in_scan(self):

        pshell_test = MockPShellFunction(script_name="test/DataLink.py",
                                         parameters={"scan_start": 0,
                                                     "scan_stop": 10,
                                                     "scan_steps": 10},
                                         scan_in_background=False)

        n_positions = 5

        positioner = StaticPositioner(n_positions)
        readables = function_value(pshell_test.read)

        result = scan(positioner=positioner,
                      readables=readables)

        self.assertEqual(n_positions, len(result))
