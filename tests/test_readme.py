import unittest
from itertools import cycle

import sys

# BEGIN EPICS MOCK.
from tests.helpers.mock_epics_dal import MockReadGroupInterface, MockWriteGroupInterface, fixed_values

scan_module = sys.modules["pyscan.scan"]
utils_module = sys.modules["pyscan.scan_actions"]

utils_module.EPICS_READER = MockReadGroupInterface
utils_module.EPICS_WRITER = MockWriteGroupInterface
scan_module.EPICS_READER = MockReadGroupInterface
scan_module.EPICS_WRITER = MockWriteGroupInterface

fixed_values["X"] = cycle([1])
fixed_values["Y"] = cycle([2])
fixed_values["Z"] = cycle([3])
# END OF MOCK.

from pyscan import *


class Readme(unittest.TestCase):
    def compare_results(self, results, expected_result):
        for result in results:
            positions = list(result.get_generator())
            self.assertEqual(expected_result, positions, "The result does not match the expected result.")

    def test_VectorAndLinePositioner(self):
        # Dummy value initialization.
        x1, x2, x3, x4 = range(1, 5)
        y1, y2, y3, y4 = range(1, 5)

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

        area_positioner_n_steps = AreaPositioner(start=[x1, y1], end=[x4, y4], n_steps=[3, 3])
        area_positioner_step_size = AreaPositioner(start=[x1, y1], end=[x4, y4], step_size=[x2 - x1, y2 - y1])

        self.compare_results(results=[area_positioner_n_steps, area_positioner_step_size],
                             expected_result=[[1, 1], [1, 2], [1, 3], [1, 4],
                                              [2, 1], [2, 2], [2, 3], [2, 4],
                                              [3, 1], [3, 2], [3, 3], [3, 4],
                                              [4, 1], [4, 2], [4, 3], [4, 4]])

    def test_CompoundPositioner(self):
        x1, x2, x3, x4 = range(1, 5)
        y1, y2, y3, y4 = range(1, 5)

        line_positioner = VectorPositioner([x1, x2, x3, x4])
        column_positioner = VectorPositioner([y1, y2, y3, y4])

        area_positioner = CompoundPositioner([line_positioner, column_positioner])

        self.compare_results(results=[area_positioner],
                             expected_result=[[1, 1], [1, 2], [1, 3], [1, 4],
                                              [2, 1], [2, 2], [2, 3], [2, 4],
                                              [3, 1], [3, 2], [3, 3], [3, 4],
                                              [4, 1], [4, 2], [4, 3], [4, 4]])

    def test_ScanResult(self):
        # Dummy value initialization.
        x1, x2, x3 = [1] * 3
        y1, y2, y3 = [2] * 3
        z1, z2, z3 = [3] * 3

        # Scan at position 1, 2, and 3.
        positioner = VectorPositioner([1, 2, 3])
        # Define 1 writable motor
        writables = epics_pv("MOTOR")
        # Define 3 readables: X, Y, Z.
        readables = [epics_pv("X"), epics_pv("Y"), epics_pv("Z")]
        # Perform the scan.
        result = scan(positioner, writables, readables)

        # The result is a list, with a list of measurement for each position.
        self.assertEqual([[x1, y1, z1],
                          [x2, y2, z2],
                          [x3, y3, z3]], result, "The result is not the expected one.")

        # In case we want to do 2 measurements at each position.
        result = scan(positioner, writables, readables, settings=scan_settings(n_measurements=2))

        # The result is a list, with a list for each position, which again has a list for each measurement.
        self.assertEqual([[[x1, y1, z1], [x1, y1, z1]],
                          [[x2, y2, z2], [x2, y2, z2]],
                          [[x3, y3, z3], [x3, y3, z3]]], result, "The result is not the expected one.")

        # In case you have a single readable.
        readables = epics_pv("X")
        result = scan(positioner, writables, readables)

        # The measurements are still wrapped in a list (with a single element, this time).
        self.assertEqual([[x1], [x2], [x3]], result, "The result is not the expected one.")

        # Scan with only 1 position, 1 motor, 1 readable.
        positioner = VectorPositioner(1)
        writables = epics_pv("MOTOR")
        readables = epics_pv("X")
        result = scan(positioner, writables, readables)

        # The result is still wrapped in 2 lists. The reason is described in the note below.
        result == [[x1]]
