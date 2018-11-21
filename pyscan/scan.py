import logging

from pyscan.dal import epics_dal, bsread_dal, function_dal
from pyscan.dal.function_dal import FunctionProxy
from pyscan.positioner.bsread import BsreadPositioner
from pyscan.scanner import Scanner
from pyscan.scan_parameters import EPICS_PV, EPICS_CONDITION, BS_PROPERTY, BS_CONDITION, scan_settings, convert_input, \
    FUNCTION_VALUE, FUNCTION_CONDITION, convert_conditions, ConditionAction, ConditionComparison
from pyscan.utils import convert_to_list, SimpleDataProcessor, ActionExecutor, compare_channel_value

# Instances to use.
EPICS_WRITER = epics_dal.WriteGroupInterface
EPICS_READER = epics_dal.ReadGroupInterface
BS_READER = bsread_dal.ReadGroupInterface
FUNCTION_PROXY = function_dal.FunctionProxy
DATA_PROCESSOR = SimpleDataProcessor
ACTION_EXECUTOR = ActionExecutor

_logger = logging.getLogger(__name__)


def scan(positioner, readables, writables=None, conditions=None, before_read=None, after_read=None, initialization=None,
         finalization=None, settings=None, data_processor=None, before_move=None, after_move=None):
    # Initialize the scanner instance.
    scanner_instance = scanner(positioner, readables, writables, conditions, before_read, after_read, initialization,
                               finalization, settings, data_processor, before_move, after_move)

    return scanner_instance.discrete_scan()


def scanner(positioner, readables, writables=None, conditions=None, before_read=None, after_read=None,
            initialization=None, finalization=None, settings=None, data_processor=None,
            before_move=None, after_move=None):
    # Allow a list or a single value to be passed. Initialize None values.
    writables = convert_input(convert_to_list(writables) or [])
    readables = convert_input(convert_to_list(readables) or [])
    conditions = convert_conditions(convert_to_list(conditions) or [])
    before_read = convert_to_list(before_read) or []
    after_read = convert_to_list(after_read) or []
    before_move = convert_to_list(before_move) or []
    after_move = convert_to_list(after_move) or []
    initialization = convert_to_list(initialization) or []
    finalization = convert_to_list(finalization) or []
    settings = settings or scan_settings()

    # TODO: Ugly. The scanner should not depend on a particular positioner implementation.
    if isinstance(positioner, BsreadPositioner) and settings.n_measurements > 1:
        raise ValueError("When using BsreadPositioner the maximum number of n_measurements = 1.")

    bs_reader = _initialize_bs_dal(readables, conditions, settings.bs_read_filter, positioner)

    epics_writer, epics_pv_reader, epics_condition_reader = _initialize_epics_dal(writables,
                                                                                  readables,
                                                                                  conditions,
                                                                                  settings)

    function_writer, function_reader, function_condition = _initialize_function_dal(writables,
                                                                                    readables,
                                                                                    conditions)

    writables_order = [type(writable) for writable in writables]

    # Write function needs to merge PV and function proxy data.
    def write_data(positions):
        positions = convert_to_list(positions)
        pv_values = [x for x, source in zip(positions, writables_order) if source == EPICS_PV]
        function_values = [x for x, source in zip(positions, writables_order) if source == FUNCTION_VALUE]

        if epics_writer:
            epics_writer.set_and_match(pv_values)

        if function_writer:
            function_writer.write(function_values)

    # Order of value sources, needed to reconstruct the correct order of the result.
    readables_order = [type(readable) for readable in readables]

    # Read function needs to merge BS, PV, and function proxy data.
    def read_data(current_position_index, retry=False):
        _logger.debug("Reading data for position index %s." % current_position_index)

        bs_values = iter(bs_reader.read(current_position_index, retry) if bs_reader else [])
        epics_values = iter(epics_pv_reader.read(current_position_index) if epics_pv_reader else [])
        function_values = iter(function_reader.read(current_position_index) if function_reader else [])

        # Interleave the values correctly.
        result = []
        for source in readables_order:
            if source == BS_PROPERTY:
                next_result = next(bs_values)
            elif source == EPICS_PV:
                next_result = next(epics_values)
            elif source == FUNCTION_VALUE:
                next_result = next(function_values)
            else:
                raise ValueError("Unknown type of readable %s used." % source)

            # We flatten the result, whenever possible.
            if isinstance(next_result, list) and source != FUNCTION_VALUE:
                result.extend(next_result)
            else:
                result.append(next_result)

        return result

    # Order of value sources, needed to reconstruct the correct order of the result.
    conditions_order = [type(condition) for condition in conditions]

    # Validate function needs to validate both BS, PV, and function proxy data.
    def validate_data(current_position_index, data):
        _logger.debug("Reading data for position index %s." % current_position_index)

        bs_values = iter(bs_reader.read_cached_conditions() if bs_reader else [])
        epics_values = iter(epics_condition_reader.read(current_position_index) if epics_condition_reader else [])
        function_values = iter(function_condition.read(current_position_index) if function_condition else [])

        for index, source in enumerate(conditions_order):
            operation = ConditionComparison.EQUAL

            if source == BS_CONDITION:
                value = next(bs_values)
                operation = conditions[index].operation
            elif source == EPICS_CONDITION:
                value = next(epics_values)
            elif source == FUNCTION_CONDITION:
                value = next(function_values)
            else:
                raise ValueError("Unknown type of condition %s used." % source)

            value_valid = False

            # Function conditions are self contained.
            if source == FUNCTION_CONDITION:
                if value:
                    value_valid = True

            else:
                expected_value = conditions[index].value
                tolerance = conditions[index].tolerance

                if compare_channel_value(value, expected_value, tolerance, operation):
                    value_valid = True

            if not value_valid:

                if conditions[index].action == ConditionAction.Retry:
                    return False

                if source == FUNCTION_CONDITION:
                    raise ValueError("Function condition %s returned False." % conditions[index].identifier)

                else:
                    raise ValueError("Condition %s, expected value %s, actual value %s, tolerance %s." %
                                             (conditions[index].identifier,
                                              conditions[index].value,
                                              value,
                                              conditions[index].tolerance))

        return True

    if not data_processor:
        data_processor = DATA_PROCESSOR()

    # Before acquisition hook.
    before_measurement_executor = None
    if before_read:
        before_measurement_executor = ACTION_EXECUTOR(before_read).execute

    # After acquisition hook.
    after_measurement_executor = None
    if after_read:
        after_measurement_executor = ACTION_EXECUTOR(after_read).execute

    # Executor before each move.
    before_move_executor = None
    if before_move:
        before_move_executor = ACTION_EXECUTOR(before_move).execute

    # Executor after each move.
    after_move_executor = None
    if after_move:
        after_move_executor = ACTION_EXECUTOR(after_move).execute

    # Initialization (before move to first position) hook.
    initialization_executor = None
    if initialization:
        initialization_executor = ACTION_EXECUTOR(initialization).execute

    # Finalization (after last acquisition AND on error) hook.
    finalization_executor = None
    if finalization:
        finalization_executor = ACTION_EXECUTOR(finalization).execute

    scanner = Scanner(positioner=positioner, data_processor=data_processor, reader=read_data,
                      writer=write_data, before_measurement_executor=before_measurement_executor,
                      after_measurement_executor=after_measurement_executor,
                      initialization_executor=initialization_executor,
                      finalization_executor=finalization_executor, data_validator=validate_data, settings=settings,
                      before_move_executor=before_move_executor, after_move_executor=after_move_executor)

    return scanner


def _initialize_epics_dal(writables, readables, conditions, settings):
    epics_writer = None
    if writables:
        epics_writables = [x for x in writables if isinstance(x, EPICS_PV)]
        if epics_writables:
            # Instantiate the PVs to move the motors.
            epics_writer = EPICS_WRITER(pv_names=[pv.pv_name for pv in epics_writables],
                                        readback_pv_names=[pv.readback_pv_name for pv in epics_writables],
                                        tolerances=[pv.tolerance for pv in epics_writables],
                                        timeout=settings.write_timeout)

    epics_readables_pv_names = [x.pv_name for x in filter(lambda x: isinstance(x, EPICS_PV), readables)]
    epics_conditions_pv_names = [x.pv_name for x in filter(lambda x: isinstance(x, EPICS_CONDITION), conditions)]

    # Reading epics PV values.
    epics_pv_reader = None
    if epics_readables_pv_names:
        epics_pv_reader = EPICS_READER(pv_names=epics_readables_pv_names)

    # Reading epics condition values.
    epics_condition_reader = None
    if epics_conditions_pv_names:
        epics_condition_reader = EPICS_READER(pv_names=epics_conditions_pv_names)

    return epics_writer, epics_pv_reader, epics_condition_reader


def _initialize_bs_dal(readables, conditions, filter_function, positioner):
    bs_readables = [x for x in filter(lambda x: isinstance(x, BS_PROPERTY), readables)]
    bs_conditions = [x for x in filter(lambda x: isinstance(x, BS_CONDITION), conditions)]

    bs_reader = None
    if bs_readables or bs_conditions:

        # TODO: The scanner should not depend on a particular positioner. Refactor.
        if isinstance(positioner, BsreadPositioner):
            bs_reader = bsread_dal.ImmediateReadGroupInterface(properties=bs_readables,
                                                               conditions=bs_conditions,
                                                               filter_function=filter_function)

            positioner.set_bs_reader(bs_reader)

            return bs_reader

        else:
            bs_reader = BS_READER(properties=bs_readables, conditions=bs_conditions, filter_function=filter_function)

    return bs_reader


def _initialize_function_dal(writables, readables, conditions):
    function_writer = FunctionProxy([x for x in writables if isinstance(x, FUNCTION_VALUE)])
    function_reader = FunctionProxy([x for x in readables if isinstance(x, FUNCTION_VALUE)])
    function_condition = FunctionProxy([x for x in conditions if isinstance(x, FUNCTION_CONDITION)])

    return function_writer, function_reader, function_condition
