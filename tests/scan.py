import unittest

import time
from threading import Thread

from bsread.sender import Sender

from pyscan.positioner.vector import VectorPositioner
from pyscan.scan import scan
from pyscan.scan_parameters import epics_pv, bs_property, epics_monitor, bs_monitor, action_set_epics_pv, \
    action_restore, scan_settings

import pyscan.scan
from tests.mock_epics_dal import MockReadGroupInterface, MockWriteGroupInterface
# Mock the Epics DAL.
pyscan.scan.EPICS_READER = MockReadGroupInterface
pyscan.scan.EPICS_WRITER = MockWriteGroupInterface
# Setup mock values
from tests.mock_epics_dal import cached_initial_values
cached_initial_values["PYSCAN:TEST:VALID1"] = 10
cached_initial_values["PYSCAN:TEST:OBS1"] = 1


def start_sender():
    # Start a mock sender stream.
    generator = Sender()
    generator.add_channel('CAMERA1:X', lambda x: x, metadata={'type': 'int32'})
    generator.add_channel('CAMERA1:Y', lambda x: x, metadata={'type': 'int32'})
    generator.add_channel('CAMERA1:VALID', lambda x: 10, metadata={'type': 'int32'})

    generator.open()
    while True:
        generator.send()
        time.sleep(0.01)


class ScanTests(unittest.TestCase):

    def setUp(self):
        sender_thread = Thread(target=start_sender)
        sender_thread.daemon = True
        sender_thread.start()

    def test_monitors(self):
        # TODO: Test if the monitors belong to the same output as the values.
        pass

    def test_actions(self):
        # TODO: Test if the actions, especially the restore one, work as expected.
        pass

    def test_mixed_sources(self):
        positions = [1, 2, 3, 4]
        positioner = VectorPositioner(positions)

        writables = [epics_pv("PYSCAN:TEST:MOTOR1:SET", "PYSCAN:TEST:MOTOR1:GET"),
                     epics_pv("PYSCAN:TEST:MOTOR2:SET", "PYSCAN:TEST:MOTOR2:GET")]

        readables = [bs_property("CAMERA1:X"),
                     bs_property("CAMERA1:Y"),
                     epics_pv("PYSCAN:TEST:OBS1")]

        monitors = [epics_monitor("PYSCAN:TEST:VALID1", 10),
                    bs_monitor("CAMERA1:VALID", 10)]

        initialization = [action_set_epics_pv("PYSCAN:TEST:PRE1:SET", 1, "PYSCAN:TEST:PRE1:GET")]

        finalization = [action_set_epics_pv("PYSCAN:TEST:PRE1:SET", 0, "PYSCAN:TEST:PRE1:GET"),
                        action_restore()]

        result = scan(positioner=positioner,
                      writables=writables,
                      readables=readables,
                      monitors=monitors,
                      initializations=initialization,
                      finalization=finalization,
                      settings=scan_settings(measurement_interval=0.25,
                                             n_measurements=3))

        self.assertEqual(len(result), len(positions), "Not the expected number of results.")

        # The first 2 attributes are from bs_read, they should be equal to the pulse ID processed.
        self.assertTrue(all(x[0] == x[1] and x[2] == 1 for x in result), "The result is wrong.")
