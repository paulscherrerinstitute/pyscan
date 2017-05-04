from pyscan.dal import epics_dal, bsread_dal
from pyscan.scanner import Scanner
from pyscan.scan_parameters import EPICS_PV, EPICS_MONITOR, BS_PROPERTY, BS_MONITOR
from pyscan.utils import convert_to_list, SimpleDataProcessor, SimpleExecutor


def scan(positioner, writables, readables, monitors=None, initializations=None, finalizations=None, settings=None):
    # Allow a list or a single value to be passed.
    writables = convert_to_list(writables) or []
    readables = convert_to_list(readables) or []
    monitors = convert_to_list(monitors) or []
    initializations = convert_to_list(initializations) or []
    finalizations = convert_to_list(finalizations) or []

    bs_reader = _initialize_bs_dal(readables, monitors)
    epics_writer, epics_pv_reader, epics_monitor_reader = _initialize_epics_dal(writables,
                                                                                readables,
                                                                                monitors,
                                                                                settings)
    # Read and validate functions need to merge both BS and PV data.
    def read_data():
        bs_values = bs_reader.read() if bs_reader else []
        epics_values = epics_pv_reader.read() if epics_pv_reader else []
        # TODO: Interleave the values as they should be.
        return bs_values + epics_values

    def validate_data(current_position, data):
        bs_values = bs_reader.read_cached_monitors() if bs_reader else []
        epics_values = epics_monitor_reader.read() if epics_monitor_reader else []
        # TODO: Actually validate something with compare_channel_value.
        return True

    initialization_executor = None
    if initializations:
        initialization_executor = SimpleExecutor(initializations)

    finalization_executor = None
    if finalizations:
        finalization_executor = SimpleExecutor(finalizations)

    scanner = Scanner(positioner=positioner,
                      writer=epics_writer.set_and_match,
                      data_processor=SimpleDataProcessor(),
                      reader=read_data,
                      data_validator=validate_data,
                      initialization_executor=initialization_executor,
                      finalization_executor=finalization_executor)

    return scanner.discrete_scan(settings.settling_time)


def _initialize_epics_dal(writables, readables, monitors, settings):
    # We support only epics_pv writables.
    if not all((isinstance(x, EPICS_PV) for x in writables)):
        raise ValueError("Only EPICS_PV can be used as writables.")

    epics_readables = filter(lambda x: isinstance(x, EPICS_PV), readables)
    epics_monitors = filter(lambda x: isinstance(x, EPICS_MONITOR), monitors)

    # Instantiate the PVs to move the motors.
    epics_writer = epics_dal.WriteGroupInterface(pv_names=[pv.pv_name for pv in writables],
                                                 readback_pv_names=[pv.readback_pv_name for pv in writables],
                                                 tolerances=[pv.tolerance for pv in writables],
                                                 timeout=settings.write_timeout)

    # Reading epics PV values.
    epics_pv_reader = None
    if epics_readables:
        epics_pv_reader = epics_dal.ReadGroupInterface(pv_names=[pv.pv_name for pv in epics_readables],
                                                       n_measurements=settings.n_measurements,
                                                       waiting=settings.measurement_interval)

    # Reading epics monitor values.
    epics_monitor_reader = None
    if epics_monitors:
        epics_monitor_reader = epics_dal.ReadGroupInterface(pv_names=[pv.pv_name for pv in epics_monitors],
                                                            n_measurements=1,
                                                            waiting=0)

    return epics_writer, epics_pv_reader, epics_monitor_reader


def _initialize_bs_dal(readables, monitors):
    bs_readables = filter(lambda x: isinstance(x, BS_PROPERTY), readables)
    bs_monitors = filter(lambda x: isinstance(x, BS_MONITOR), monitors)

    bs_reader = None
    if bs_readables or bs_monitors:
        bs_reader = bsread_dal.ReadGroupInterface(properties=bs_readables,
                                                  monitor_properties=bs_monitors)

    return bs_reader
