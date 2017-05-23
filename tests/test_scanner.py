import unittest

from pyscan.positioner.vector import VectorPositioner
from pyscan.scanner import Scanner
from pyscan.utils import SimpleDataProcessor
from tests.helpers.utils import TestWriter, TestReader

test_positions = [0, 1, 2, 3, 4, 5]


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
