import unittest

from pyscan.positioner import LinearDiscreetPositioner, ZigZagLinearDiscreetPositioner


class DiscreetPositionersTests(unittest.TestCase):
    @staticmethod
    def is_close(list1, list2, epsilon=0.00001):
        return all((value1 - value2) < epsilon for value1, value2 in zip(list1, list2))

    def verify_result(self, positioner, expected_result):
        positions = list(positioner.next_position())
        self.assertEqual(len(positions), len(expected_result),
                         "The number of positions does not match "
                         "the expected one.\n"
                         "Received: %s\nExpected: %s." % (positions, expected_result))

        for i, position in enumerate(positions):
            self.assertTrue(self.is_close(position, expected_result[i]),
                            "The elements in position %d do not match the expected result.\n"
                            "Received: %s\nExpected: %s." % (i, positions, expected_result))

    def test_LinearDiscreetPositioner(self):
        expected_result = [[-2.], [-1.], [0.], [1.], [2.]]

        # Generate 5 steps, from -2 to 2, using number of steps.
        self.verify_result(LinearDiscreetPositioner([-2], [2], [4]), expected_result)
        # Generate 10 steps, 2 passes, using number of steps.
        self.verify_result(LinearDiscreetPositioner([-2], [2], [4], passes=2), expected_result * 2)

        # Generate 5 steps, from -2 to 2, using step size.
        self.verify_result(LinearDiscreetPositioner([-2], [2], [1.]), expected_result)
        # Generate 10 steps, 2 passes, using step size.
        self.verify_result(LinearDiscreetPositioner([-2], [2], [1.], passes=2), expected_result * 2)

        # Generate 5 steps, from -2 to 2, using number of steps, with offset.
        self.verify_result(LinearDiscreetPositioner([-4], [0], [4], offsets=[2]), expected_result)
        # Generate 10 steps, 2 passes, using number of steps.
        self.verify_result(LinearDiscreetPositioner([-4], [0], [4], passes=2, offsets=[2]), expected_result * 2)

        # Generate 5 steps, from -2 to 2, using step size, with offset.
        self.verify_result(LinearDiscreetPositioner([-4], [0], [1.], offsets=[2]), expected_result)
        # Generate 10 steps, 2 passes, using step size, with offset.
        self.verify_result(LinearDiscreetPositioner([-4], [0], [1.], passes=2, offsets=[2]), expected_result * 2)

        expected_result = [[-2.], [-0.8], [0.4], [1.6]]
        # Generate 4 steps, from -2 to 2, using step size 1.2
        self.verify_result(LinearDiscreetPositioner([-2], [2], [1.2]), expected_result)

        expected_result = [[2.], [1.], [0.], [-1.], [-2.]]

        # Generate 4 steps, from 2 to -2, using number of steps.
        self.verify_result(LinearDiscreetPositioner([2], [-2], [4]), expected_result)

        expected_result = [[2], [0.8], [-0.4], [-1.6]]

        # Generate 4 steps, from 2 to -2, using step size -1.2
        self.verify_result(LinearDiscreetPositioner([2], [-2], [-1.2]), expected_result)

    def test_LinearDiscreetPositioner_exceptions(self):
        # TODO: Implement tests for input validation.
        # Negative number of steps.
        # Right to left, with positive step size
        # Left to right, with negative step size
        # Different number of steps for each axis.
        # Different step size for same interval in more axes.
        # Steps is not a float or an integer.
        pass

    def test_ZigZagLinearDiscreetPositioner(self):
        expected_single_result = [[-2.], [-1.], [0.], [1.], [2.]]
        expected_3pass_result = [[-2.], [-1.], [0.], [1.], [2.], [1.], [0.], [-1.], [-2.], [-1.], [0.], [1.], [2.]]

        # Test if with 1 pass, still behaves like a normal LinearDiscreetPositioner.
        self.verify_result(ZigZagLinearDiscreetPositioner([-2], [2], [4], passes=1), expected_single_result)

        # Test if with 3 passes, it omits the duplicate positions.
        self.verify_result(ZigZagLinearDiscreetPositioner([-2], [2], [4], passes=3), expected_3pass_result)

        expected_single_result = [[-2.], [-0.8], [0.4], [1.6]]
        expected_3pass_result = [[-2.], [-0.8], [0.4], [1.6], [0.4], [-0.8], [-2.], [-0.8], [0.4], [1.6]]

        # Test what happens if the step size is not dividable by the interval.
        self.verify_result(ZigZagLinearDiscreetPositioner([-2], [2], [1.2], passes=1), expected_single_result)

        # Test what happens if the step size is not dividable by the interval, 3 passes.
        self.verify_result(ZigZagLinearDiscreetPositioner([-2], [2], [1.2], passes=3), expected_3pass_result)

        expected_3pass_result = [[2.], [0.8], [-0.4], [-1.6], [-0.4], [0.8], [2.], [0.8], [-0.4], [-1.6]]

        # Test what happens if the step size is not dividable by the interval, 3 passes, right to left.
        self.verify_result(ZigZagLinearDiscreetPositioner([2], [-2], [-1.2], passes=3), expected_3pass_result)

    def test_ZigZagLinearDiscreetPositioner_exceptions(self):
        # TODO: Implement tests for input validation.
        pass
