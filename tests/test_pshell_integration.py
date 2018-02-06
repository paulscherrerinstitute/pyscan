import unittest

from pyscan import StaticPositioner, function_value, scan

from tests.helpers.mock_pshell_function import MockPShellFunction


class PshellIntegration(unittest.TestCase):

    def test_pshell_function(self):

        n_steps = 5

        pshell_test = MockPShellFunction(script_name="test/DataLink.py",
                                         parameters={"scan_start": 0,
                                                     "scan_stop": 10,
                                                     "scan_steps": n_steps},
                                         scan_in_background=False)

        result = pshell_test.read()

        self.assertIsNotNone(pshell_test.read())

        self.assertTrue(isinstance(result, dict))

        self.assertEqual(n_steps + 1, len(result["data"]))

        for index in range(n_steps + 1):
            result["data"][index] == float(index)

    def test_pshell_function_in_scan(self):

        n_steps = 5

        pshell_test = MockPShellFunction(script_name="test/DataLink.py",
                                         parameters={"scan_start": 0,
                                                     "scan_stop": 10,
                                                     "scan_steps": n_steps},
                                         scan_in_background=False)

        n_positions = 5

        positioner = StaticPositioner(n_positions)
        readables = function_value(pshell_test.read)

        result = scan(positioner=positioner,
                      readables=readables)

        self.assertEqual(n_positions, len(result))

        for position_index in range(n_positions):
            for value_index in range(n_steps + 1):
                result[position_index][0]["data"][value_index] == float(value_index)

