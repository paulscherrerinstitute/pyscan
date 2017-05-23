import unittest


import sys
from tests.helpers.mock_epics_dal import MockReadGroupInterface, MockWriteGroupInterface, cached_initial_values, \
    pv_cache

# BEGIN EPICS MOCK.

scan_module = sys.modules["pyscan.scan"]
utils_module = sys.modules["pyscan.scan_actions"]

utils_module.EPICS_READER = MockReadGroupInterface
utils_module.EPICS_WRITER = MockWriteGroupInterface
scan_module.EPICS_READER = MockReadGroupInterface
scan_module.EPICS_WRITER = MockWriteGroupInterface

# Setup mock values
cached_initial_values["PYSCAN:TEST:VALID1"] = 10
cached_initial_values["PYSCAN:TEST:OBS1"] = 1

cached_initial_values["PYSCAN:TEST:MOTOR1:GET"] = -10
cached_initial_values["PYSCAN:TEST:MOTOR1:SET"] = -10
cached_initial_values["PYSCAN:TEST:MOTOR2:GET"] = -20
cached_initial_values["PYSCAN:TEST:MOTOR2:SET"] = -20

# END OF MOCK.

from pyscan import epics_pv
from pyscan.interface.pshell import tscan, lscan


class PShell(unittest.TestCase):
    def test_lscan(self):
        writables = [epics_pv("PYSCAN:TEST:MOTOR1:SET", "PYSCAN:TEST:MOTOR1:GET"),
                     epics_pv("PYSCAN:TEST:MOTOR2:SET", "PYSCAN:TEST:MOTOR2:GET")]

        readables = [epics_pv("PYSCAN:TEST:OBS1")]

        start = [0, 0]
        end = [2, 6]
        steps = 2

        # Collect motor positions after each measurement.
        def after_read():
            motor_positions.append((pv_cache["PYSCAN:TEST:MOTOR1:SET"][0].value,
                                    pv_cache["PYSCAN:TEST:MOTOR2:SET"][0].value))
        motor_positions = []

        result = lscan(writables=writables, readables=readables, start=start, end=end, steps=steps, relative=True,
                       after_read=after_read)

        self.assertEqual(len(result), steps + 1, "The result length does not match the number of steps.")

        self.assertEqual((pv_cache["PYSCAN:TEST:MOTOR1:SET"][0].value,
                          pv_cache["PYSCAN:TEST:MOTOR2:SET"][0].value), (-10, -20),
                         "Initial motor positions not restored.")

        self.assertEqual(motor_positions, [(-10, -20), (-9, -17), (-8, -14)],
                         "Motor did not move on relative positions.")

    def test_tscan(self):
        points = 5
        acquisition_interval = 0.1

        def increase_before():
            nonlocal before_counter
            before_counter += 1
        before_counter = 0

        def increase_after():
            nonlocal after_counter
            after_counter += 1
        after_counter = 0

        readables = epics_pv("PYSCAN:TEST:OBS1")
        result = tscan(readables, points=points, interval=acquisition_interval,
                       before_read=increase_before, after_read=increase_after)

        self.assertEqual(len(result), points, "Number of received points does not math the requirement.")
        self.assertEqual(points, before_counter, "The number of before_read invocation does not match.")
        self.assertEqual(points, after_counter, "The number of after_read invocation does not match.")
