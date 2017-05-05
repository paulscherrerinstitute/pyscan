from pyscan.dal import epics_dal, bsread_dal
from pyscan.scanner import Scanner
from pyscan.scan_parameters import EPICS_PV, EPICS_MONITOR, BS_PROPERTY, BS_MONITOR
from pyscan.utils import convert_to_list, SimpleDataProcessor, ActionExecutor, compare_channel_value

# Instances to use.
EPICS_WRITER = epics_dal.WriteGroupInterface
EPICS_READER = epics_dal.ReadGroupInterface
BS_READER = bsread_dal.ReadGroupInterface
DATA_PROCESSOR = SimpleDataProcessor


def scan(positioner, writables, readables, monitors=None, initializations=None, finalization=None, settings=None):
    # Allow a list or a single value to be passed.
    writables = convert_to_list(writables) or []
    readables = convert_to_list(readables) or []
    monitors = convert_to_list(monitors) or []
    initializations = convert_to_list(initializations) or []
    finalization = convert_to_list(finalization) or []

    bs_reader = _initialize_bs_dal(readables, monitors)
    epics_writer, epics_pv_reader, epics_monitor_reader = _initialize_epics_dal(writables,
                                                                                readables,
                                                                                monitors,
                                                                                settings)

    # Order of value sources, needed to reconstruct the correct order of the result.
    readables_order = [type(readable) for readable in readables]

    # Read function needs to merge both BS and PV data.
    def read_data():
        bs_values = iter(bs_reader.read() if bs_reader else [])
        epics_values = iter(epics_pv_reader.read() if epics_pv_reader else [])

        # Interleave the values correctly.
        result = []
        for source in readables_order:
            next_result = next(bs_values) if source == BS_PROPERTY else next(epics_values)

            # We flatten the result, whenever possible.
            if isinstance(next_result, list):
                result.extend(next_result)
            else:
                result.append(next_result)

        return result

    # Order of value sources, needed to reconstruct the correct order of the result.
    monitor_order = [type(monitor) for monitor in monitors]

    # Validate function needs to validate both BS and PV data.
    def validate_data(current_position, data):
        bs_values = iter(bs_reader.read_cached_monitors() if bs_reader else [])
        epics_values = iter(epics_monitor_reader.read() if epics_monitor_reader else [])

        for index, value_source in enumerate(monitor_order):
            value = next(bs_values) if value_source == BS_MONITOR else next(epics_values)
            expected_value = monitors[index].value
            tolerance = monitors[index].tolerance

            if not compare_channel_value(value, expected_value, tolerance):
                # TODO: The "wait" part of WaitAndAbort does not work.. do we need it?
                raise ValueError("Monitor %s, expected value %s, actual value %s, tolerance %s." %
                                 (monitors[index].identifier, expected_value, value, tolerance))
        return True

    initialization_executor = None
    if initializations:
        initialization_executor = ActionExecutor(initializations).execute

    finalization_executor = None
    if finalization:
        finalization_executor = ActionExecutor(finalization).execute

    scanner = Scanner(positioner=positioner,
                      writer=epics_writer.set_and_match,
                      data_processor=DATA_PROCESSOR(),
                      reader=read_data,
                      data_validator=validate_data,
                      initialization_executor=initialization_executor,
                      finalization_executor=finalization_executor)

    return scanner.discrete_scan(settings.settling_time)


def _initialize_epics_dal(writables, readables, monitors, settings):
    # We support only epics_pv writables.
    if not all((isinstance(x, EPICS_PV) for x in writables)):
        raise ValueError("Only EPICS_PV can be used as writables.")

    epics_readables_pv_names = [x.pv_name for x in filter(lambda x: isinstance(x, EPICS_PV), readables)]
    epics_monitors_pv_names = [x.pv_name for x in filter(lambda x: isinstance(x, EPICS_MONITOR), monitors)]

    # Instantiate the PVs to move the motors.
    epics_writer = EPICS_WRITER(pv_names=[pv.pv_name for pv in writables],
                                readback_pv_names=[pv.readback_pv_name for pv in writables],
                                tolerances=[pv.tolerance for pv in writables],
                                timeout=settings.write_timeout)

    # Reading epics PV values.
    epics_pv_reader = None
    if epics_readables_pv_names:
        epics_pv_reader = EPICS_READER(pv_names=epics_readables_pv_names,
                                       n_measurements=settings.n_measurements,
                                       waiting=settings.measurement_interval)

    # Reading epics monitor values.
    epics_monitor_reader = None
    if epics_monitors_pv_names:
        epics_monitor_reader = EPICS_READER(pv_names=epics_monitors_pv_names,
                                            n_measurements=1,
                                            waiting=0)

    return epics_writer, epics_pv_reader, epics_monitor_reader


def _initialize_bs_dal(readables, monitors):
    bs_readables = [x.identifier for x in filter(lambda x: isinstance(x, BS_PROPERTY), readables)]
    bs_monitors = [x.identifier for x in filter(lambda x: isinstance(x, BS_MONITOR), monitors)]

    bs_reader = None
    if bs_readables or bs_monitors:
        bs_reader = BS_READER(properties=bs_readables, monitor_properties=bs_monitors)

    return bs_reader
