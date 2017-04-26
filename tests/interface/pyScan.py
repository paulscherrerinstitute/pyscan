import json
import unittest

from tests.interface.old_scan import Scan as CurrentScan
from tests.interface.pyScan_test_data import test_output_format_expected_result
from tests.utils import TestPyScanDal


class PyScan(unittest.TestCase):
    @staticmethod
    def get_ScanLine_indices():
        indict1 = dict()
        indict1['Knob'] = ["1.1", "1.2"]
        indict1["ScanValues"] = [[-3, -2, -1, 0], [-3, -2, -1, 0]]
        indict1['Observable'] = ["READ1", "READ2", "READ3"]
        indict1['Waiting'] = 0.1

        indict2 = dict()
        # TODO: Check what happens if only a single Knob is specified.
        indict2['Knob'] = ["2.1", "2.2"]
        indict2['ScanRange'] = [[0, 2], [0, 2]]
        indict2['Nstep'] = 3
        # TODO: Check what happens if single value observable is given.
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

    def standard_init_tests(self, result):
        self.assertEqual(result["ErrorMessage"], None, "Initialization failed.")

    def standard_scan_tests(self, result, test_dal, indict1, indict2, expected_positions):
        # Check if the results object has all the needed parameters.
        expected_elements = ["TimeStampStart", "KnobReadback", "Observable",
                             "TimeStampEnd", "Validation", "ErrorMessage"]
        self.assertEqual(set(expected_elements), set(result), "Expected elements missing in result.")

        # Correct "ErrorMessage" when successfully completed.
        self.assertEqual(result["ErrorMessage"], "Measurement finalized (finished/aborted) normally. "
                                                 "Need initialisation before next measurement.",
                         "Scan failed.")

        # Test timestamps.
        self.assertTrue(result["TimeStampEnd"] > result["TimeStampStart"],
                        "The end timestamp is smaller than the start timestamp.")

        # The first element of the result must be the initial PV values.
        original_values = test_dal.positions[0]
        self.assertEqual(original_values, indict1["Knob"] + indict2["Knob"] + indict2["Observable"],
                         "The first element of the read positions should be the initial condition.")

        # Adjust the expected results to match the number of measurements on the last dimension.
        expanded_expected_positions = []
        n_measurements = indict2["NumberOfMeasurements"]
        if n_measurements > 1:
            for position in expected_positions:
                expanded_expected_positions.extend([position] * n_measurements)
        else:
            expanded_expected_positions = expected_positions

        # First 4 PVs are readbacks, the first array entry is the original values before changing them for measuring.
        sampled_positions = [single_position[:4] for single_position in test_dal.positions[1:]]
        self.assertEqual(sampled_positions, expanded_expected_positions,
                         "The expected positions do not match the one read by the mock dal.")

    def standard_line_tests(self, result, indict1, indict2, expected_positions):
        n_measurements = indict2["NumberOfMeasurements"]

        knob_readbacks = result["KnobReadback"]

        # Flatten the list.
        knob_readbacks_expanded = [knob for sublist in result["KnobReadback"] for knob in sublist]

        # Re-group the expanded expected positions by the number of measurements.
        if n_measurements > 1:
            for index, position in enumerate(expected_positions):
                expected_positions[index] = [position] * n_measurements

        # Check if the knob readbacks equal the expected positions (the motors were positioned to the correct values).
        self.assertEqual(knob_readbacks_expanded, expected_positions,
                         "The knob readback values do not match the expected one.")

        # The slow dimension is always the slowest to change.
        self.assertEqual(len(knob_readbacks), indict1['Nstep'],
                         "The number of knob_readbacks do not match with the first dimension steps.")
        self.assertEqual(len(knob_readbacks[0]), indict2["Nstep"],
                         "The number of knob_readbacks do not match with the second dimension steps.")

        observables = result["Observable"]
        self.assertEqual(len(observables), indict1['Nstep'],
                         "The number of observables do not match with the first dimension steps.")
        # Only observables from the last dimension are taken into account.
        self.assertEqual(len(observables[0]), indict2['Nstep'],
                         "The number of observables do not match with the second dimension steps.")

        # TODO: Test result["Validation"] -> why is it even empty?

        # Check if the number of measurements is correct for the results.
        if n_measurements > 1:
            self.assertEqual(len(knob_readbacks[0][0]), n_measurements,
                             "The number of measurements do not match with the second dimension NumberOfMeasurements.")

            # Check if only observables from the last dimension were read.
            self.assertEqual(observables[0][0], [indict2['Observable']] * n_measurements,
                             "The last dimension observables are not read.")

        else:
            # Check if only observables from the last dimension were read.
            self.assertEqual(observables[0][0], indict2['Observable'],
                             "The last dimension observables are not read.")

    def test_ScanLine(self):
        indict1, indict2 = self.get_ScanLine_indices()
        # Only the number of measurements on the last dimension can influence the result.
        indict1["NumberOfMeasurements"] = 3

        test_dal = TestPyScanDal()
        pyscan = CurrentScan()
        self.standard_init_tests(pyscan.initializeScan([indict1, indict2], test_dal))

        expected_positions = [[-3, -3, 0, 0], [-3, -3, 1, 1], [-3, -3, 2, 2],
                              [-2, -2, 0, 0], [-2, -2, 1, 1], [-2, -2, 2, 2],
                              [-1, -1, 0, 0], [-1, -1, 1, 1], [-1, -1, 2, 2],
                              [-0, -0, 0, 0], [-0, -0, 1, 1], [-0, -0, 2, 2]]

        result = pyscan.startScan()
        self.standard_scan_tests(result, test_dal, indict1, indict2, expected_positions)
        self.standard_line_tests(result, indict1, indict2, expected_positions)

        # Repeat the same test with multiple measurements.

        indict1, indict2 = self.get_ScanLine_indices()
        # Each measurement (KnobReadback, Observable, Validation) is repeated 4 times.
        indict2["NumberOfMeasurements"] = 4
        # This should not change anything - and we are testing this.
        indict1["NumberOfMeasurements"] = 5

        test_dal = TestPyScanDal()
        pyscan = CurrentScan()
        self.standard_init_tests(pyscan.initializeScan([indict1, indict2], test_dal))
        result = pyscan.startScan()
        self.standard_scan_tests(result, test_dal, indict1, indict2, expected_positions)
        self.standard_line_tests(result, indict1, indict2, expected_positions)

    def standard_series_tests(self, result, indict1, indict2, expected_positions):
        n_measurements = indict2["NumberOfMeasurements"]
        knob_readbacks = result["KnobReadback"]

        # Re-group the expanded expected positions by the number of measurements.
        if n_measurements > 1:
            for index, position in enumerate(expected_positions):
                expected_positions[index] = [position] * n_measurements

        # There should be 2 dimensions in the results (indict1, indict2).
        self.assertEqual(len(knob_readbacks), 2,
                         "The number of knob_readbacks do not match with the number of axis.")
        # Each row represents the number of steps in the first axis.
        self.assertEqual(len(knob_readbacks[0]), indict1["Nstep"][0],
                         "The number of knob_readbacks do not match with the first dimension steps.")
        # Again one entry for each axis.
        self.assertEqual(len(knob_readbacks[0][0]), 2,
                         "The number of knob_readbacks do not match with the number of axis.")
        # And finally the last dimension represents the number of steps in the last axis.
        self.assertEqual(len(knob_readbacks[0][0][0]), indict2["Nstep"][0],
                         "The number of knob_readbacks do not match with the second dimension steps.")

        observables = result["Observable"]
        # Same logic as for the knob readbacks.
        self.assertEqual(len(observables), 2,
                         "The number of observables do not match with the number of axis.")
        self.assertEqual(len(observables[0]), indict1['Nstep'][0],
                         "The number of observables do not match with the first dimension steps.")
        self.assertEqual(len(observables[0][0]), 2,
                         "The number of observables do not match with the number of axis.")
        self.assertEqual(len(observables[0][0][0]), indict2["Nstep"][0],
                         "The number of observables do not match with the second dimension steps.")

        # TODO: Test result["Validation"] -> why is it even empty?

        # Check if the number of measurements is correct for the results.
        if n_measurements > 1:
            self.assertEqual(len(knob_readbacks[0][0][0][0]), n_measurements,
                             "The number of measurements do not match with the second dimension NumberOfMeasurements.")

            self.assertEqual(observables[0][0][0][0], [indict2['Observable']] * n_measurements,
                             "Not the correct number of observables was read.")
        else:
            # Check if only observables from the last dimension were read.
            self.assertEqual(observables[0][0][0][0], indict2['Observable'],
                             "The last dimension observables are not read.")

    def test_ScanSeries(self):
        indict1, indict2 = self.get_ScanSeries_indices()
        # Only the number of measurements on the last dimension can influence the result.
        indict1["NumberOfMeasurements"] = 3

        test_dal = TestPyScanDal()
        pyscan = CurrentScan()
        self.standard_init_tests(pyscan.initializeScan([indict1, indict2], test_dal))

        # Vary one value in its entire range, per axis. Other values are initial positions.
        expected_positions = [[-3, "1.2", 0, "2.2"], [-3, "1.2", 1, "2.2"], [-3, "1.2", 2, "2.2"],
                              [-3, "1.2", "2.1", 0], [-3, "1.2", "2.1", 1], [-3, "1.2", "2.1", 2],
                              [-2, "1.2", 0, "2.2"], [-2, "1.2", 1, "2.2"], [-2, "1.2", 2, "2.2"],
                              [-2, "1.2", "2.1", 0], [-2, "1.2", "2.1", 1], [-2, "1.2", "2.1", 2],
                              [-1, "1.2", 0, "2.2"], [-1, "1.2", 1, "2.2"], [-1, "1.2", 2, "2.2"],
                              [-1, "1.2", "2.1", 0], [-1, "1.2", "2.1", 1], [-1, "1.2", "2.1", 2],
                              [-0, "1.2", 0, "2.2"], [-0, "1.2", 1, "2.2"], [-0, "1.2", 2, "2.2"],
                              [-0, "1.2", "2.1", 0], [-0, "1.2", "2.1", 1], [-0, "1.2", "2.1", 2],
                              ["1.1", -3, 0, "2.2"], ["1.1", -3, 1, "2.2"], ["1.1", -3, 2, "2.2"],
                              ["1.1", -3, "2.1", 0], ["1.1", -3, "2.1", 1], ["1.1", -3, "2.1", 2],
                              ["1.1", -2, 0, "2.2"], ["1.1", -2, 1, "2.2"], ["1.1", -2, 2, "2.2"],
                              ["1.1", -2, "2.1", 0], ["1.1", -2, "2.1", 1], ["1.1", -2, "2.1", 2],
                              ["1.1", -1, 0, "2.2"], ["1.1", -1, 1, "2.2"], ["1.1", -1, 2, "2.2"],
                              ["1.1", -1, "2.1", 0], ["1.1", -1, "2.1", 1], ["1.1", -1, "2.1", 2],
                              ["1.1", -0, 0, "2.2"], ["1.1", -0, 1, "2.2"], ["1.1", -0, 2, "2.2"],
                              ["1.1", -0, "2.1", 0], ["1.1", -0, "2.1", 1], ["1.1", -0, "2.1", 2]]

        result = pyscan.startScan()
        self.standard_scan_tests(result, test_dal, indict1, indict2, expected_positions)
        self.standard_series_tests(result, indict1, indict2, expected_positions)

        # Repeat the same test with multiple measurements.

        indict1, indict2 = self.get_ScanSeries_indices()
        # Each measurement (KnobReadback, Observable, Validation) is repeated 4 times.
        indict2["NumberOfMeasurements"] = 2
        # Only the number of measurements on the last dimension can influence the result.
        indict1["NumberOfMeasurements"] = 3

        test_dal = TestPyScanDal()
        pyscan = CurrentScan()
        self.standard_init_tests(pyscan.initializeScan([indict1, indict2], test_dal))
        result = pyscan.startScan()
        self.standard_scan_tests(result, test_dal, indict1, indict2, expected_positions)
        self.standard_series_tests(result, indict1, indict2, expected_positions)

    def test_ScanMixed(self):
        # First dimension is Range scan, second is Series scan.
        indict1, _ = self.get_ScanLine_indices()
        _, indict2 = self.get_ScanSeries_indices()
        # Only the number of measurements on the last dimension can influence the result.
        indict1["NumberOfMeasurements"] = 3

        test_dal = TestPyScanDal()
        pyscan = CurrentScan()
        self.standard_init_tests(pyscan.initializeScan([indict1, indict2], test_dal))

        # First dimension LineScan, second dimension first change one, than another.
        expected_positions = [[-3, -3, 0, "2.2"], [-3, -3, 1, "2.2"], [-3, -3, 2, "2.2"],
                              [-3, -3, "2.1", 0], [-3, -3, "2.1", 1], [-3, -3, "2.1", 2],
                              [-2, -2, 0, "2.2"], [-2, -2, 1, "2.2"], [-2, -2, 2, "2.2"],
                              [-2, -2, "2.1", 0], [-2, -2, "2.1", 1], [-2, -2, "2.1", 2],
                              [-1, -1, 0, "2.2"], [-1, -1, 1, "2.2"], [-1, -1, 2, "2.2"],
                              [-1, -1, "2.1", 0], [-1, -1, "2.1", 1], [-1, -1, "2.1", 2],
                              [-0, -0, 0, "2.2"], [-0, -0, 1, "2.2"], [-0, -0, 2, "2.2"],
                              [-0, -0, "2.1", 0], [-0, -0, "2.1", 1], [-0, -0, "2.1", 2]]

        result = pyscan.startScan()
        self.standard_scan_tests(result, test_dal, indict1, indict2, expected_positions)

        # TODO: Profile the outputs.

        # Repeat the same test with multiple measurements.

        indict1, _ = self.get_ScanLine_indices()
        _, indict2 = self.get_ScanSeries_indices()
        # Only the number of measurements on the last dimension can influence the result.
        indict1["NumberOfMeasurements"] = 3
        # Each measurement (KnobReadback, Observable, Validation) is repeated 4 times.
        indict2["NumberOfMeasurements"] = 4

        test_dal = TestPyScanDal()
        pyscan = CurrentScan()
        self.standard_init_tests(pyscan.initializeScan([indict1, indict2], test_dal))

        # TODO: Profile the outputs.

    def test_output_format(self):
        indict1, indict3 = self.get_ScanLine_indices()
        indict2, indict4 = self.get_ScanSeries_indices()

        test_dal = TestPyScanDal()
        pyscan = CurrentScan()
        result = pyscan.initializeScan([indict1, indict2, indict3, indict4], test_dal)

        self.assertEqual(result["Validation"], test_output_format_expected_result,
                         "The pre-allocation was not correct. Oh boy..")

    def test_Monitors(self):
        pass

    def test_Additive(self):
        pass

    def test_Actions(self):
        pass

    def test_abort(self):
        pass

    def test_pause(self):
        pass

    def test_progress(self):
        pass