import unittest

from pyscan.interface.pyScan import Scan
from tests.utils import TestPyScanDal


class PyScan(unittest.TestCase):

    def test_ScanRange(self):
        indict1 = dict()
        indict1['Knob'] = ["1.1", "1.2"]
        indict1['ScanRange'] = [[-3, 0], [-3, 0]]
        indict1['Nstep'] = 4
        indict1['Observable'] = ["READ1", "READ2", "READ3"]
        indict1['Waiting'] = 0.1

        indict2 = dict()
        indict2['Knob'] = ["2.1", "2.2"]
        indict2['ScanRange'] = [[0, 2], [0, 2]]
        indict2['Nstep'] = 3
        indict2['Observable'] = ["READ4", "READ5"]
        indict2['Waiting'] = 0.1

        testDal = TestPyScanDal()
        pyscan = Scan()
        pyscan.initializeScan([indict1, indict2], testDal)
        result = pyscan.startScan()

        expected_positions = [[-3, -3, 0, 0], [-3, -3, 1, 1], [-3, -3, 2, 2],
                              [-2, -2, 0, 0], [-2, -2, 1, 1], [-2, -2, 2, 2],
                              [-1, -1, 0, 0], [-1, -1, 1, 1], [-1, -1, 2, 2],
                              [-0, -0, 0, 0], [-0, -0, 1, 1], [-0, -0, 2, 2]]

        # First 4 PVs are readbacks, the first read is NULL.
        sampled_positions = [single_position[:4] for single_position in testDal.positions[1:]]
        self.assertEqual(sampled_positions, expected_positions,
                         "The expected positions do not match the one read by the mock dal.")

        knob_readbacks = result["KnobReadback"]

        # The slow dimension is always the slowest to change.
        self.assertEqual(len(knob_readbacks), indict1['Nstep'],
                         "The number of steps do not match with the first dimension.")
        self.assertEqual(len(knob_readbacks[0]), indict2["Nstep"],
                         "The number of steps do not match with the second dimension.")

        # TODO: When online, check if there is a merge method on lists.
        knob_readbacks_expanded = []
        for knobs in knob_readbacks:
            knob_readbacks_expanded.extend(knobs)

        # Check if the knob readbacks equal the expected positions (the motors were positioned to the correct values).
        self.assertEqual(knob_readbacks_expanded, expected_positions,
                         "The knob readback values do not match the expected one.")

        observables = result["Observable"]
        self.assertEqual(len(observables), indict1['Nstep'],
                         "The number of steps do not match with the first dimension.")
        # Only observables from the last dimension are taken into account.
        self.assertEqual(len(observables[0]), indict2['Nstep'],
                         "The number of steps do not match with the second dimension.")
        # Check if only observables from the last dimension were read.
        self.assertEqual(observables[0][0], indict2['Observable'], "The last dimension observables are not read.")


