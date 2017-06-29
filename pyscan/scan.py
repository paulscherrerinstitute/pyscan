from pyscan.dal import epics_dal, bsread_dal, function_dal
from pyscan.dal.function_dal import FunctionProxy
from pyscan.scanner import Scanner
from pyscan.scan_parameters import EPICS_PV, EPICS_MONITOR, BS_PROPERTY, BS_MONITOR, scan_settings, convert_input, \
    FUNCTION_VALUE
from pyscan.utils import convert_to_list, SimpleDataProcessor, ActionExecutor, compare_channel_value

# Instances to use.
EPICS_WRITER = epics_dal.WriteGroupInterface
EPICS_READER = epics_dal.ReadGroupInterface
BS_READER = bsread_dal.ReadGroupInterface
FUNCTION_PROXY = function_dal.FunctionProxy
DATA_PROCESSOR = SimpleDataProcessor
ACTION_EXECUTOR = ActionExecutor


def scan(positioner, readables, writables=None, monitors=None, before_read=None, after_read=None, initialization=None,
         finalization=None, settings=None, data_processor=None):
    # Initialize the scanner instance.
    scanner_instance = scanner(positioner, readables, writables, monitors, before_read, after_read, initialization,
                               finalization, settings, data_processor)

    return scanner_instance.discrete_scan()


def scanner(positioner, readables, writables=None, monitors=None, before_read=None, after_read=None,
            initialization=None, finalization=None, settings=None, data_processor=None):

    # Allow a list or a single value to be passed. Initialize None values.
    writables = convert_input(convert_to_list(writables) or [])
    readables = convert_input(convert_to_list(readables) or [])
    monitors = convert_to_list(monitors) or []
    before_read = convert_to_list(before_read) or []
    after_read = convert_to_list(after_read) or []
    initialization = convert_to_list(initialization) or []
    finalization = convert_to_list(finalization) or []
    settings = settings or scan_settings()

    bs_reader = _initialize_bs_dal(readables, monitors, settings.bs_read_filter)
    epics_writer, epics_pv_reader, epics_monitor_reader = _initialize_epics_dal(writables,
                                                                                readables,
                                                                                monitors,
                                                                                settings)
    function_writer, function_reader, function_monitor = _initialize_function_dal(writables,
                                                                                  readables,
                                                                                  monitors)

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
    def read_data():
        bs_values = iter(bs_reader.read() if bs_reader else [])
        epics_values = iter(epics_pv_reader.read() if epics_pv_reader else [])
        function_values = iter(function_reader.read() if function_reader else [])

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
    monitor_order = [type(monitor) for monitor in monitors]

    # Validate function needs to validate both BS, PV, and function proxy data.
    def validate_data(current_position, data):
        bs_values = iter(bs_reader.read_cached_monitors() if bs_reader else [])
        epics_values = iter(epics_monitor_reader.read() if epics_monitor_reader else [])
        function_values = iter(function_monitor.read() if function_monitor else [])

        for index, source in enumerate(monitor_order):
            if source == BS_MONITOR:
                value = next(bs_values)
            elif source == EPICS_MONITOR:
                value = next(epics_values)
            elif source == FUNCTION_VALUE:
                value = next(function_values)
            else:
                raise ValueError("Unknown type of readable %s used." % source)

            # Function monitors are self contained.
            if source == FUNCTION_VALUE:
                if not value:
                    raise ValueError("Function monitor %s returned False." % monitors[index].identifier)
            else:
                expected_value = monitors[index].value
                tolerance = monitors[index].tolerance

                if not compare_channel_value(value, expected_value, tolerance):
                    raise ValueError("Monitor %s, expected value %s, actual value %s, tolerance %s." %
                                     (monitors[index].identifier, expected_value, value, tolerance))

        return True

    if not data_processor:
        data_processor = DATA_PROCESSOR()

    # Before acquisition hook.
    before_executor = None
    if before_read:
        before_executor = ACTION_EXECUTOR(before_read).execute

    # After acquisition hook.
    after_executor = None
    if after_read:
        after_executor = ACTION_EXECUTOR(after_read).execute

    # Initialization (before move to first position) hook.
    initialization_executor = None
    if initialization:
        initialization_executor = ACTION_EXECUTOR(initialization).execute

    # Finalization (after last acquisition AND on error) hook.
    finalization_executor = None
    if finalization:
        finalization_executor = ACTION_EXECUTOR(finalization).execute

    scanner = Scanner(positioner=positioner, data_processor=data_processor, reader=read_data,
                      writer=write_data, before_executor=before_executor,
                      after_executor=after_executor, initialization_executor=initialization_executor,
                      finalization_executor=finalization_executor, data_validator=validate_data, settings=settings)

    return scanner


def _initialize_epics_dal(writables, readables, monitors, settings):
    epics_writer = None
    if writables:
        epics_writables = [x for x in writables if isinstance(x, EPICS_PV)]
        if epics_writables:
            # Instantiate the PVs to move the motors.
            epics_writer = EPICS_WRITER(pv_names=[pv.pv_name for pv in writables],
                                        readback_pv_names=[pv.readback_pv_name for pv in writables],
                                        tolerances=[pv.tolerance for pv in writables],
                                        timeout=settings.write_timeout)

    epics_readables_pv_names = [x.pv_name for x in filter(lambda x: isinstance(x, EPICS_PV), readables)]
    epics_monitors_pv_names = [x.pv_name for x in filter(lambda x: isinstance(x, EPICS_MONITOR), monitors)]

    # Reading epics PV values.
    epics_pv_reader = None
    if epics_readables_pv_names:
        epics_pv_reader = EPICS_READER(pv_names=epics_readables_pv_names)

    # Reading epics monitor values.
    epics_monitor_reader = None
    if epics_monitors_pv_names:
        epics_monitor_reader = EPICS_READER(pv_names=epics_monitors_pv_names)

    return epics_writer, epics_pv_reader, epics_monitor_reader


def _initialize_bs_dal(readables, monitors, filter_function):
    bs_readables = [x for x in filter(lambda x: isinstance(x, BS_PROPERTY), readables)]
    bs_monitors = [x for x in filter(lambda x: isinstance(x, BS_MONITOR), monitors)]

    bs_reader = None
    if bs_readables or bs_monitors:
        bs_reader = BS_READER(properties=bs_readables, monitors=bs_monitors, filter_function=filter_function)

    return bs_reader


def _initialize_function_dal(writables, readables, monitors):
    function_writer = FunctionProxy([x for x in writables if isinstance(x, FUNCTION_VALUE)])
    function_reader = FunctionProxy([x for x in readables if isinstance(x, FUNCTION_VALUE)])
    function_monitor = FunctionProxy([x for x in monitors if isinstance(x, FUNCTION_VALUE)])

    return function_writer, function_reader, function_monitor
