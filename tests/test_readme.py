import unittest


class Readme(unittest.TestCase):

    def compare_results(self, results, expected_result):
        for result in results:
            positions = list(result.get_generator())
            self.assertEqual(expected_result, positions, "The result does not match the expected result.")

    def test_VectorAndLinePositioner(self):
        # Dummy value initialization.
        x1, x2, x3, x4 = range(1, 5)
        y1, y2, y3, y4 = range(1, 5)

        from pyscan.positioner.vector import VectorPositioner
        from pyscan.positioner.line import LinePositioner

        # Move to positions x1,y1; then x2,y2; x3,y3; x4,y4.
        vector_positioner = VectorPositioner(positions=[[x1, y1], [x2, y2], [x3, y3], [x4, y4]])

        # Start at positions x1,y1; end at positions x4,y4; make 3 steps to reach the end.
        line_positioner_n_steps = LinePositioner(start=[x1, y1], end=[x4, y4], n_steps=3)

        # Start at position x1,y1; end at position x4,y4: make steps of size x2-x1 for x axis and y2-y1 for y axis.
        line_positioner_step_size = LinePositioner(start=[x1, y1], end=[x4, y4], step_size=[x2 - x1, y2 - y1])

        self.compare_results(results=[vector_positioner, line_positioner_n_steps, line_positioner_step_size],
                             expected_result=[[1, 1], [2, 2], [3, 3], [4, 4]])

    def test_AreaPositioner(self):
        x1, x2, x3, x4 = range(1, 5)
        y1, y2, y3, y4 = range(1, 5)

        from pyscan.positioner.area import AreaPositioner

        area_positioner_n_steps = AreaPositioner(start=[x1, y1], end=[x4, y4], n_steps=[3, 3])
        area_positioner_step_size = AreaPositioner(start=[x1, y1], end=[x4, y4], step_size=[x2 - x1, y2 - y1])

        self.compare_results(results=[area_positioner_n_steps, area_positioner_step_size],
                             expected_result=[[1, 1], [1, 2], [1, 3], [1, 4], 
                                              [2, 1], [2, 2], [2, 3], [2, 4], 
                                              [3, 1], [3, 2], [3, 3], [3, 4], 
                                              [4, 1], [4, 2], [4, 3], [4, 4]])
