from collections import namedtuple

from pyscan import config

EPICS_PV = namedtuple("EPICS_PV", ["identifier", "pv_name", "readback_pv_name", "tolerance", "readback_pv_value"])
EPICS_MONITOR = namedtuple("EPICS_MONITOR", ["identifier", "pv_name", "value", "action", "tolerance"])
BS_PROPERTY = namedtuple("BS_PROPERTY", ["identifier", "property"])
BS_MONITOR = namedtuple("BS_MONITOR", ["identifier", "property", "value", "action", "tolerance"])
SCAN_SETTINGS = namedtuple("SCAN_SETTINGS", ["measurement_interval", "n_measurements",
                                             "write_timeout", "settling_time", "progress_callback", "bs_read_filter"])


def epics_pv(pv_name, readback_pv_name=None, tolerance=None, readback_pv_value=None):
    """
    Construct a tuple for PV representation
    :param pv_name: Name of the PV.
    :param readback_pv_name: Name of the readback PV.
    :param tolerance: Tolerance if the PV is writable.
    :param readback_pv_value: If the readback_pv_value is set, the readback is compared against this instead of 
    comparing it to the setpoint.
    :return: Tuple of (identifier, pv_name, pv_readback, tolerance)
    """
    identifier = pv_name

    if not pv_name:
        raise ValueError("pv_name not specified.")

    if not readback_pv_name:
        readback_pv_name = pv_name

    if not tolerance or tolerance < config.max_float_tolerance:
        tolerance = config.max_float_tolerance

    return EPICS_PV(identifier, pv_name, readback_pv_name, tolerance, readback_pv_value)


def epics_monitor(pv_name, value, action=None, tolerance=None):
    """
    Construct a tuple for an epics monitor representation.
    :param pv_name: Name of the PV to monitor.
    :param value: Value we expect the PV to be in.
    :param action: What to do when the monitor fails ('Abort' and 'WaitAndAbort' supporteds)
    :param tolerance: Tolerance within which the monitor needs to be.
    :return: Tuple of ("pv_name", "value", "action", "tolerance", "timeout")
    """
    identifier = pv_name

    if not pv_name:
        raise ValueError("pv_name not specified.")

    if value is None:
        raise ValueError("pv value not specified.")

    # the default action is Abort.
    if not action:
        action = "Abort"

    if not tolerance or tolerance < config.max_float_tolerance:
        tolerance = config.max_float_tolerance

    return EPICS_MONITOR(identifier, pv_name, value, action, tolerance)


def bs_property(name):
    """
    Construct a tuple for bs read property representation.
    :param name: Complete property name.
    """
    identifier = name

    if not name:
        raise ValueError("name not specified.")

    return BS_PROPERTY(identifier, name)


def bs_monitor(name, value, tolerance=None):
    """
    Construct a tuple for bs monitor property representation.
    :param name: Complete property name.
    :param value: Expected value.
    :param tolerance: Tolerance within which the monitor needs to be.
    :return:  Tuple of ("property", "value", "action", "tolerance")
    """
    identifier = name

    if not name:
        raise ValueError("name not specified.")

    if value is None:
        raise ValueError("value not specified.")

    if not tolerance or tolerance < config.max_float_tolerance:
        tolerance = config.max_float_tolerance

    # We do not support other actions for BS monitors.
    action = "Abort"

    return BS_MONITOR(identifier, name, value, action, tolerance)


def scan_settings(measurement_interval=None, n_measurements=None, write_timeout=None, settling_time=None,
                  progress_callback=None, bs_read_filter=None):
    if not measurement_interval or measurement_interval < 0:
        measurement_interval = config.scan_default_measurement_interval

    if not n_measurements or n_measurements < 1:
        n_measurements = config.scan_default_n_measurements

    if not write_timeout or write_timeout < 0:
        write_timeout = config.epics_default_set_and_match_timeout

    if not settling_time or settling_time < 0:
        settling_time = config.epics_default_settling_time

    if not progress_callback:
        def default_progress_callback(current_position, total_positions):
            completed_percentage = 100.0 * (current_position / total_positions)
            print("Scan: %.2f %% completed (%d/%d)" % (completed_percentage, current_position, total_positions))

        progress_callback = default_progress_callback

    return SCAN_SETTINGS(measurement_interval, n_measurements, write_timeout, settling_time, progress_callback,
                         bs_read_filter)


def convert_input(input):
    """
    Convert any type of readable into appropriate named tuples.
    :param input: Readables input from the user.
    :return: Readables converted into named tuples.
    """
    converted_readables = []
    for readable in input:
        # Readable already of correct type.
        if isinstance(readable, (EPICS_PV, BS_PROPERTY)):
            converted_readables.append(readable)
        # We need to convert it.
        elif isinstance(readable, str):
            if "://" in readable:
                # Epics PV!
                if readable.lower().startswith("ca://"):
                    converted_readables.append(epics_pv(readable[5:]))
                # bs_read property.
                elif readable.lower().startswith("bs://"):
                    converted_readables.append(bs_property(readable[5:]))
                # A new protocol we don't know about?
                else:
                    raise ValueError("Readable %s uses an unexpected protocol. "
                                     "'ca://' and 'bs://' are supported." % readable)
            # No protocol specified, default is epics.
            else:
                converted_readables.append(epics_pv(readable))

        # Supported named tuples or string, we cannot interpret the rest.
        else:
            raise ValueError("Readable of unexpected type %s. %s" % (type(readable), readable))

    return converted_readables
