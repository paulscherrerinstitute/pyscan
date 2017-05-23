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

        readables = epics_pv("PYSCAN:TEST:OBS1")
        result = tscan(readables, points=points, interval=acquisition_interval)

        self.assertEqual(len(result), points, "Number of received points does not math the requirement.")

