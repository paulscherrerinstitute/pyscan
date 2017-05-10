import unittest
from itertools import count

from pyscan.positioner.area import AreaPositioner, ZigZagAreaPositioner, MultiAreaPositioner
from pyscan.positioner.compound import CompoundPositioner
from pyscan.positioner.line import LinePositioner, ZigZagLinePositioner
from pyscan.positioner.serial import SerialPositioner
from pyscan.positioner.vector import VectorPositioner, ZigZagVectorPositioner
from pyscan.utils import convert_to_position_list
from tests.helpers.utils import is_close


class DiscreetPositionersTests(unittest.TestCase):
    def verify_result(self, positioner, expected_result):
        """
        Test if the output positions are close enough to the desired one.
        :param positioner: Positioner instance to get the positions from.
        :param expected_result: Expected values.
        """
        positions = list(positioner.get_generator())
        self.assertEqual(len(positions), len(expected_result),
                         "The number of positions does not match "
                         "the expected one.\n"
                         "Received: %s\nExpected: %s." % (positions, expected_result))

        for i, position in enumerate(positions):
            self.assertTrue(is_close(position, expected_result[i]),
                            "The elements in position %d do not match the expected result.\n"
                            "Received: %s\nExpected: %s." % (i, positions, expected_result))

    def verify_multi_result(self, positioner, expected_result):
        """
        Same as verify_result, but for multiple values per position.
        :param positioner: Positioner instance to get the positions from.
        :param expected_result: Expected values.
        :return: 
        """
        positions = list(positioner.get_generator())

        for index, axis_positions, axis_expected in zip(count(), positions, expected_result):
            self.assertEqual(len(axis_positions), len(axis_expected),
                             "The number of positions at %d does not match "
                             "the expected one.\n"
                             "Received: %s\nExpected: %s." % (index, axis_positions, axis_expected))

            for individual_position, individual_expected in zip(axis_positions, axis_positions):
                self.assertTrue(is_close(individual_position, individual_expected),
                                "The elements in position %d do not match the expected result.\n"
                                "Received: %s\nExpected: %s." % (index, positions, expected_result))

    def standard_linear_tests(self, positioner_type):
        """
        Collection of standard tests that every linear discreet positioner should pass.
        :param positioner_type: Class to test.
        """
        expected_result = [[-2.], [-1.], [0.], [1.], [2.]]

        # Generate 5 steps, from -2 to 2, using number of steps.
        self.verify_result(positioner_type([-2], [2], n_steps=4), expected_result)

        # Generate 5 steps, from -2 to 2, using step size.
        self.verify_result(positioner_type([-2], [2], step_size=[1.]), expected_result)

        # Generate 5 steps, from -2 to 2, using number of steps, with offset.
        self.verify_result(positioner_type(-4, 0, n_steps=4, offsets=2), expected_result)

        # Generate 5 steps, from -2 to 2, using step size, with offset.
        self.verify_result(positioner_type([-4], [0], step_size=1, offsets=[2]), expected_result)

        expected_result = [[-2.], [-0.8], [0.4], [1.6]]

        # Generate 4 steps, from -2 to 2, using step size 1.2
        self.verify_result(positioner_type([-2], [2], step_size=[1.2]), expected_result)

        expected_result = [[2.], [1.], [0.], [-1.], [-2.]]

        # Generate 4 steps, from 2 to -2, using number of steps.
        self.verify_result(positioner_type([2], [-2], n_steps=4), expected_result)

        expected_result = [[2], [0.8], [-0.4], [-1.6]]

        # Generate 4 steps, from 2 to -2, using step size -1.2
        self.verify_result(positioner_type([2], [-2], step_size=[-1.2]), expected_result)

    def standard_linear_multipass_tests(self, positioner_type):
        """
        Multipass tests that every linear discreet positioner should pass.
        :param positioner_type:  Class to test.
        """
        expected_result = [[-2.], [-1.], [0.], [1.], [2.]]

        # Generate 10 steps, 2 passes, using number of steps.
        self.verify_result(positioner_type([-2], [2], n_steps=4, passes=2), expected_result * 2)

        # Generate 10 steps, 2 passes, using step size.
        self.verify_result(positioner_type([-2], [2], step_size=1, passes=2), expected_result * 2)

        # Generate 10 steps, 2 passes, using step size, with offset.
        self.verify_result(positioner_type([-4], [0], step_size=[1.], passes=2, offsets=[2]), expected_result * 2)

    def standard_linear_multipass_zigzag_tests(self, positioner_type):
        """
        Zigzag multipass tests that every linear discreet positioner should pass.
        :param positioner_type:  Class to test.
        """
        expected_3pass_result = [[-2.], [-1.], [0.], [1.], [2.], [1.], [0.], [-1.], [-2.], [-1.], [0.], [1.], [2.]]

        # Test if with 3 passes, it omits the duplicate positions.
        self.verify_result(positioner_type([-2], [2], n_steps=4, passes=3), expected_3pass_result)

        expected_3pass_result = [[-2.], [-0.8], [0.4], [1.6], [0.4], [-0.8], [-2.], [-0.8], [0.4], [1.6]]

        # Test what happens if the step size is not dividable by the interval, 3 passes.
        self.verify_result(positioner_type([-2], [2], step_size=1.2, passes=3), expected_3pass_result)

        expected_3pass_result = [[2.], [0.8], [-0.4], [-1.6], [-0.4], [0.8], [2.], [0.8], [-0.4], [-1.6]]

        # Test what happens if the step size is not dividable by the interval, 3 passes, right to left.
        self.verify_result(positioner_type([2], [-2], step_size=[-1.2], passes=3), expected_3pass_result)

    def test_LinePositioner(self):
        self.standard_linear_tests(LinePositioner)
        self.standard_linear_multipass_tests(LinePositioner)

        # Advance each given motor for each step.
        expected_result = [[0, 0, 0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0]]

        # Generate 3d steps, with number of steps.
        self.verify_result(LinePositioner([0, 0, 0], [2, 2, 2], n_steps=2), expected_result)
        # Generate 3d steps, with step size
        self.verify_result(LinePositioner([0, 0, 0], [2, 2, 2], step_size=[1., 1., 1.]), expected_result)

    def test_ZigZagLinearPositioner(self):
        self.standard_linear_tests(ZigZagLinePositioner)
        self.standard_linear_multipass_zigzag_tests(ZigZagLinePositioner)

    def test_VectorPositioner(self):
        expected_result = [[-2., -2], [-1., -1], [0., 0], [1., 1], [2., 2]]

        # # Test 1 pass.
        self.verify_result(VectorPositioner(expected_result), expected_result)

        # Test 3 passes.
        self.verify_result(VectorPositioner(expected_result, passes=3), expected_result * 3)

        expected_result = [[0.0, -1], [1.0, 0], [2.0, 1], [3.0, 2], [4.0, 3]]

        # Test offset.
        self.verify_result(VectorPositioner(expected_result, offsets=[2, 1]), expected_result)


    def test_ZigZagVectorPositioner(self):
        expected_single_result = [[-2., -2], [-1., -1], [0., 0], [1., 1], [2., 2]]
        expected_3pass_result = [[-2.0, -2], [-1.0, -1], [0.0, 0], [1.0, 1], [2.0, 2],
                                 [1.0, 1], [0.0, 0], [-1.0, -1], [-2.0, -2],
                                 [-1.0, -1], [0.0, 0], [1.0, 1], [2.0, 2]]

        # Verify that the positioner works the same with one pass.
        self.verify_result(ZigZagVectorPositioner(expected_single_result, passes=1), expected_single_result)

        # Check if the expected result with 3 passes is the same.
        self.verify_result(ZigZagVectorPositioner(expected_single_result, passes=3), expected_3pass_result)

    def test_AreaPositioner(self):
        self.standard_linear_tests(AreaPositioner)
        self.standard_linear_multipass_tests(AreaPositioner)

        expected_result = [[0.0, 0], [0.0, 3.0],
                           [3.0, 0], [3.0, 3.0]]
        # Check if the area positioner advances axes by axes.
        self.verify_result(AreaPositioner([0, 0], [3, 3], [1, 1]), expected_result)

        expected_result = [[0.0, 0], [0.0, 1.0], [0.0, 2.0], [0.0, 3.0], [0.0, 4.0],
                           [1.0, 0], [1.0, 1.0], [1.0, 2.0], [1.0, 3.0], [1.0, 4.0],
                           [2.0, 0], [2.0, 1.0], [2.0, 2.0], [2.0, 3.0], [2.0, 4.0],
                           [3.0, 0], [3.0, 1.0], [3.0, 2.0], [3.0, 3.0], [3.0, 4.0]]
        # Check if the dimensions are correct for 2d, with steps count.
        self.verify_result(AreaPositioner([0, 0], [3, 4], n_steps=[3, 4]), expected_result)
        # Check if the dimensions are correct for 2d, with steps size.
        self.verify_result(AreaPositioner([0, 0], [3, 4], step_size=[1., 1.]), expected_result)

        # Check if the dimensions are correct for 2d, with steps count, multi passes
        self.verify_result(AreaPositioner([0, 0], [3, 4], [3, 4], passes=3), expected_result * 3)
        # Check if the dimensions are correct for 2d, with steps size, multi passes
        self.verify_result(AreaPositioner([0, 0], [3, 4], step_size=[1., 1.], passes=3), expected_result * 3)

        expected_result = [[0.0, 0, 0], [0.0, 0, 2.0], [0.0, 1.0, 0], [0.0, 1.0, 2.0], [0.0, 2.0, 0], [0.0, 2.0, 2.0],
                           [1.0, 0, 0], [1.0, 0, 2.0], [1.0, 1.0, 0], [1.0, 1.0, 2.0], [1.0, 2.0, 0], [1.0, 2.0, 2.0],
                           [2.0, 0, 0], [2.0, 0, 2.0], [2.0, 1.0, 0], [2.0, 1.0, 2.0], [2.0, 2.0, 0], [2.0, 2.0, 2.0],
                           [3.0, 0, 0], [3.0, 0, 2.0], [3.0, 1.0, 0], [3.0, 1.0, 2.0], [3.0, 2.0, 0], [3.0, 2.0, 2.0],
                           [4.0, 0, 0], [4.0, 0, 2.0], [4.0, 1.0, 0], [4.0, 1.0, 2.0], [4.0, 2.0, 0], [4.0, 2.0, 2.0]]

        # Check if the dimensions are correct for 3d, with steps count.
        self.verify_result(AreaPositioner([0, 0, 0], [4, 2, 2], n_steps=[4, 2, 1]), expected_result)
        # Check if the dimensions are correct for 3d, with steps size.
        self.verify_result(AreaPositioner([0, 0, 0], [4, 2, 2], step_size=[1., 1., 2.]), expected_result)

        # Check if the dimensions are correct for 3d, with steps count, multi passes.
        self.verify_result(AreaPositioner([0, 0, 0], [4, 2, 2], [4, 2, 1], passes=3), expected_result * 3)
        # Check if the dimensions are correct for 3d, with steps size, multi passes.
        self.verify_result(AreaPositioner([0, 0, 0], [4, 2, 2], step_size=[1., 1., 2.], passes=3), expected_result * 3)

    def test_ZigZagAreaPositioner(self):
        self.standard_linear_tests(ZigZagAreaPositioner)
        # It is not a zigzag positioner in the classical sense. Between passes, it does not do zigzags.
        self.standard_linear_multipass_tests(ZigZagAreaPositioner)

        expected_result = [[0.0, 0.0], [0.0, 3.0],
                           [3.0, 3.0], [3.0, 0.0]]
        # Check if the area positioner advances axes by axes.
        self.verify_result(ZigZagAreaPositioner([0, 0], [3, 3], [1, 1]), expected_result)

        expected_result = [[0.0, 0.0], [0.0, 1.0], [0.0, 2.0], [0.0, 3.0], [0.0, 4.0],
                           [1.0, 4.0], [1.0, 3.0], [1.0, 2.0], [1.0, 1.0], [1.0, 0.0],
                           [2.0, 0.0], [2.0, 1.0], [2.0, 2.0], [2.0, 3.0], [2.0, 4.0],
                           [3.0, 4.0], [3.0, 3.0], [3.0, 2.0], [3.0, 1.0], [3.0, 0.0]]

        # Check if the dimensions are correct for 2d, with steps count.
        self.verify_result(ZigZagAreaPositioner([0, 0], [3, 4], [3, 4]), expected_result)
        # Check if the dimensions are correct for 2d, with steps size.
        self.verify_result(ZigZagAreaPositioner([0, 0], [3, 4], step_size=[1., 1.]), expected_result)

        # Check if the dimensions are correct for 2d, with steps count, multi passes
        self.verify_result(ZigZagAreaPositioner([0, 0], [3, 4], [3, 4], passes=3), expected_result * 3)
        # Check if the dimensions are correct for 2d, with steps size, multi passes
        self.verify_result(ZigZagAreaPositioner([0, 0], [3, 4], step_size=[1., 1.], passes=3), expected_result * 3)

        expected_result = [[0.0, 0.0, 0.0], [0.0, 0.0, 2.0], [0.0, 1.0, 2.0], [0.0, 1.0, 0.0], [0.0, 2.0, 0.0],
                           [0.0, 2.0, 2.0], [1.0, 2.0, 2.0], [1.0, 2.0, 0.0], [1.0, 1.0, 0.0], [1.0, 1.0, 2.0],
                           [1.0, 0.0, 2.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [2.0, 0.0, 2.0], [2.0, 1.0, 2.0],
                           [2.0, 1.0, 0.0], [2.0, 2.0, 0.0], [2.0, 2.0, 2.0], [3.0, 2.0, 2.0], [3.0, 2.0, 0.0],
                           [3.0, 1.0, 0.0], [3.0, 1.0, 2.0], [3.0, 0.0, 2.0], [3.0, 0.0, 0.0], [4.0, 0.0, 0.0],
                           [4.0, 0.0, 2.0], [4.0, 1.0, 2.0], [4.0, 1.0, 0.0], [4.0, 2.0, 0.0], [4.0, 2.0, 2.0]]

        # Check if the dimensions are correct for 3d, with steps count.
        self.verify_result(ZigZagAreaPositioner([0, 0, 0], [4, 2, 2], n_steps=[4, 2, 1]), expected_result)
        # Check if the dimensions are correct for 3d, with steps size.
        self.verify_result(ZigZagAreaPositioner([0, 0, 0], [4, 2, 2], step_size=[1., 1., 2.]), expected_result)

        # Check if the dimensions are correct for 3d, with steps count, multi passes.
        self.verify_result(ZigZagAreaPositioner([0, 0, 0], [4, 2, 2], [4, 2, 1], passes=3), expected_result * 3)
        # Check if the dimensions are correct for 3d, with steps size, multi passes.
        self.verify_result(ZigZagAreaPositioner([0, 0, 0], [4, 2, 2], step_size=[1., 1., 2.], passes=3),
                           expected_result * 3)

    def test_MultiAreaPositioner(self):
        expected_result = [[[0.0, 0.0], [4, 4]], [[0.0, 0.0], [5.0, 5.0]], [[0.0, 0.0], [6.0, 6.0]],
                           [[1.0, 1.0], [4, 4]], [[1.0, 1.0], [5.0, 5.0]], [[1.0, 1.0], [6.0, 6.0]],
                           [[2.0, 2.0], [4, 4]], [[2.0, 2.0], [5.0, 5.0]], [[2.0, 2.0], [6.0, 6.0]]]

        # Single pass, number of steps, 2 values per axis.
        self.verify_multi_result(MultiAreaPositioner([[0, 0], [4, 4]], [[2, 2], [6, 6]], [[2, 2], [2, 2]]),
                                 expected_result)
        # # Multi pass, number of steps.
        self.verify_multi_result(MultiAreaPositioner([[0, 0], [4, 4]], [[2, 2], [6, 6]], [[2, 2], [2, 2]], passes=3),
                                 expected_result * 3)

        # Single pass, step size, 2 values per axis.
        self.verify_multi_result(MultiAreaPositioner([[0, 0], [4, 4]], [[2, 2], [6, 6]], [[1., 1.], [1., 1.]]),
                                 expected_result)
        # # Multi pass, step size, 2 values per axis.
        self.verify_multi_result(MultiAreaPositioner([[0, 0], [4, 4]], [[2, 2], [6, 6]], [[1., 1.], [1., 1.]],
                                                     passes=3), expected_result * 3)

    def test_SerialPositioner(self):
        expected_result = [[0], [1], [2], [3], [4]]

        # This should simply scan over all the values.
        self.verify_result(SerialPositioner([0, 1, 2, 3, 4], [-1]), expected_result)

        expected_result = [[0, -1], [1, -1], [2, -1],
                           [-1, 0], [-1, 1]]
        # One axis at the time, returning each value back to the original when finished.
        self.verify_result(SerialPositioner([[0, 1, 2], [0, 1]], [-1, -1]),
                           expected_result)

        expected_result = [[0, -1, -1], [1, -1, -1],
                           [-1, 0, -1], [-1, 1, -1],
                           [-1, -1, 0], [-1, -1, 1]]
        # Same as above, but for 3 axis.
        self.verify_result(SerialPositioner([[0, 1], [0, 1], [0, 1]], [-1, -1, -1]),
                           expected_result)

        # Test for PyScan.
        expected_result = [[-3, -12], [-2, -12], [-1, -12], [0, -12],
                           [-11, -3], [-11, -2], [-11, -1], [-11, 0]]

        first_initial = [-11, -12]
        first_input = [[-3, -2, -1, 0], [-3, -2, -1, 0]]

        self.verify_result(SerialPositioner(first_input, first_initial), expected_result)

        expected_result = [[0, -22], [1, -22], [2, -22],
                           [-21, 0], [-21, 1], [-21, 2]]

        second_initial = [-21, -22]
        second_input = [[0, 1, 2], [0, 1, 2]]

        self.verify_result(SerialPositioner(second_input, second_initial), expected_result)

    def test_CompoundPositioner(self):
        expected_result = [[0], [1], [2], [3]]
        # The compound positioner should not modify the behaviour if only 1 positioner was supplied.
        self.verify_result(CompoundPositioner([SerialPositioner([0, 1, 2, 3], [-1])]), expected_result)

        expected_result = [[0.0, 0.0], [0.0, 3.0],
                           [3.0, 3.0], [3.0, 0.0]]
        # Test with other positioners as well.
        self.verify_result(CompoundPositioner([ZigZagAreaPositioner([0, 0], [3, 3], [1, 1])]), expected_result)

        self.verify_result(CompoundPositioner([VectorPositioner(expected_result, passes=3)]), expected_result * 3)

        # Perform tests for PyScan.
        first_input = [[-3, -2, -1, 0], [-3, -2, -1, 0]]
        second_input = [[0, 1, 2], [0, 1, 2]]
        # Transform the list to be position by position, not axis by axis.
        first_input = convert_to_position_list(first_input)
        second_input = convert_to_position_list(second_input)

        # 2 ScanLine axes.
        expected_result = [[-3, -3, 0, 0], [-3, -3, 1, 1], [-3, -3, 2, 2],
                           [-2, -2, 0, 0], [-2, -2, 1, 1], [-2, -2, 2, 2],
                           [-1, -1, 0, 0], [-1, -1, 1, 1], [-1, -1, 2, 2],
                           [-0, -0, 0, 0], [-0, -0, 1, 1], [-0, -0, 2, 2]]

        self.verify_result(CompoundPositioner([VectorPositioner(first_input),
                                               VectorPositioner(second_input)]), expected_result)

        # 2 ScanSeries axes.
        expected_result = [[-3, -12, 0, -22], [-3, -12, 1, -22], [-3, -12, 2, -22],
                           [-3, -12, -21, 0], [-3, -12, -21, 1], [-3, -12, -21, 2],
                           [-2, -12, 0, -22], [-2, -12, 1, -22], [-2, -12, 2, -22],
                           [-2, -12, -21, 0], [-2, -12, -21, 1], [-2, -12, -21, 2],
                           [-1, -12, 0, -22], [-1, -12, 1, -22], [-1, -12, 2, -22],
                           [-1, -12, -21, 0], [-1, -12, -21, 1], [-1, -12, -21, 2],
                           [-0, -12, 0, -22], [-0, -12, 1, -22], [-0, -12, 2, -22],
                           [-0, -12, -21, 0], [-0, -12, -21, 1], [-0, -12, -21, 2],
                           [-11, -3, 0, -22], [-11, -3, 1, -22], [-11, -3, 2, -22],
                           [-11, -3, -21, 0], [-11, -3, -21, 1], [-11, -3, -21, 2],
                           [-11, -2, 0, -22], [-11, -2, 1, -22], [-11, -2, 2, -22],
                           [-11, -2, -21, 0], [-11, -2, -21, 1], [-11, -2, -21, 2],
                           [-11, -1, 0, -22], [-11, -1, 1, -22], [-11, -1, 2, -22],
                           [-11, -1, -21, 0], [-11, -1, -21, 1], [-11, -1, -21, 2],
                           [-11, -0, 0, -22], [-11, -0, 1, -22], [-11, -0, 2, -22],
                           [-11, -0, -21, 0], [-11, -0, -21, 1], [-11, -0, -21, 2]]

        # Initial positions to be used.
        first_input = [[-3, -2, -1, 0], [-3, -2, -1, 0]]
        second_input = [[0, 1, 2], [0, 1, 2]]
        first_initial = [-11, -12]
        second_initial = [-21, -22]

        self.verify_result(CompoundPositioner([SerialPositioner(first_input, first_initial),
                                               SerialPositioner(second_input, second_initial)]),
                           expected_result)

        # First dimension LineScan, second dimension first change one, than another.
        expected_result = [[-3, -3, 0, -22], [-3, -3, 1, -22], [-3, -3, 2, -22],
                           [-3, -3, -21, 0], [-3, -3, -21, 1], [-3, -3, -21, 2],
                           [-2, -2, 0, -22], [-2, -2, 1, -22], [-2, -2, 2, -22],
                           [-2, -2, -21, 0], [-2, -2, -21, 1], [-2, -2, -21, 2],
                           [-1, -1, 0, -22], [-1, -1, 1, -22], [-1, -1, 2, -22],
                           [-1, -1, -21, 0], [-1, -1, -21, 1], [-1, -1, -21, 2],
                           [-0, -0, 0, -22], [-0, -0, 1, -22], [-0, -0, 2, -22],
                           [-0, -0, -21, 0], [-0, -0, -21, 1], [-0, -0, -21, 2]]

        first_input = convert_to_position_list([[-3, -2, -1, 0], [-3, -2, -1, 0]])

        self.verify_result(CompoundPositioner([VectorPositioner(first_input),
                                               SerialPositioner(second_input, second_initial)]),
                           expected_result)
