import threading
import unittest
from time import sleep, time


from pyscan.utils import flat_list_generator

from tests.helpers.pyScan_data import test_output_format_expected_result, test_ScanLine_first_KnobReadback, \
    test_ScanLine_first_Validation, test_ScanLine_first_Observable, test_ScanLine_second_KnobReadback, \
    test_ScanLine_second_Validation, test_ScanLine_second_Observable, test_ScanSeries_first_KnobReadback, \
    test_ScanSeries_first_Validation, test_ScanSeries_first_Observable, test_ScanSeries_second_KnobReadback, \
    test_ScanSeries_second_Validation, test_ScanSeries_second_Observable, test_ScanMixed_first_KnobReadback, \
    test_ScanMixed_first_Validation, test_ScanMixed_first_Observable, test_ScanMixed_second_KnobReadback, \
    test_ScanMixed_second_Validation, test_ScanMixed_second_Observable, test_SimpleScan_first_KnobReadback, \
    test_SimpleScan_first_Validation, test_SimpleScan_first_Observable, test_SimpleScan_second_KnobReadback, \
    test_SimpleScan_second_Validation, test_SimpleScan_second_Observable

# Comment this 2 lines to test with the old dal.
from tests.helpers.scan_old import Scan as CurrentScan
from tests.helpers.utils import TestPyScanDal as CurrentMockDal

from pyscan.interface.pyScan import Scan as CurrentScan
from tests.helpers.mock_epics_dal import MockPyEpicsDal as CurrentMockDal


class PyScan(unittest.TestCase):
    @staticmethod
    def get_ScanLine_indices():
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
        indict2["ScanValues"] = [[0, 1, 2], [0, 1]]
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

        n_measurements = indict2["NumberOfMeasurements"]

        # The first element of the result must be the initial PV values.
        original_values = test_dal.get_positions()[0]
        expected_values = indict1["Knob"] + indict2["Knob"] + indict2["Observable"]
        self.assertEqual(original_values, expected_values,
                         "The first element of the read positions should be the initial condition.")

        # Adjust the expected results to match the number of measurements on the last dimension.
        expanded_expected_positions = []

        if n_measurements > 1:
            for position in expected_positions:
                expanded_expected_positions.extend([position] * n_measurements)
        else:
            expanded_expected_positions = expected_positions

        # First 4 PVs are readbacks, the first array entry is the original values before changing them for measuring.
        sampled_positions = list(flat_list_generator([element for element in test_dal.get_positions()[1:]]))
        sampled_positions = [position[:4] for position in sampled_positions]
        self.assertEqual(sampled_positions, expanded_expected_positions,
                         "The expected positions do not match the one read by the mock dal.")

    def standard_line_tests(self, result, indict1, indict2, expected_positions):
        n_measurements = indict2["NumberOfMeasurements"]

        knob_readbacks = result["KnobReadback"]

        # Flatten the list.
        knob_readbacks_expanded = list(flat_list_generator(result["KnobReadback"]))
        knob_readbacks_expanded = [knob[:4] for knob in knob_readbacks_expanded]

        # Re-group the expanded expected positions by the number of measurements.
        if n_measurements > 1:
            for index, position in enumerate(expected_positions):
                expected_positions[index] = [position] * n_measurements
        expected_positions = list(flat_list_generator(expected_positions))

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

        test_dal = CurrentMockDal()
        pyscan = CurrentScan()
        self.standard_init_tests(pyscan.initializeScan([indict1, indict2], test_dal))

        expected_positions = [[-3, -3, 0, 0], [-3, -3, 1, 1], [-3, -3, 2, 2],
                              [-2, -2, 0, 0], [-2, -2, 1, 1], [-2, -2, 2, 2],
                              [-1, -1, 0, 0], [-1, -1, 1, 1], [-1, -1, 2, 2],
                              [-0, -0, 0, 0], [-0, -0, 1, 1], [-0, -0, 2, 2]]

        result = pyscan.startScan()
        self.standard_scan_tests(result, test_dal, indict1, indict2, expected_positions)
        self.standard_line_tests(result, indict1, indict2, expected_positions)

        # Check if the results match with the data collected with the original pyscan.
        self.assertEqual(test_ScanLine_first_KnobReadback, result["KnobReadback"],
                         "KnobReadback format does not match")
        self.assertEqual(test_ScanLine_first_Validation, result["Validation"],
                         "Validation format does not match")
        self.assertEqual(test_ScanLine_first_Observable, result["Observable"],
                         "Observable format does not match")

        # Repeat the same test with multiple measurements.

        indict1, indict2 = self.get_ScanLine_indices()
        # Each measurement (KnobReadback, Observable, Validation) is repeated 4 times.
        indict2["NumberOfMeasurements"] = 4
        # This should not change anything - and we are testing this.
        indict1["NumberOfMeasurements"] = 5

        test_dal = CurrentMockDal()
        pyscan = CurrentScan()
        self.standard_init_tests(pyscan.initializeScan([indict1, indict2], test_dal))
        result = pyscan.startScan()
        self.standard_scan_tests(result, test_dal, indict1, indict2, expected_positions)
        self.standard_line_tests(result, indict1, indict2, expected_positions)

        # Check if the results match with the data collected with the original pyscan.
        self.assertEqual(test_ScanLine_second_KnobReadback, result["KnobReadback"],
                         "KnobReadback format does not match")
        self.assertEqual(test_ScanLine_second_Validation, result["Validation"],
                         "Validation format does not match")
        self.assertEqual(test_ScanLine_second_Observable, result["Observable"],
                         "Observable format does not match")

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

        test_dal = CurrentMockDal()
        pyscan = CurrentScan()
        self.standard_init_tests(pyscan.initializeScan([indict1, indict2], test_dal))

        # Vary one value in its entire range, per axis. Other values are initial positions.
        expected_positions = [[-3, "1.2", 0, "2.2"], [-3, "1.2", 1, "2.2"], [-3, "1.2", 2, "2.2"],
                              [-3, "1.2", "2.1", 0], [-3, "1.2", "2.1", 1],
                              [-2, "1.2", 0, "2.2"], [-2, "1.2", 1, "2.2"], [-2, "1.2", 2, "2.2"],
                              [-2, "1.2", "2.1", 0], [-2, "1.2", "2.1", 1],
                              [-1, "1.2", 0, "2.2"], [-1, "1.2", 1, "2.2"], [-1, "1.2", 2, "2.2"],
                              [-1, "1.2", "2.1", 0], [-1, "1.2", "2.1", 1],
                              [-0, "1.2", 0, "2.2"], [-0, "1.2", 1, "2.2"], [-0, "1.2", 2, "2.2"],
                              [-0, "1.2", "2.1", 0], [-0, "1.2", "2.1", 1],
                              ["1.1", -3, 0, "2.2"], ["1.1", -3, 1, "2.2"], ["1.1", -3, 2, "2.2"],
                              ["1.1", -3, "2.1", 0], ["1.1", -3, "2.1", 1],
                              ["1.1", -2, 0, "2.2"], ["1.1", -2, 1, "2.2"], ["1.1", -2, 2, "2.2"],
                              ["1.1", -2, "2.1", 0], ["1.1", -2, "2.1", 1],
                              ["1.1", -1, 0, "2.2"], ["1.1", -1, 1, "2.2"], ["1.1", -1, 2, "2.2"],
                              ["1.1", -1, "2.1", 0], ["1.1", -1, "2.1", 1],
                              ["1.1", -0, 0, "2.2"], ["1.1", -0, 1, "2.2"], ["1.1", -0, 2, "2.2"],
                              ["1.1", -0, "2.1", 0], ["1.1", -0, "2.1", 1]]

        result = pyscan.startScan()
        self.standard_scan_tests(result, test_dal, indict1, indict2, expected_positions)
        self.standard_series_tests(result, indict1, indict2, expected_positions)

        # Check if the results match with the data collected with the original pyscan.
        self.assertEqual(test_ScanSeries_first_KnobReadback, result["KnobReadback"],
                         "KnobReadback format does not match")
        self.assertEqual(test_ScanSeries_first_Validation, result["Validation"],
                         "Validation format does not match")
        self.assertEqual(test_ScanSeries_first_Observable, result["Observable"],
                         "Observable format does not match")

        # Repeat the same test with multiple measurements.

        indict1, indict2 = self.get_ScanSeries_indices()
        # Each measurement (KnobReadback, Observable, Validation) is repeated 4 times.
        indict2["NumberOfMeasurements"] = 2
        # Only the number of measurements on the last dimension can influence the result.
        indict1["NumberOfMeasurements"] = 3

        test_dal = CurrentMockDal()
        pyscan = CurrentScan()
        self.standard_init_tests(pyscan.initializeScan([indict1, indict2], test_dal))
        result = pyscan.startScan()
        self.standard_scan_tests(result, test_dal, indict1, indict2, expected_positions)
        self.standard_series_tests(result, indict1, indict2, expected_positions)

        # Check if the results match with the data collected with the original pyscan.
        self.assertEqual(test_ScanSeries_second_KnobReadback, result["KnobReadback"],
                         "KnobReadback format does not match")
        self.assertEqual(test_ScanSeries_second_Validation, result["Validation"],
                         "Validation format does not match")
        self.assertEqual(test_ScanSeries_second_Observable, result["Observable"],
                         "Observable format does not match")

    def test_ScanMixed(self):
        # First dimension is Range scan, second is Series scan.
        indict1, _ = self.get_ScanLine_indices()
        _, indict2 = self.get_ScanSeries_indices()
        # Only the number of measurements on the last dimension can influence the result.
        indict1["NumberOfMeasurements"] = 3

        test_dal = CurrentMockDal()
        pyscan = CurrentScan()
        self.standard_init_tests(pyscan.initializeScan([indict1, indict2], test_dal))

        # First dimension LineScan, second dimension first change one, than another.
        expected_positions = [[-3, -3, 0, "2.2"], [-3, -3, 1, "2.2"], [-3, -3, 2, "2.2"],
                              [-3, -3, "2.1", 0], [-3, -3, "2.1", 1],
                              [-2, -2, 0, "2.2"], [-2, -2, 1, "2.2"], [-2, -2, 2, "2.2"],
                              [-2, -2, "2.1", 0], [-2, -2, "2.1", 1],
                              [-1, -1, 0, "2.2"], [-1, -1, 1, "2.2"], [-1, -1, 2, "2.2"],
                              [-1, -1, "2.1", 0], [-1, -1, "2.1", 1],
                              [-0, -0, 0, "2.2"], [-0, -0, 1, "2.2"], [-0, -0, 2, "2.2"],
                              [-0, -0, "2.1", 0], [-0, -0, "2.1", 1]]

        result = pyscan.startScan()
        self.standard_scan_tests(result, test_dal, indict1, indict2, expected_positions)

        # Check if the results match with the data collected with the original pyscan.
        self.assertEqual(test_ScanMixed_first_KnobReadback, result["KnobReadback"],
                         "KnobReadback format does not match")
        self.assertEqual(test_ScanMixed_first_Validation, result["Validation"],
                         "Validation format does not match")
        self.assertEqual(test_ScanMixed_first_Observable, result["Observable"],
                         "Observable format does not match")

        # Repeat the same test with multiple measurements.

        indict1, _ = self.get_ScanLine_indices()
        _, indict2 = self.get_ScanSeries_indices()
        # Only the number of measurements on the last dimension can influence the result.
        indict1["NumberOfMeasurements"] = 3
        # Each measurement (KnobReadback, Observable, Validation) is repeated 4 times.
        indict2["NumberOfMeasurements"] = 4

        test_dal = CurrentMockDal()
        pyscan = CurrentScan()
        self.standard_init_tests(pyscan.initializeScan([indict1, indict2], test_dal))

        # Check if the results match with the data collected with the original pyscan.
        self.assertEqual(test_ScanMixed_second_KnobReadback, result["KnobReadback"],
                         "KnobReadback format does not match")
        self.assertEqual(test_ScanMixed_second_Validation, result["Validation"],
                         "Validation format does not match")
        self.assertEqual(test_ScanMixed_second_Observable, result["Observable"],
                         "Observable format does not match")

    def test_output_format(self):
        # Test with the old scan, to verify if this is it.
        indict1, indict3 = self.get_ScanLine_indices()
        indict2, indict4 = self.get_ScanSeries_indices()

        test_dal = CurrentMockDal()
        pyscan = CurrentScan()
        result = pyscan.initializeScan([indict1, indict2, indict3, indict4], test_dal)

        self.assertEqual(result["Validation"], test_output_format_expected_result,
                         "The pre-allocation was not correct. Oh boy..")

    def test_simple_scan(self):
        # Test the simplest possible scan.
        indict1 = dict()
        indict1['Knob'] = ["1.1"]
        indict1["ScanValues"] = [-3, -2, -1, 0]
        indict1['Observable'] = ["READ1"]
        indict1['Waiting'] = 0.1

        test_dal = CurrentMockDal()
        pyscan = CurrentScan()
        result = pyscan.initializeScan(indict1, test_dal)
        self.standard_init_tests(result)
        result = pyscan.startScan()

        # Check if the results match with the data collected with the original pyscan.
        self.assertEqual(test_SimpleScan_first_KnobReadback, result["KnobReadback"],
                         "KnobReadback format does not match")
        self.assertEqual(test_SimpleScan_first_Validation, result["Validation"],
                         "Validation format does not match")
        self.assertEqual(test_SimpleScan_first_Observable, result["Observable"],
                         "Observable format does not match")

        # With multiple measurements.

        indict1 = dict()
        indict1['Knob'] = ["1.1"]
        indict1["ScanValues"] = [-3, -2, -1, 0]
        indict1['Observable'] = ["READ1"]
        indict1['Waiting'] = 0.1
        indict1["NumberOfMeasurements"] = 3

        test_dal = CurrentMockDal()
        pyscan = CurrentScan()
        result = pyscan.initializeScan(indict1, test_dal)
        self.standard_init_tests(result)
        result = pyscan.startScan()

        # Check if the results match with the data collected with the original pyscan.
        self.assertEqual(test_SimpleScan_second_KnobReadback, result["KnobReadback"],
                         "KnobReadback format does not match")
        self.assertEqual(test_SimpleScan_second_Validation, result["Validation"],
                         "Validation format does not match")
        self.assertEqual(test_SimpleScan_second_Observable, result["Observable"],
                         "Observable format does not match")

    def test_Monitors(self):
        indict1, indict2 = self.get_ScanLine_indices()
        # Only the number of measurements on the last dimension can influence the result.
        indict2['Monitor'] = ["PYSCAN:TEST:MONITOR1"]
        indict2['MonitorValue'] = [1]
        indict2['MonitorTolerance'] = [0.01]
        indict2['MonitorAction'] = ["WaitAndAbort"]
        indict2['MonitorTimeout'] = [3]

        # This will pass, because every 2 read attempts the monitor will have a valid value.
        test_dal = CurrentMockDal(pv_fixed_values={"PYSCAN:TEST:MONITOR1": [0, 1]})
        pyscan = CurrentScan()
        self.standard_init_tests(pyscan.initializeScan([indict1, indict2], test_dal))
        result = pyscan.startScan()

        # Correct "ErrorMessage" when successfully completed.
        self.assertEqual(result["ErrorMessage"], "Measurement finalized (finished/aborted) normally. "
                                                 "Need initialisation before next measurement.", "Scan failed.")

        # This will never pass, but we should wait for the retry attempts in this case.
        test_dal = CurrentMockDal(pv_fixed_values={"PYSCAN:TEST:MONITOR1": [0]})
        pyscan = CurrentScan()
        self.standard_init_tests(pyscan.initializeScan([indict1, indict2], test_dal))

        # Correct "ErrorMessage" when successfully completed.
        pyscan.startScan()
        self.assertRaisesRegex(Exception, "Number of maximum read attempts", pyscan.startScan)

        # This will never pass, but the scan has to abort immediately without doing 3 attempts.
        indict2['MonitorAction'] = ["Abort"]
        test_dal = CurrentMockDal(pv_fixed_values={"PYSCAN:TEST:MONITOR1": [0]})
        pyscan = CurrentScan()
        self.standard_init_tests(pyscan.initializeScan([indict1, indict2], test_dal))

        # Correct "ErrorMessage" when successfully completed.
        self.assertRaisesRegex(Exception, "expected value", pyscan.startScan)

    def test_Additive(self):
        # TODO: Test if the additive mode works well.
        pass

    def test_abort(self):
        indict1 = dict()
        indict1['Knob'] = ["1.1"]
        indict1["ScanValues"] = [-3, -2, -1, 0]
        indict1['Observable'] = ["READ1"]
        indict1['Waiting'] = 0.3

        test_dal = CurrentMockDal()
        pyscan = CurrentScan()
        result = pyscan.initializeScan(indict1, test_dal)
        self.standard_init_tests(result)

        def abort_scan():
            sleep(0.1)
            # We might want to wait for the initialization to happen, or just wait for the pause to work.
            n_retry = 0
            while n_retry < 5:
                try:
                    pyscan.abortScan = 1
                except:
                    pass
                n_retry += 1
                # Initialization should not take more than 1 second.
                sleep(0.2)

        threading.Thread(target=abort_scan).start()
        self.assertRaisesRegex(Exception, "aborted", pyscan.startScan)

    def test_pause(self):
        indict1 = dict()
        indict1['Knob'] = ["1.1"]
        indict1["ScanValues"] = [-3, -2, -1, 0]
        indict1['Observable'] = ["READ1"]
        indict1['Waiting'] = 0.3
        indict1['StepbackOnPause'] = 0

        test_dal = CurrentMockDal()
        pyscan = CurrentScan()
        result = pyscan.initializeScan(indict1, test_dal)
        self.standard_init_tests(result)

        def pause_scan():
            # We need to let the scan initialize first, otherwise it overwrites the pauseScan flag.
            sleep(0.1)
            # We might want to wait for the initialization to happen, or just wait for the pause to work.
            n_retry = 0
            while n_retry < 5:
                try:
                    pyscan.pauseScan = 1
                except:
                    pass
                n_retry += 1
                # Initialization should not take more than 1 second.
                sleep(0.2)
            sleep(3)
            pyscan.pauseScan = 0

        begin_timestamp = time()
        threading.Thread(target=pause_scan).start()
        pyscan.startScan()

        time_elapsed = time() - begin_timestamp
        self.assertTrue(time_elapsed > 3, "We paused the scan for 3 seconds, but this did not "
                                          "reflect in the execution time %f." % time_elapsed)

    def test_abort_paused_scan(self):
        indict1 = dict()
        indict1['Knob'] = ["1.1"]
        indict1["ScanValues"] = [-3, -2, -1, 0]
        indict1['Observable'] = ["READ1"]
        indict1['Waiting'] = 0.3
        indict1['StepbackOnPause'] = 0

        test_dal = CurrentMockDal()
        pyscan = CurrentScan()
        result = pyscan.initializeScan(indict1, test_dal)
        self.standard_init_tests(result)

        def pause_scan():
            # We need to let the scan initialize first, otherwise it overwrites the pauseScan flag.
            sleep(0.1)
            # We might want to wait for the initialization to happen, or just wait for the pause to work.
            n_retry = 0
            while n_retry < 5:
                try:
                    pyscan.pauseScan = 1
                except:
                    pass
                n_retry += 1
                # Initialization should not take more than 1 second.
                sleep(0.2)
            sleep(3)
            pyscan.abortScan = 1

        begin_timestamp = time()
        threading.Thread(target=pause_scan).start()

        self.assertRaisesRegex(Exception, "aborted", pyscan.startScan)
        time_elapsed = time() - begin_timestamp
        self.assertTrue(time_elapsed > 3, "We paused the scan for 3 seconds before aborting, "
                                          "but this did not reflect in the execution time %f." % time_elapsed)

    def test_progress(self):
        indict = {}
        indict['Knob'] = "PYSCAN:TEST:MOTOR1:SET"
        indict['Waiting'] = 0.5

        indict['Observable'] = "PYSCAN:TEST:OBS1"
        # One percentage step for each scan value.
        indict['ScanValues'] = [0, 1, 2, 3]
        # This should not change the percentages.
        indict['NumberOfMeasurements'] = 2

        test_dal = CurrentMockDal()
        pyscan = CurrentScan()

        # Check if the progress bar works.
        def monitor_scan():
            # make sure the initialization is done:
            while pyscan.ProgDisp.Progress:
                sleep(1)

            current_value = 0
            while current_value < 100:
                last_value = pyscan.ProgDisp.Progress
                if last_value > current_value:
                    progress_values.append(pyscan.ProgDisp.Progress)
                    current_value = last_value
            else:
                nonlocal progress_completed
                progress_completed = True

        progress_values = []
        progress_completed = False
        threading.Thread(target=monitor_scan).start()

        pyscan.initializeScan(indict, dal=test_dal)
        outdict = pyscan.startScan()

        # Correct "ErrorMessage" when successfully completed.
        self.assertEqual(outdict["ErrorMessage"], "Measurement finalized (finished/aborted) normally. "
                                                  "Need initialisation before next measurement.", "Scan failed.")

        # Wait for the progress thread to terminate.
        sleep(0.2)

        self.assertTrue(progress_completed, "Progress bar did not complete.")
        self.assertListEqual(progress_values, [25, 50, 75, 100], "The completed percentage is wrong.")
