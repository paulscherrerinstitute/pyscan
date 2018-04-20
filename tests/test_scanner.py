import threading
import unittest

import sys

from pyscan import *
from tests.helpers.mock_epics_dal import MockReadGroupInterface, MockWriteGroupInterface, cached_initial_values
from tests.helpers.utils import TestWriter, TestReader

test_positions = [0, 1, 2, 3, 4, 5]

# BEGIN EPICS MOCK.

scan_module = sys.modules["pyscan.scan"]
utils_module = sys.modules["pyscan.scan_actions"]

utils_module.EPICS_READER = MockReadGroupInterface
utils_module.EPICS_WRITER = MockWriteGroupInterface
scan_module.EPICS_READER = MockReadGroupInterface
scan_module.EPICS_WRITER = MockWriteGroupInterface

# Setup mock values
cached_initial_values["PYSCAN:TEST:OBS1"] = 1

# END OF MOCK.


class ScannerTests(unittest.TestCase):

    def test_ScannerBasics(self):

        positioner = VectorPositioner(test_positions)

        target_positions = []
        writer = TestWriter(target_positions).write

        data_processor = SimpleDataProcessor()

        read_buffer = [0, 11, 22, 33, 44, 55]
        reader = TestReader(read_buffer).read

        scanner = Scanner(positioner, data_processor, reader, writer)
        scanner.discrete_scan()

        self.assertEqual(target_positions, test_positions,
                         "The output positions are not equal to the input positions.")

        self.assertEqual(read_buffer, data_processor.get_data(),
                         "The provided and received data is not the same.")

        self.assertEqual(test_positions, data_processor.positions,
                         "The provided and sampled positions are not the same.")

    def test_status(self):
        positioner = StaticPositioner(5)
        readables = "PYSCAN:TEST:OBS1"
        settings = scan_settings(settling_time=0.05)

        scanner_instance = scanner(positioner=positioner, readables=readables, settings=settings)
        self.assertEqual(scanner_instance.get_status(), STATUS_INITIALIZED, "Status is not initialized.")
        scanner_instance.pause_scan()
        self.assertEqual(scanner_instance.get_status(), STATUS_INITIALIZED, "Pause before start should work.")

        def verify():
            sleep(0.1)
            self.assertEqual(scanner_instance.get_status(), STATUS_PAUSED, "Scan pause not detected by status.")
            scanner_instance.resume_scan()
            sleep(0.1)
            self.assertEqual(scanner_instance.get_status(), STATUS_RUNNING, "Resume status not correct.")

        threading.Thread(target=verify).start()
        scanner_instance.discrete_scan()
        self.assertEqual(scanner_instance.get_status(), STATUS_FINISHED, "Finished status not correct.")

        scanner_instance.abort_scan()
        self.assertRaisesRegex(Exception, "User aborted scan.", scanner_instance.discrete_scan)
        self.assertEqual(scanner_instance.get_status(), STATUS_ABORTED)

    def test_bsread_positioner_multi_measurements(self):

        with self.assertRaisesRegex(ValueError, "When using BsreadPositioner the maximum number of n_measurements = 1"):
            scanner(readables=[epics_pv("something")],
                    positioner=BsreadPositioner(10),
                    settings=scan_settings(n_measurements=2))
