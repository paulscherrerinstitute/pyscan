import unittest

from pyscan.positioner import VectorPositioner
from pyscan.scan import Scanner, SimpleDataProcessor
from tests.utils import TestWriter, TestReader

test_positions = [0, 1, 2, 3, 4, 5]


class ScannerTests(unittest.TestCase):

    def test_ScannerBasics(self):
        positioner = VectorPositioner(test_positions)

        target_positions = []
        writer = TestWriter(target_positions)

        read_buffer = [0, 11, 22, 33, 44, 55]
        reader = TestReader(read_buffer)

        data_processor = SimpleDataProcessor()

        scanner = Scanner(positioner, writer, data_processor, reader)
        scanner.discrete_scan()

        self.assertEqual(target_positions, test_positions,
                         "The output positions are not equal to the input positions.")

        self.assertEqual(read_buffer, [data for position, data in data_processor.get_data()],
                         "The provided and received data is not the same.")

        self.assertEqual(test_positions, [position for position, data in data_processor.get_data()],
                         "The provided and sampled positions are not the same.")
