import unittest

from pyscan.positioner import LinearPositioner, ZigZagLinearPositioner, VectorPositioner, \
    ZigZagVectorPositioner, AreaPositioner, ZigZagAreaPositioner
from tests.utils import is_close


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

    def standard_linear_tests(self, positioner_type):
        """
        Collection of standard tests that every linear discreet positioner should pass.
        :param positioner_type: Class to test.
        """
        expected_result = [[-2.], [-1.], [0.], [1.], [2.]]

        # Generate 5 steps, from -2 to 2, using number of steps.
        self.verify_result(positioner_type([-2], [2], [4]), expected_result)

        # Generate 5 steps, from -2 to 2, using step size.
        self.verify_result(positioner_type([-2], [2], [1.]), expected_result)

        # Generate 5 steps, from -2 to 2, using number of steps, with offset.
        self.verify_result(positioner_type([-4], [0], [4], offsets=[2]), expected_result)

        # Generate 5 steps, from -2 to 2, using step size, with offset.
        self.verify_result(positioner_type([-4], [0], [1.], offsets=[2]), expected_result)

        expected_result = [[-2.], [-0.8], [0.4], [1.6]]

        # Generate 4 steps, from -2 to 2, using step size 1.2
        self.verify_result(positioner_type([-2], [2], [1.2]), expected_result)

        expected_result = [[2.], [1.], [0.], [-1.], [-2.]]

        # Generate 4 steps, from 2 to -2, using number of steps.
        self.verify_result(positioner_type([2], [-2], [4]), expected_result)

        expected_result = [[2], [0.8], [-0.4], [-1.6]]

        # Generate 4 steps, from 2 to -2, using step size -1.2
        self.verify_result(positioner_type([2], [-2], [-1.2]), expected_result)


    def standard_linear_multipass_tests(self, positioner_type):
        """
        Multipass tests that every linear discreet positioner should pass.
        :param positioner_type:  Class to test.
        """
        expected_result = [[-2.], [-1.], [0.], [1.], [2.]]

        # Generate 10 steps, 2 passes, using number of steps.
        self.verify_result(positioner_type([-2], [2], [4], passes=2), expected_result * 2)

        # Generate 10 steps, 2 passes, using step size.
        self.verify_result(positioner_type([-2], [2], [1.], passes=2), expected_result * 2)

        # Generate 10 steps, 2 passes, using step size, with offset.
        self.verify_result(positioner_type([-4], [0], [1.], passes=2, offsets=[2]), expected_result * 2)

    def standard_linear_multipass_zigzag_tests(self, positioner_type):
        """
        Zigzag multipass tests that every linear discreet positioner should pass.
        :param positioner_type:  Class to test.
        """
        expected_3pass_result = [[-2.], [-1.], [0.], [1.], [2.], [1.], [0.], [-1.], [-2.], [-1.], [0.], [1.], [2.]]

        # Test if with 3 passes, it omits the duplicate positions.
        self.verify_result(positioner_type([-2], [2], [4], passes=3), expected_3pass_result)

        expected_3pass_result = [[-2.], [-0.8], [0.4], [1.6], [0.4], [-0.8], [-2.], [-0.8], [0.4], [1.6]]

        # Test what happens if the step size is not dividable by the interval, 3 passes.
        self.verify_result(positioner_type([-2], [2], [1.2], passes=3), expected_3pass_result)

        expected_3pass_result = [[2.], [0.8], [-0.4], [-1.6], [-0.4], [0.8], [2.], [0.8], [-0.4], [-1.6]]

        # Test what happens if the step size is not dividable by the interval, 3 passes, right to left.
        self.verify_result(positioner_type([2], [-2], [-1.2], passes=3), expected_3pass_result)

    def test_LinearPositioner(self):
        self.standard_linear_tests(LinearPositioner)
        self.standard_linear_multipass_tests(LinearPositioner)

        expected_result = [[0, 0, 0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0]]

        # Generate 3d steps, with number of steps.
        self.verify_result(LinearPositioner([0, 0, 0], [2, 2, 2], [2, 2, 2]), expected_result)
        # Generate 3d steps, with step size
        self.verify_result(LinearPositioner([0, 0, 0], [2, 2, 2], [1., 1., 1.]), expected_result)

    def test_LinearPositioner_exceptions(self):
        # TODO: Implement tests for input validation.
        # Negative number of steps.
        # Right to left, with positive step size
        # Left to right, with negative step size
        # Different number of steps for each axis.
        # Different step size for same interval in more axes.
        # Steps is not a float or an integer.
        pass

    def test_ZigZagLinearPositioner(self):
        self.standard_linear_tests(ZigZagLinearPositioner)
        self.standard_linear_multipass_zigzag_tests(ZigZagLinearPositioner)

    def test_ZigZagLinearPositioner_exceptions(self):
        # TODO: Implement tests for input validation.
        pass

    def test_VectorPositioner(self):
        expected_result = [[-2., -2], [-1., -1], [0., 0], [1., 1], [2., 2]]

        # # Test 1 pass.
        self.verify_result(VectorPositioner(expected_result), expected_result)

        # Test 3 passes.
        self.verify_result(VectorPositioner(expected_result, passes=3), expected_result * 3)

        expected_result = [[0.0, -1], [1.0, 0], [2.0, 1], [3.0, 2], [4.0, 3]]

        # Test offset.
        self.verify_result(VectorPositioner(expected_result, offsets=[2, 1]), expected_result)

    def test_VectorPositioner_exceptions(self):
        # TODO: Test VectorPositioner validation.
        pass

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
        self.verify_result(AreaPositioner([0, 0], [3, 4], [3, 4]), expected_result)
        # Check if the dimensions are correct for 2d, with steps size.
        self.verify_result(AreaPositioner([0, 0], [3, 4], [1., 1.]), expected_result)

        # Check if the dimensions are correct for 2d, with steps count, multi passes
        self.verify_result(AreaPositioner([0, 0], [3, 4], [3, 4], passes=3), expected_result*3)
        # Check if the dimensions are correct for 2d, with steps size, multi passes
        self.verify_result(AreaPositioner([0, 0], [3, 4], [1., 1.], passes=3), expected_result*3)

        expected_result = [[0.0, 0, 0], [0.0, 0, 2.0], [0.0, 1.0, 0], [0.0, 1.0, 2.0], [0.0, 2.0, 0], [0.0, 2.0, 2.0],
                           [1.0, 0, 0], [1.0, 0, 2.0], [1.0, 1.0, 0], [1.0, 1.0, 2.0], [1.0, 2.0, 0], [1.0, 2.0, 2.0],
                           [2.0, 0, 0], [2.0, 0, 2.0], [2.0, 1.0, 0], [2.0, 1.0, 2.0], [2.0, 2.0, 0], [2.0, 2.0, 2.0],
                           [3.0, 0, 0], [3.0, 0, 2.0], [3.0, 1.0, 0], [3.0, 1.0, 2.0], [3.0, 2.0, 0], [3.0, 2.0, 2.0],
                           [4.0, 0, 0], [4.0, 0, 2.0], [4.0, 1.0, 0], [4.0, 1.0, 2.0], [4.0, 2.0, 0], [4.0, 2.0, 2.0]]

        # Check if the dimensions are correct for 3d, with steps count.
        self.verify_result(AreaPositioner([0, 0, 0], [4, 2, 2], [4, 2, 1]), expected_result)
        # Check if the dimensions are correct for 3d, with steps size.
        self.verify_result(AreaPositioner([0, 0, 0], [4, 2, 2], [1., 1., 2.]), expected_result)

        # Check if the dimensions are correct for 3d, with steps count, multi passes.
        self.verify_result(AreaPositioner([0, 0, 0], [4, 2, 2], [4, 2, 1], passes=3), expected_result * 3)
        # Check if the dimensions are correct for 3d, with steps size, multi passes.
        self.verify_result(AreaPositioner([0, 0, 0], [4, 2, 2], [1., 1., 2.], passes=3), expected_result * 3)

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
        self.verify_result(ZigZagAreaPositioner([0, 0], [3, 4], [1., 1.]), expected_result)

        # Check if the dimensions are correct for 2d, with steps count, multi passes
        self.verify_result(ZigZagAreaPositioner([0, 0], [3, 4], [3, 4], passes=3), expected_result * 3)
        # Check if the dimensions are correct for 2d, with steps size, multi passes
        self.verify_result(ZigZagAreaPositioner([0, 0], [3, 4], [1., 1.], passes=3), expected_result * 3)
        
        expected_result = [[0.0, 0.0, 0.0], [0.0, 0.0, 2.0], [0.0, 1.0, 2.0], [0.0, 1.0, 0.0], [0.0, 2.0, 0.0],
                           [0.0, 2.0, 2.0], [1.0, 2.0, 2.0], [1.0, 2.0, 0.0], [1.0, 1.0, 0.0], [1.0, 1.0, 2.0], 
                           [1.0, 0.0, 2.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [2.0, 0.0, 2.0], [2.0, 1.0, 2.0], 
                           [2.0, 1.0, 0.0], [2.0, 2.0, 0.0], [2.0, 2.0, 2.0], [3.0, 2.0, 2.0], [3.0, 2.0, 0.0], 
                           [3.0, 1.0, 0.0], [3.0, 1.0, 2.0], [3.0, 0.0, 2.0], [3.0, 0.0, 0.0], [4.0, 0.0, 0.0], 
                           [4.0, 0.0, 2.0], [4.0, 1.0, 2.0], [4.0, 1.0, 0.0], [4.0, 2.0, 0.0], [4.0, 2.0, 2.0]]

        # Check if the dimensions are correct for 3d, with steps count.
        self.verify_result(ZigZagAreaPositioner([0, 0, 0], [4, 2, 2], [4, 2, 1]), expected_result)
        # Check if the dimensions are correct for 3d, with steps size.
        self.verify_result(ZigZagAreaPositioner([0, 0, 0], [4, 2, 2], [1., 1., 2.]), expected_result)

        # Check if the dimensions are correct for 3d, with steps count, multi passes.
        self.verify_result(ZigZagAreaPositioner([0, 0, 0], [4, 2, 2], [4, 2, 1], passes=3), expected_result * 3)
        # Check if the dimensions are correct for 3d, with steps size, multi passes.
        self.verify_result(ZigZagAreaPositioner([0, 0, 0], [4, 2, 2], [1., 1., 2.], passes=3), expected_result * 3)

