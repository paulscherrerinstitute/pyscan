import traceback
from datetime import datetime
from time import sleep

import numpy as np
from copy import deepcopy

from pyscan.epics_dal import PyEpicsDal
from pyscan.interface.pyScan.utils import PyScanDataProcessor
from pyscan.positioner import VectorPositioner, SerialPositioner, CompoundPositioner
from pyscan.scan import Scanner
from pyscan.utils import convert_to_list, convert_to_position_list

READ_GROUP = "Measurements"
WRITE_GROUP = "Knobs"
MONITOR_GROUP = "Monitors"


class Scan(object):
    def execute_scan(self):

        data_processor = PyScanDataProcessor(self.outdict,
                                             n_readbacks=self.n_readbacks,
                                             n_validations=self.n_validations,
                                             n_observables=self.n_observables,
                                             n_measurements=self.n_measurements)

        after_executor = self.get_action_executor("In-loopPostAction")

        # Wrap the post action executor to update the number of completed scans.
        def progress_after_executor(scanner_instance):
            # Execute other post actions.
            after_executor(scanner_instance)

            # Update progress.
            self.n_done_measurements += 1
            self.ProgDisp.Progress = 100.0 * (self.n_done_measurements /
                                              self.n_total_positions)

        def prepare_monitors(reader):
            # TODO: Make actual EPICS monitors, instead of polling (if this is desired?, ASK FIRST!)

            # If there are no monitors defined we have nothing to validate.
            if not self.dimensions[-1]["Monitor"]:
                return None

            def validate_monitors(position, data):
                monitor_values = reader()
                combined_data = zip(self.dimensions[-1]['Monitor'],
                                    self.dimensions[-1]['MonitorValue'],
                                    self.dimensions[-1]['MonitorTolerance'],
                                    self.dimensions[-1]['MonitorAction'],
                                    self.dimensions[-1]['MonitorTimeout'],
                                    monitor_values)

                for pv, expected_value, tolerance, action, timeout, value in combined_data:
                    # Monitor value does not match.
                    if not self.match_monitor_value(value, expected_value, tolerance):

                        if action == "Abort":
                            raise ValueError("Monitor %s, expected value %s, tolerance %s, has value %s. Aborting."
                                             % (pv, expected_value, tolerance, value))
                        elif action == "WaitAndAbort":
                            # TODO: The "wait" part in WaitAndAbort.
                            raise ValueError("Monitor %s, expected value %s, tolerance %s, has value %s. Aborting."
                                             % (pv, expected_value, tolerance, value))
                        else:
                            # TODO: Other actions do not really have a defined behaviour. Do we need any more?
                            raise ValueError("MonitorAction %s, on PV %s, is not supported." % (pv, action))

                return True

            return validate_monitors

        self.scanner = Scanner(positioner=self.get_positioner(),
                               writer=self.epics_dal.get_group(WRITE_GROUP).set_and_match,
                               data_processor=data_processor,
                               reader=self.epics_dal.get_group(READ_GROUP).read,
                               before_executor=self.get_action_executor("In-loopPreAction"),
                               after_executor=progress_after_executor,
                               initialization_executor=self.get_action_executor("PreAction"),
                               finalization_executor=self.get_action_executor("PostAction"),
                               data_validator=prepare_monitors(self.epics_dal.get_group(MONITOR_GROUP).read))

        after_move_settling_time = self.dimensions[-1]["KnobWaitingExtra"]
        self.outdict.update(self.scanner.discrete_scan(after_move_settling_time))

    def get_positioner(self):
        """
        Generate a positioner for the provided dimensions.
        :return: Positioner object.
        """
        # Read all the initial positions - in case we need to do an additive scan.
        initial_positions = self.epics_dal.get_group(READ_GROUP).read(n_measurements=1)

        positioners = []
        knob_readback_offset = 0
        for dimension in self.dimensions:
            is_additive = bool(dimension.get("Additive", 0))
            is_series = bool(dimension.get("Series", 0))
            n_knob_readbacks = len(dimension["KnobReadback"])

            # This dimension uses relative positions, read the PVs initial state.
            # We also need initial positions for the series scan.
            if is_additive or is_series:
                offsets = convert_to_list(
                    initial_positions[knob_readback_offset:knob_readback_offset + n_knob_readbacks])
            else:
                offsets = None

            # Series scan in this dimension, use StepByStepVectorPositioner.
            if is_series:
                # In the StepByStep positioner, the initial values need to be added to the steps.
                positions = convert_to_list(dimension["ScanValues"])
                positioners.append(SerialPositioner(positions, initial_positions=offsets,
                                                    offsets=offsets if is_additive else None))
            # Line scan in this dimension, use VectorPositioner.
            else:
                positions = convert_to_position_list(convert_to_list(dimension["KnobExpanded"]))
                positioners.append(VectorPositioner(positions, offsets=offsets))

            # Increase the knob readback offset.
            knob_readback_offset += n_knob_readbacks

        # Assemble all individual positioners together.
        positioner = CompoundPositioner(positioners)
        return positioner

    def get_action_executor(self, entry_name):
        actions = []
        max_waiting = 0
        for dim_index, dim in enumerate(self.dimensions):
            for action_index, action in enumerate(dim[entry_name]):
                set_pv, read_pv, value, tolerance, timeout = action
                if set_pv == "match":
                    raise NotImplementedError("match not yet implemented for PreAction.")

                # Initialize the write group, to speed up in loop stuff.
                group_name = "%s_%d_%d" % (entry_name, dim_index, action_index)
                self.epics_dal.add_writer_group(group_name, set_pv, read_pv, tolerance, timeout)
                actions.append((group_name, value))

            if entry_name + "Waiting" in dim:
                max_waiting = max(max_waiting, dim[entry_name + "Waiting"])

        def execute(scanner):
            for action in actions:
                name = action[0]
                value = action[1]
                # Retrieve the epics group and write the value.
                self.epics_dal.get_group(name).set_and_match(value)

            sleep(max_waiting)

        return execute

    @staticmethod
    def match_monitor_value(value, expected_value, tolerance):
        # We have a NON-ZERO tolerance policy.
        if not tolerance:
            tolerance = 0.00001

        # Monitor value is in list, i.e. several cases are okay
        if isinstance(expected_value, list):
            if value in expected_value:
                return True
        # String values must match exactly.
        elif isinstance(value, str):
            if value == expected_value:
                return True
        # Numbers have to take into account the tolerance.
        elif isinstance(value, int) or isinstance(value, float):
            if abs(value - expected_value) < tolerance:
                return True
        else:
            raise ValueError("Unexpected case.\nvalue = %s\nexpected_value = %s\ntolerance = %s" %
                             (value, expected_value, tolerance))

        return False

    class DummyProgress(object):
        def __init__(self):
            self.Progress = 0
            self.abortScan = 0

    def __init__(self):
        self.dimensions = None
        self.epics_dal = None
        self.scanner = None
        self.outdict = None

        self.all_read_pvs = None
        self.n_readbacks = None
        self.n_validations = None
        self.n_observables = None
        self.n_total_positions = None
        self.n_measurements = None

        # Accessed by some clients.
        self.ProgDisp = None
        self._pauseScan = 0

        # Just to make old GUI work.
        self._abortScan = 0
        self.n_done_measurements = 0

    @property
    def abortScan(self):
        return self._abort_scan

    @abortScan.setter
    def abortScan(self, value):
        self._abortScan = value

        if self._abortScan:
            self.scanner.abort_scan()

    @property
    def pauseScan(self):
        return self._pauseScan

    @pauseScan.setter
    def pauseScan(self, value):
        self._pauseScan = value

        if self._pauseScan:
            self.scanner.pause_scan()
        else:
            self.scanner.resume_scan()

    def initializeScan(self, inlist, dal=None):
        """
        Initialize and verify the provided scan values.
        :param inlist: List of dictionaries for each dimension.
        :param dal: Which reader should be used to access the PVs. Default: PyEpicsDal.
        :return: Dictionary with results.
        """
        if not inlist:
            raise ValueError("Provided inlist is empty.")

        if dal is not None:
            self.epics_dal = dal
        else:
            self.epics_dal = PyEpicsDal()

        # Prepare the scan dimensions.
        if isinstance(inlist, list):
            self.dimensions = inlist
        # In case it is a simple one dimensional scan.
        else:
            self.dimensions = [inlist]

        try:
            for index, dic in enumerate(self.dimensions):
                # We read most of the PVs only if declared in the last dimension.
                is_last_dimension = index == (len(self.dimensions) - 1)

                # Just in case there are identical input dictionaries. (Normally, it may not happen.)
                dic['ID'] = index

                # Waiting time.
                if is_last_dimension and ('Waiting' not in dic.keys()):
                    raise ValueError('Waiting for the scan was not given.')

                # Validation channels - values just added to the results.
                if 'Validation' in dic.keys():
                    if not isinstance(dic['Validation'], list):
                        raise ValueError('Validation should be a list of channels. Input dictionary %d.' % index)
                else:
                    dic['Validation'] = []

                # Relative scan.
                if 'Additive' not in dic.keys():
                    dic['Additive'] = 0

                # Step back when pause is invoked.
                if is_last_dimension and ('StepbackOnPause' not in dic.keys()):
                    dic['StepbackOnPause'] = 1

                # Number of measurments per position.
                if is_last_dimension and ('NumberOfMeasurements' not in dic.keys()):
                    dic['NumberOfMeasurements'] = 1

                # PVs to sample.
                if is_last_dimension and ('Observable' not in dic.keys()):
                    raise ValueError('The observable is not given.')
                elif is_last_dimension:
                    if not isinstance(dic['Observable'], list):
                        dic['Observable'] = [dic['Observable']]

                self._setup_knobs(index, dic)

                self._setup_knob_scan_values(index, dic)

                self._setup_pre_actions(index, dic)

                self._setup_inloop_pre_actions(index, dic)

                self._setup_post_action(index, dic)

                self._setup_inloop_post_action(index, dic)

            # Total number of measurements
            self.n_total_positions = 1
            for dic in self.dimensions:
                if not dic['Series']:
                    self.n_total_positions = self.n_total_positions * dic['Nstep']
                else:
                    self.n_total_positions = self.n_total_positions * sum(dic['Nstep'])

            self._setup_epics_dal()
            # Monitors only in the last dimension.
            self._setup_monitors(self.dimensions[-1])

            # Prealocating the place for the output
            self.outdict = {"ErrorMessage": None,
                            "KnobReadback": self.allocateOutput(),
                            "Validation": self.allocateOutput(),
                            "Observable": self.allocateOutput()}

        except ValueError:
            self.outdict = {"ErrorMessage": traceback.format_exc()}

        # Backward compatibility.
        self.ProgDisp = Scan.DummyProgress()
        self._pauseScan = 0
        self.abortScan = 0
        self.n_done_measurements = 0

        return self.outdict

    def allocateOutput(self):
        root_list = []
        for dimension in reversed(self.dimensions):
            n_steps = dimension['Nstep']

            if dimension['Series']:
                # For Series scan, each step of each knob represents another result.
                current_dimension_list = []
                for n_steps_in_knob in n_steps:
                    current_knob_list = []
                    for _ in range(n_steps_in_knob):
                        current_knob_list.append(deepcopy(root_list))

                    current_dimension_list.append(deepcopy(current_knob_list))
                root_list = current_dimension_list
            else:
                # For line scan, each step represents another result.
                current_dimension_list = []
                for _ in range(n_steps):
                    current_dimension_list.append(deepcopy(root_list))
                root_list = current_dimension_list

        return root_list

    def _setup_epics_dal(self):
        # Collect all PVs that need to be read at each scan step.
        self.all_read_pvs = []
        all_write_pvs = []
        all_readback_pvs = []
        all_tolerances = []
        max_knob_waiting = -1

        self.n_readbacks = 0
        for d in self.dimensions:
            self.all_read_pvs.append(d['KnobReadback'])
            self.n_readbacks += len(d['KnobReadback'])

            # Collect all data need to write to PVs.
            all_write_pvs.append(d["Knob"])
            all_readback_pvs.append(d["KnobReadback"])
            all_tolerances.append(d["KnobTolerance"])
            max_knob_waiting = max(max_knob_waiting, max(d["KnobWaiting"]))

        self.all_read_pvs.append(self.dimensions[-1]['Validation'])
        self.n_validations = len(self.dimensions[-1]['Validation'])
        self.all_read_pvs.append(self.dimensions[-1]['Observable'])
        self.n_observables = len(self.dimensions[-1]['Observable'])
        # Expand all read PVs
        self.all_read_pvs = [item for sublist in self.all_read_pvs for item in sublist]

        # Expand Knobs and readbacks PVs.
        all_write_pvs = [item for sublist in all_write_pvs for item in sublist]
        all_readback_pvs = [item for sublist in all_readback_pvs for item in sublist]
        all_tolerances = [item for sublist in all_tolerances for item in sublist]

        # The number of measurements is sampled only from the last dimension.
        self.n_measurements = self.dimensions[-1]["NumberOfMeasurements"]

        # How much time should we wait after each measurement
        after_measurement_waiting_time = self.dimensions[-1]["Waiting"]

        # Initialize PV connections and check if all PV names are valid.
        self.epics_dal.add_reader_group(READ_GROUP, self.all_read_pvs, self.n_measurements,
                                        after_measurement_waiting_time)
        self.epics_dal.add_writer_group(WRITE_GROUP, all_write_pvs, all_readback_pvs, all_tolerances, max_knob_waiting)

    def _setup_knobs(self, index, dic):
        """
        Setup the values for moving knobs in the scan.
        :param index: Index in the dictionary.
        :param dic: The dictionary.
        """
        if 'Knob' not in dic.keys():
            raise ValueError('Knob for the scan was not given for the input dictionary %d.' % index)
        else:
            if not isinstance(dic['Knob'], list):
                dic['Knob'] = [dic['Knob']]

        if 'KnobReadback' not in dic.keys():
            dic['KnobReadback'] = dic['Knob']
        if not isinstance(dic['KnobReadback'], list):
            dic['KnobReadback'] = [dic['KnobReadback']]
        if len(dic['KnobReadback']) != len(dic['Knob']):
            raise ValueError('The number of KnobReadback does not meet to the number of Knobs.')

        if 'KnobTolerance' not in dic.keys():
            dic['KnobTolerance'] = [1.0] * len(dic['Knob'])
        if not isinstance(dic['KnobTolerance'], list):
            dic['KnobTolerance'] = [dic['KnobTolerance']]
        if len(dic['KnobTolerance']) != len(dic['Knob']):
            raise ValueError('The number of KnobTolerance does not meet to the number of Knobs.')

        if 'KnobWaiting' not in dic.keys():
            dic['KnobWaiting'] = [10.0] * len(dic['Knob'])
        if not isinstance(dic['KnobWaiting'], list):
            dic['KnobWaiting'] = [dic['KnobWaiting']]
        if len(dic['KnobWaiting']) != len(dic['Knob']):
            raise ValueError('The number of KnobWaiting does not meet to the number of Knobs.')

        if 'KnobWaitingExtra' not in dic.keys():
            dic['KnobWaitingExtra'] = 0.0
        else:
            try:
                dic['KnobWaitingExtra'] = float(dic['KnobWaitingExtra'])
            except:
                raise ValueError('KnobWaitingExtra is not a number in the input dictionary %d.' % index)

        # Originally dic["Knob"] values were saved. I'm supposing this was a bug - readback values needed to be saved.

        # TODO: We can optimize this by moving the initialization in the epics_dal init, but pre actions need
        # to be moved after the epics_dal init than
        self.epics_dal.add_reader_group("KnobReadback", dic['KnobReadback'])
        dic['KnobSaved'] = self.epics_dal.get_group("KnobReadback").read()
        self.epics_dal.close_group("KnobReadback")

    def _setup_knob_scan_values(self, index, dic):
        if 'Series' not in dic.keys():
            dic['Series'] = 0

        if not dic['Series']:  # Setting up scan values for SKS and MKS
            if 'ScanValues' not in dic.keys():
                if 'ScanRange' not in dic.keys():
                    raise ValueError('Neither ScanRange nor ScanValues is given '
                                     'in the input dictionary %d.' % index)
                elif not isinstance(dic['ScanRange'], list):
                    raise ValueError('ScanRange is not given in the right format. '
                                     'Input dictionary %d.' % index)
                elif not isinstance(dic['ScanRange'][0], list):
                    dic['ScanRange'] = [dic['ScanRange']]

                if ('Nstep' not in dic.keys()) and ('StepSize' not in dic.keys()):
                    raise ValueError('Neither Nstep nor StepSize is given.')

                if 'Nstep' in dic.keys():  # StepSize is ignored when Nstep is given
                    if not isinstance(dic['Nstep'], int):
                        raise ValueError('Nstep should be an integer. Input dictionary %d.' % index)
                    ran = []
                    for r in dic['ScanRange']:
                        s = (r[1] - r[0]) / (dic['Nstep'] - 1)
                        f = np.arange(r[0], r[1], s)
                        f = np.append(f, np.array(r[1]))
                        ran.append(f.tolist())
                    dic['KnobExpanded'] = ran
                else:  # StepSize given
                    if len(dic['Knob']) > 1:
                        raise ValueError('Give Nstep instead of StepSize for MKS. '
                                         'Input dictionary %d.' % index)
                    # StepSize is only valid for SKS
                    r = dic['ScanRange'][0]

                    # TODO: THIS IS RECONSTRUCTED AND MIGHT BE WRONG, CHECK!
                    s = dic['StepSize'][0]

                    f = np.arange(r[0], r[1], s)
                    f = np.append(f, np.array(r[1]))
                    dic['Nstep'] = len(f)
                    dic['KnobExpanded'] = [f.tolist()]
            else:
                # Scan values explicitly defined.
                if not isinstance(dic['ScanValues'], list):
                    raise ValueError('ScanValues is not given in the right fromat. '
                                     'Input dictionary %d.' % index)

                if len(dic['ScanValues']) != len(dic['Knob']) and len(dic['Knob']) != 1:
                    raise ValueError('The length of ScanValues does not meet to the number of Knobs.')

                if len(dic['Knob']) > 1:
                    minlen = 100000
                    for r in dic['ScanValues']:
                        if minlen > len(r):
                            minlen = len(r)
                    ran = []
                    for r in dic['ScanValues']:
                        ran.append(r[0:minlen])  # Cut at the length of the shortest list.
                    dic['KnobExpanded'] = ran
                    dic['Nstep'] = minlen
                else:
                    dic['KnobExpanded'] = [dic['ScanValues']]
                    dic['Nstep'] = len(dic['ScanValues'])
        else:  # Setting up scan values for Series scan
            if 'ScanValues' not in dic.keys():
                raise ValueError('ScanValues should be given for Series '
                                 'scan in the input dictionary %d.' % index)

            if not isinstance(dic['ScanValues'], list):
                raise ValueError('ScanValues should be given as a list (of lists) '
                                 'for Series scan in the input dictionary %d.' % index)

            if len(dic['Knob']) != len(dic['ScanValues']):
                raise ValueError('Scan values length does not match to the '
                                 'number of knobs in the input dictionary %d.' % index)

            Nstep = []
            for vl in dic['ScanValues']:
                if not isinstance(vl, list):
                    raise ValueError('ScanValue element should be given as a list for '
                                     'Series scan in the input dictionary %d.' % index)
                Nstep.append(len(vl))
            dic['Nstep'] = Nstep

    def _setup_pre_actions(self, index, dic):
        if 'PreAction' in dic.keys():
            if not isinstance(dic['PreAction'], list):
                raise ValueError('PreAction should be a list. Input dictionary %d.' % index)
            for l in dic['PreAction']:
                if not isinstance(l, list):
                    raise ValueError('Every PreAction should be a list. Input dictionary %d.' % index)
                if len(l) != 5:
                    if not l[0] == 'SpecialAction':
                        raise ValueError('Every PreAction should be in a form of '
                                         '[Ch-set, Ch-read, Value, Tolerance, Timeout]. '
                                         'Input dictionary ' + str(index) + '.')

            if 'PreActionWaiting' not in dic.keys():
                dic['PreActionWaiting'] = 0.0
            if not isinstance(dic['PreActionWaiting'], float) and not isinstance(dic['PreActionWaiting'], int):
                raise ValueError('PreActionWating should be a float. Input dictionary %d.' % index)

            if 'PreActionOrder' not in dic.keys():
                dic['PreActionOrder'] = [0] * len(dic['PreAction'])
            if not isinstance(dic['PreActionOrder'], list):
                raise ValueError('PreActionOrder should be a list. Input dictionary %d.' % index)

        else:
            dic['PreAction'] = []
            dic['PreActionWaiting'] = 0.0
            dic['PreActionOrder'] = [0] * len(dic['PreAction'])

    def _setup_inloop_pre_actions(self, index, dic):
        if 'In-loopPreAction' in dic.keys():
            if not isinstance(dic['In-loopPreAction'], list):
                raise ValueError('In-loopPreAction should be a list. Input dictionary %d.' % index)
            for l in dic['In-loopPreAction']:
                if not isinstance(l, list):
                    raise ValueError('Every In-loopPreAction should be a list. '
                                     'Input dictionary ' + str(index) + '.')
                if len(l) != 5:
                    if not l[0] == 'SpecialAction':
                        raise ValueError('Every In-loopPreAction should be in a form of '
                                         '[Ch-set, Ch-read, Value, Tolerance, Timeout]. '
                                         'Input dictionary ' + str(index) + '.')

            if 'In-loopPreActionWaiting' not in dic.keys():
                dic['In-loopPreActionWaiting'] = 0.0
            if not isinstance(dic['In-loopPreActionWaiting'], float) and not isinstance(
                    dic['In-loopPreActionWaiting'], int):
                raise ValueError('In-loopPreActionWating should be a float. Input dictionary %d.' % index)

            if 'In-loopPreActionOrder' not in dic.keys():
                dic['In-loopPreActionOrder'] = [0] * len(dic['In-loopPreAction'])
            if not isinstance(dic['In-loopPreActionOrder'], list):
                raise ValueError('In-loopPreActionOrder should be a list. Input dictionary %d.' % index)

        else:
            dic['In-loopPreAction'] = []
            dic['In-loopPreActionWaiting'] = 0.0
            dic['In-loopPreActionOrder'] = [0] * len(dic['In-loopPreAction'])

    def _setup_post_action(self, index, dic):
        if 'PostAction' in dic.keys():
            if dic['PostAction'] == 'Restore':
                PA = []
                for index in range(0, len(dic['Knob'])):
                    k = dic['Knob'][index]
                    v = dic['KnobSaved'][index]
                    PA.append([k, k, v, 1.0, 10])
                dic['PostAction'] = PA
            elif not isinstance(dic['PostAction'], list):
                raise ValueError('PostAction should be a list. Input dictionary %d.' % index)
            Restore = 0
            for index in range(0, len(dic['PostAction'])):
                l = dic['PostAction'][index]
                if l == 'Restore':
                    Restore = 1
                    PA = []
                    for j in range(0, len(dic['Knob'])):
                        k = dic['Knob'][j]
                        v = dic['KnobSaved'][j]
                        PA.append([k, k, v, 1.0, 10])
                elif not isinstance(l, list):
                    raise ValueError('Every PostAction should be a list. Input dictionary %d.' % index)
                elif len(l) != 5:
                    if not l[0] == 'SpecialAction':
                        raise ValueError('Every PostAction should be in a form of '
                                         '[Ch-set, Ch-read, Value, Tolerance, Timeout]. '
                                         'Input dictionary %d.' % index)
            if Restore:
                dic['PostAction'].remove('Restore')
                dic['PostAction'] = dic['PostAction'] + PA

        else:
            dic['PostAction'] = []

    def _setup_inloop_post_action(self, index, dic):
        if 'In-loopPostAction' in dic.keys():
            if dic['In-loopPostAction'] == 'Restore':
                PA = []
                for index in range(0, len(dic['Knob'])):
                    k = dic['Knob'][index]
                    v = dic['KnobSaved'][index]
                    PA.append([k, k, v, 1.0, 10])
                dic['In-loopPostAction'] = PA
            elif not isinstance(dic['In-loopPostAction'], list):
                raise ValueError('In-loopPostAction should be a list. Input dictionary %d.' % index)
            Restore = 0
            for index in range(0, len(dic['In-loopPostAction'])):
                l = dic['In-loopPostAction'][index]
                if l == 'Restore':
                    Restore = 1
                    PA = []
                    for j in range(0, len(dic['Knob'])):
                        k = dic['Knob'][j]
                        v = dic['KnobSaved'][j]
                        PA.append([k, k, v, 1.0, 10])
                    dic['In-loopPostAction'][index] = PA
                elif not isinstance(l, list):
                    raise ValueError('Every In-loopPostAction should be a list. '
                                     'Input dictionary %d.' % index)
                elif len(l) != 5:
                    raise ValueError('Every In-loopPostAction should be in a form of '
                                     '[Ch-set, Ch-read, Value, Tolerance, Timeout]. '
                                     'Input dictionary %d.' % index)
            if Restore:
                dic['In-loopPostAction'].remove('Restore')
                dic['In-loopPostAction'] = dic['In-loopPostAction'] + PA
        else:
            dic['In-loopPostAction'] = []

    def _setup_monitors(self, dic):
        if ('Monitor' in dic.keys()) and (dic['Monitor']):
            if isinstance(dic['Monitor'], str):
                dic['Monitor'] = [dic['Monitor']]

            # Initialize monitor group and check if all monitor PVs are valid.
            self.epics_dal.add_reader_group(MONITOR_GROUP, dic["Monitor"])

            if 'MonitorValue' not in dic.keys():
                dic["MonitorValue"] = self.epics_dal.get_group(MONITOR_GROUP).read()
            elif not isinstance(dic['MonitorValue'], list):
                dic['MonitorValue'] = [dic['MonitorValue']]
            if len(dic['MonitorValue']) != len(dic['Monitor']):
                raise ValueError('The length of MonitorValue does not meet to the length of Monitor.')

            # Try to construct the monitor tolerance, if not given.
            if 'MonitorTolerance' not in dic.keys():
                dic['MonitorTolerance'] = []
                for value in self.epics_dal.get_group(MONITOR_GROUP).read():
                    if isinstance(value, str):
                        # No tolerance for string values.
                        dic['MonitorTolerance'].append(None)
                    elif value == 0:
                        # Default tolerance for unknown values is 0.1.
                        dic['MonitorTolerance'].append(0.1)
                    else:
                        # 10% of the current value will be the torelance when not given
                        dic['MonitorTolerance'].append(abs(value * 0.1))

            elif not isinstance(dic['MonitorTolerance'], list):
                dic['MonitorTolerance'] = [dic['MonitorTolerance']]
            if len(dic['MonitorTolerance']) != len(dic['Monitor']):
                raise ValueError('The length of MonitorTolerance does not meet to the length of Monitor.')

            if 'MonitorAction' not in dic.keys():
                raise ValueError('MonitorAction is not give though Monitor is given.')

            if not isinstance(dic['MonitorAction'], list):
                dic['MonitorAction'] = [dic['MonitorAction']]
            for m in dic['MonitorAction']:
                if m != 'Abort' and m != 'Wait' and m != 'WaitAndAbort':
                    raise ValueError('MonitorAction shold be Wait, Abort, or WaitAndAbort.')

            if 'MonitorTimeout' not in dic.keys():
                dic['MonitorTimeout'] = [30.0] * len(dic['Monitor'])
            elif not isinstance(dic['MonitorTimeout'], list):
                dic['MonitorValue'] = [dic['MonitorValue']]
            if len(dic['MonitorValue']) != len(dic['Monitor']):
                raise ValueError('The length of MonitorValue does not meet to the length of Monitor.')
            for m in dic['MonitorTimeout']:
                try:
                    float(m)
                except:
                    raise ValueError('MonitorTimeout should be a list of float(or int).')

        else:
            dic['Monitor'] = []
            dic['MonitorValue'] = []
            dic['MonitorTolerance'] = []
            dic['MonitorAction'] = []
            dic['MonitorTimeout'] = []

    def startScan(self):
        if self.outdict['ErrorMessage']:
            if 'After the last scan,' not in self.outdict['ErrorMessage']:
                self.outdict['ErrorMessage'] = 'It seems that the initialization was not successful... ' \
                                               'No scan was performed.'
            return self.outdict

        # Execute the scan.
        self.outdict['TimeStampStart'] = datetime.now()
        self.execute_scan()
        self.outdict['TimeStampEnd'] = datetime.now()

        self.outdict['ErrorMessage'] = 'Measurement finalized (finished/aborted) normally. ' \
                                       'Need initialisation before next measurement.'

        # Cleanup after the scan.
        self.epics_dal.close_all_groups()

        return self.outdict
