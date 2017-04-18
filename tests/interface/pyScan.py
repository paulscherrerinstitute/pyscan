import unittest

from pyscan.interface.pyScan import Scan
from tests.utils import TestPyScanDal


class PyScan(unittest.TestCase):

    @staticmethod
    def get_ScanRange_indices():
        indict1 = dict()
        indict1['Knob'] = ["1.1", "1.2"]
        indict1["ScanValues"] = [[-3, -2, -1, 0], [-3, -2, -1, 0]]
        indict1['Observable'] = ["READ1", "READ2", "READ3"]
        indict1['Waiting'] = 0.1

        indict2 = dict()
        indict2['Knob'] = ["2.1", "2.2"]
        indict2['ScanRange'] = [[0, 2], [0, 2]]
        indict2['Nstep'] = 3
        indict2['Observable'] = ["READ4", "READ5"]
        indict2['Waiting'] = 0.1
        return indict1, indict2

    @staticmethod
    def get_ScanSeries_indices():
        indict1 = dict()
        indict1['Knob'] = ["1.1", "1.2"]
        indict1["ScanValues"] = [[-3, -2, -1, 0], [-3, -2, -1, 0]]
        indict1['Series'] = 1
        indict1['Observable'] = ["READ1", "READ2", "READ3"]
        indict1['Waiting'] = 0.1

        indict2 = dict()
        indict2['Knob'] = ["2.1", "2.2"]
        indict2["ScanValues"] = [[0, 1, 2], [0, 1, 2]]
        indict2['Series'] = 1
        indict2['Observable'] = ["READ4", "READ5"]
        indict2['Waiting'] = 0.1
        return indict1, indict2

    @staticmethod
    def get_ScanValues_indices():
        pass

    def test_ScanRange(self):
        indict1, indict2 = self.get_ScanRange_indices()
        # Only the number of measurements on the last dimension can influence the result.
        indict1["NumberOfMeasurements"] = 3

        test_dal = TestPyScanDal()
        pyscan = Scan()
        result = pyscan.initializeScan([indict1, indict2], test_dal)

        self.assertEqual(result["ErrorMessage"], None, "Initialization failed.")

        result = pyscan.startScan()

        self.assertEqual(result["ErrorMessage"], "Measurement finalized (finished/aborted) normally. "
                                                 "Need initialisation before next measurement.",
                         "Scan failed.")

        # Check if the results object has all the needed parameters.
        expected_elements = ["TimeStampStart", "KnobReadback", "Observable",
                             "TimeStampEnd", "Validation", "ErrorMessage"]
        self.assertEqual(set(expected_elements), set(result), "Expected elements missing in result.")

        # Test timestamps.
        self.assertTrue(result["TimeStampEnd"] > result["TimeStampStart"],
                        "The end timestamp is smaller than the start timestamp.")

        # Test ErrorMessage (when everything is ok)
        self.assertEqual(result["ErrorMessage"], 'Measurement finalized (finished/aborted) normally. '
                                                 'Need initialisation before next measurement.',
                         "The expected error message is missing.")

        expected_positions = [[-3, -3, 0, 0], [-3, -3, 1, 1], [-3, -3, 2, 2],
                              [-2, -2, 0, 0], [-2, -2, 1, 1], [-2, -2, 2, 2],
                              [-1, -1, 0, 0], [-1, -1, 1, 1], [-1, -1, 2, 2],
                              [-0, -0, 0, 0], [-0, -0, 1, 1], [-0, -0, 2, 2]]

        # The first element of the result must be the initial PV values.
        original_values = test_dal.positions[0]
        self.assertEqual(original_values, indict1["Knob"] + indict2["Knob"] + indict2["Observable"],
                         "The first element of the read positions should be the initial condition.")

        # First 4 PVs are readbacks, the first array entry is the original values before changing them for measuring.
        sampled_positions = [single_position[:4] for single_position in test_dal.positions[1:]]
        self.assertEqual(sampled_positions, expected_positions,
                         "The expected positions do not match the one read by the mock dal.")

        knob_readbacks = result["KnobReadback"]

        # The slow dimension is always the slowest to change.
        self.assertEqual(len(knob_readbacks), indict1['Nstep'],
                         "The number of steps do not match with the first dimension.")
        self.assertEqual(len(knob_readbacks[0]), indict2["Nstep"],
                         "The number of steps do not match with the second dimension.")

        # Flatten the list.
        knob_readbacks_expanded = [knob for sublist in knob_readbacks for knob in sublist]

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

        # TODO: Test result["Validation"] -> why is it even empty?

    def test_ScanRange_multi_measurments(self):
        indict1, indict2 = self.get_ScanRange_indices()
        # Each measurement (KnobReadback, Observable, Validation) is repeated 4 times.
        indict2["NumberOfMeasurements"] = 4
        # This should not change anything - and we are testing this.
        indict1["NumberOfMeasurements"] = 5

        test_dal = TestPyScanDal()
        pyscan = Scan()
        result = pyscan.initializeScan([indict1, indict2], test_dal)

        self.assertEqual(result["ErrorMessage"], None, "Initialization failed.")

        result = pyscan.startScan()

        self.assertEqual(result["ErrorMessage"], "Measurement finalized (finished/aborted) normally. "
                                                 "Need initialisation before next measurement.",
                         "Scan failed.")

        # The first element of the result must be the initial PV values.
        original_values = test_dal.positions[0]
        self.assertEqual(original_values, indict1["Knob"] + indict2["Knob"] + indict2["Observable"],
                         "The first element of the read positions should be the initial condition.")

        knob_readbacks = result["KnobReadback"]

        self.assertEqual(len(knob_readbacks), indict1['Nstep'],
                         "The number of steps do not match with the first dimension.")
        self.assertEqual(len(knob_readbacks[0]), indict2["Nstep"],
                         "The number of steps do not match with the second dimension.")
        self.assertEqual(len(knob_readbacks[0][0]), indict2["NumberOfMeasurements"],
                         "The number of measurements do not match with the second dimension NumberOfMeasurements.")

        observables = result["Observable"]

        self.assertEqual(len(observables), indict1['Nstep'],
                         "The number of steps do not match with the first dimension.")
        # Only observables from the last dimension are taken into account.
        self.assertEqual(len(observables[0]), indict2['Nstep'],
                         "The number of steps do not match with the second dimension.")
        # Check if only observables from the last dimension were read.
        self.assertEqual(observables[0][0], [indict2['Observable']] * indict2["NumberOfMeasurements"],
                         "Not the correct number of observables was read.")

        # TODO: Test result["Validation"] -> why is it even empty?

    def test_ScanSeries(self):
        indict1, indict2 = self.get_ScanSeries_indices()

        test_dal = TestPyScanDal()
        pyscan = Scan()
        result = pyscan.initializeScan([indict1], test_dal)

        self.assertEqual(result["ErrorMessage"], None, "Initialization failed.")

        result = pyscan.startScan()

        self.assertEqual(result["ErrorMessage"], "Measurement finalized (finished/aborted) normally. "
                                                 "Need initialisation before next measurement.",
                         "Scan failed.")


    # TODO: Test PreAction and PostAction.
    # TODO: Test In-loopPreAction, In-loopPostAction
    # TODO: Test Monitor.
    # TODO: Test additive - Does that mean relative? YES!
