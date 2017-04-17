import unittest

from pyscan.interface.pyScan import Scan
from tests.utils import TestPyScanDal


class PyScan(unittest.TestCase):

    def test_initializeScan(self):
        indict1 = dict()
        indict1['Knob'] = ["1.1", "1.2"]
        indict1['ScanRange'] = [[-2, 0], [-2, 0]]
        indict1['Nstep'] = 3
        indict1['Observable'] = ["READ1", "READ2"]
        indict1['Waiting'] = 0.1

        indict2 = dict()
        indict2['Knob'] = ["2.1", "2.2"]
        indict2['ScanRange'] = [[0, 2], [0, 2]]
        indict2['Nstep'] = 3
        indict2['Observable'] = ["READ3", "READ4"]
        indict2['Waiting'] = 0.1

        testDal = TestPyScanDal()
        pyscan = Scan()
        pyscan.initializeScan([indict1, indict2], testDal)
        result = pyscan.startScan()

        expected_positions = [[-2, -2, 0, 0], [-2, -2, 1, 1], [-2, -2, 2, 2],
                              [-1, -1, 0, 0], [-1, -1, 1, 1], [-1, -1, 2, 2],
                              [-0, -0, 0, 0], [-0, -0, 1, 1], [-0, -0, 2, 2]]

        # First 4 PVs are readbacks, the first read is NULL.
        sampled_positions = [single_position[:4] for single_position in testDal.positions[1:]]
        self.assertEqual(sampled_positions, expected_positions)