import unittest

from pyscan import epics_pv, StaticPositioner, scan, SimpleDataProcessor
from pyscan.utils import DictionaryDataProcessor

# BEGIN EPICS MOCK.
import sys
from tests.helpers.mock_epics_dal import MockReadGroupInterface, MockWriteGroupInterface, fixed_values

scan_module = sys.modules["pyscan.scan"]
utils_module = sys.modules["pyscan.scan_actions"]

utils_module.EPICS_READER = MockReadGroupInterface
utils_module.EPICS_WRITER = MockWriteGroupInterface
scan_module.EPICS_READER = MockReadGroupInterface
scan_module.EPICS_WRITER = MockWriteGroupInterface

# END OF MOCK.


class DataProcessorsTest(unittest.TestCase):

    def tearDown(self):
        if "PYSCAN:TEST:OBS1" in fixed_values:
            del fixed_values["PYSCAN:TEST:OBS1"]
        if "PYSCAN:TEST:OBS2" in fixed_values:
            del fixed_values["PYSCAN:TEST:OBS2"]
        if "PYSCAN:TEST:OBS3" in fixed_values:
            del fixed_values["PYSCAN:TEST:OBS3"]

    def test_DictionaryDataProcessor(self):
        n_images = 10
        positioner = StaticPositioner(n_images)
        readables = [epics_pv("PYSCAN:TEST:OBS1"),
                     epics_pv("PYSCAN:TEST:OBS2"),
                     epics_pv("PYSCAN:TEST:OBS3")]

        # Shift each OBS by 1, so we can resolve them when comparing results.
        fixed_values["PYSCAN:TEST:OBS1"] = iter(range(0, n_images))
        fixed_values["PYSCAN:TEST:OBS2"] = iter(range(1, n_images + 1))
        fixed_values["PYSCAN:TEST:OBS3"] = iter(range(2, n_images + 2))

        data_processor = DictionaryDataProcessor(readables)

        result = scan(positioner=positioner, readables=readables, data_processor=data_processor)

        for index in range(n_images):
            self.assertEqual(result[index]["PYSCAN:TEST:OBS1"], index, "Unexpected result for OBS1.")
            self.assertEqual(result[index]["PYSCAN:TEST:OBS2"], index+1, "Unexpected result for OBS2.")
            self.assertEqual(result[index]["PYSCAN:TEST:OBS3"], index+2, "Unexpected result for OBS3.")

    def test_data_and_position_references(self):
        n_images = 10
        positioner = StaticPositioner(n_images)
        readables = [epics_pv("PYSCAN:TEST:OBS1"),
                     epics_pv("PYSCAN:TEST:OBS2"),
                     epics_pv("PYSCAN:TEST:OBS3")]

        # Shift each OBS by 1, so we can resolve them when comparing results.
        fixed_values["PYSCAN:TEST:OBS1"] = iter(range(0, n_images))
        fixed_values["PYSCAN:TEST:OBS2"] = iter(range(1, n_images + 1))
        fixed_values["PYSCAN:TEST:OBS3"] = iter(range(2, n_images + 2))

        positions = []
        data = []
        data_processor = SimpleDataProcessor(positions, data)

        def after_read():
            nonlocal current_number_of_items
            self.assertEqual(len(positions), len(data), "The number of positions and data is out of sync.")
            self.assertEqual(len(data), current_number_of_items + 1, "More than 1 data point was taken.")
            current_number_of_items += 1
        current_number_of_items = 0

        scan(positioner=positioner, readables=readables, data_processor=data_processor, after_read=after_read)