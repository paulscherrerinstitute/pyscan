import unittest

from pyscan import StaticPositioner, function_value, scan

from tests.helpers.mock_pshell_function import MockPShellFunction


class PshellIntegration(unittest.TestCase):

    def test_pshell_function(self):

        n_steps = 3

        # Actual parameters do not matter - the response if fixed.
        pshell_test = MockPShellFunction(script_name="",
                                         parameters={})

        result = pshell_test.read()

        self.assertIsNotNone(result)

        self.assertTrue(isinstance(result, list))

        self.assertEqual(n_steps, len(result))

        self.assertEqual(len(result[0]), 6)

        for index in range(n_steps):
            result[index][0] == float(10)
            result[index][1] == float(20)
            result[index][2] == float(50)
            result[index][3] == float(60)

    def test_pshell_function_in_scan(self):

        n_steps = 3

        pshell_test = MockPShellFunction(script_name="",
                                         parameters={})

        n_positions = 5

        positioner = StaticPositioner(n_positions)
        readables = function_value(pshell_test.read)

        result = scan(positioner=positioner,
                      readables=readables)

        self.assertEqual(n_positions, len(result))

        for position_index in range(n_positions):
            for step_index in range(n_steps):
                result[position_index][0][step_index][0] == float(10)

