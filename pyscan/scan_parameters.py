from collections import namedtuple

from pyscan import config

EPICS_PV = namedtuple("EPICS_PV", ["identifier", "pv_name", "readback_pv_name", "tolerance", "readback_pv_value"])
EPICS_MONITOR = namedtuple("EPICS_MONITOR", ["identifier", "pv_name", "value", "action", "tolerance"])
BS_PROPERTY = namedtuple("BS_PROPERTY", ["identifier", "property", "default_value"])
BS_MONITOR = namedtuple("BS_MONITOR", ["identifier", "property", "value", "action", "tolerance", "default_value"])
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


def bs_property(name, default_value=Exception):
    """
    Construct a tuple for bs read property representation.
    :param name: Complete property name.
    :param default_value: The default value that is assigned to the property if it is missing.
    :return:  Tuple of ("identifier", "property", "default_value")
    """
    identifier = name

    if not name:
        raise ValueError("name not specified.")

    return BS_PROPERTY(identifier, name, default_value)


def bs_monitor(name, value, tolerance=None, default_value=Exception):
    """
    Construct a tuple for bs monitor property representation.
    :param name: Complete property name.
    :param value: Expected value.
    :param tolerance: Tolerance within which the monitor needs to be.
    :param default_value: Default value of a monitor, if not present in the bs stream.
    :return:  Tuple of ("identifier", "property", "value", "action", "tolerance", "default_value")
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

    return BS_MONITOR(identifier, name, value, action, tolerance, default_value)


def scan_settings(measurement_interval=None, n_measurements=None, write_timeout=None, settling_time=None,
                  progress_callback=None, bs_read_filter=None):
    """
    Set the scan settings.
    :param measurement_interval: Default 0. Interval between each measurement, in case n_measurements is more than 1.
    :param n_measurements: Default 1. How many measurements to make at each position.
    :param write_timeout: How much time to wait in seconds for set_and_match operations on epics PVs.
    :param settling_time: How much time to wait in seconds after the motors have reached the desired destination.
    :param progress_callback: Function to call after each scan step is completed. 
                              Signature: def callback(current_position, total_positions)
    :param bs_read_filter: Filter to apply to the bs read receive function, to filter incoming messages.
                              Signature: def callback(message)
    :return: Scan settings named tuple.
    """
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


def convert_input(input_parameters):
    """
    Convert any type of readable into appropriate named tuples.
    :param input_parameters: Readables input from the user.
    :return: Readables converted into named tuples.
    """
    converted_readables = []
    for input in input_parameters:
        # Readable already of correct type.
        if isinstance(input, (EPICS_PV, BS_PROPERTY)):
            converted_readables.append(input)
        # We need to convert it.
        elif isinstance(input, str):
            # Check if the string is valid.
            if not input:
                raise ValueError("Input cannot be an empty string.")

            if "://" in input:
                # Epics PV!
                if input.lower().startswith("ca://"):
                    converted_readables.append(epics_pv(input[5:]))
                # bs_read property.
                elif input.lower().startswith("bs://"):
                    converted_readables.append(bs_property(input[5:]))
                # A new protocol we don't know about?
                else:
                    raise ValueError("Readable %s uses an unexpected protocol. "
                                     "'ca://' and 'bs://' are supported." % input)
            # No protocol specified, default is epics.
            else:
                converted_readables.append(epics_pv(input))

        # Supported named tuples or string, we cannot interpret the rest.
        else:
            raise ValueError("Input of unexpected type %s. Value: '%s'." % (type(input), input))

    return converted_readables
