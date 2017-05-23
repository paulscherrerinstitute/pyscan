import unittest


import sys

from pyscan import epics_pv
from tests.helpers.mock_epics_dal import MockReadGroupInterface, MockWriteGroupInterface, cached_initial_values

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

# END OF MOCK.

from pyscan.interface.pshell import tscan


class PShell(unittest.TestCase):
    def test_lscan(self):
        pass

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
