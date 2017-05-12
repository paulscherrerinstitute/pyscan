from collections import namedtuple

from pyscan import config

EPICS_PV = namedtuple("EPICS_PV", ["pv_name", "readback_pv_name", "tolerance"])
EPICS_MONITOR = namedtuple("EPICS_MONITOR", ["identifier", "pv_name", "value", "action", "tolerance"])
BS_PROPERTY = namedtuple("BS_PROPERTY", ["identifier", "camera", "property"])
BS_MONITOR = namedtuple("BS_MONITOR", ["identifier", "camera", "property", "value", "action", "tolerance"])
SCAN_SETTINGS = namedtuple("SCAN_SETTINGS", ["measurement_interval", "n_measurements",
                                             "write_timeout", "settling_time", "progress_callback"])


def epics_pv(pv_name, readback_pv_name=None, tolerance=None):
    """
    Construct a tuple for PV representation
    :param pv_name: Name of the PV.
    :param readback_pv_name: Name of the readback PV.
    :param tolerance: Tolerance if the PV is writable.
    :return: Tuple of (pv_name, pv_readback, tolerance)
    """

    if not pv_name:
        raise ValueError("pv_name not specified.")

    if not readback_pv_name:
        readback_pv_name = pv_name

    if not tolerance or tolerance < config.min_tolerance:
        tolerance = config.min_tolerance

    return EPICS_PV(pv_name, readback_pv_name, tolerance)


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

    if not tolerance or tolerance < config.min_tolerance:
        tolerance = config.min_tolerance

    return EPICS_MONITOR(identifier, pv_name, value, action, tolerance)


def bs_property(name):
    """
    Construct a tuple for bs read property representation.
    :param name: Complete property name.
    """
    identifier = name

    if not name:
        raise ValueError("name not specified.")

    if not name.count(":") == 1:
        raise ValueError("Property name needs to be in format 'camera_name:property_name', but %s was provided" % name)

    camera_name, property_name = name.split(":")
    return BS_PROPERTY(identifier, camera_name, property_name)


def bs_monitor(name, value, tolerance=None):
    """
    Construct a tuple for bs monitor property representation.
    :param name: Complete property name.
    :param value: Expected value.
    :param tolerance: Tolerance within which the monitor needs to be.
    :return:  Tuple of ("camera", "property", "value", "action", "tolerance")
    """
    identifier = name

    if not name:
        raise ValueError("name not specified.")

    if not name.count(":") == 1:
        raise ValueError("Property name needs to be in format 'camera_name:property_name', but %s was provided" % name)

    if value is None:
        raise ValueError("value not specified.")

    if not tolerance or tolerance < config.min_tolerance:
        tolerance = config.min_tolerance

    # We do not support other actions for BS monitors.
    action = "Abort"

    camera_name, property_name = name.split(":")

    return BS_MONITOR(identifier, camera_name, property_name, value, action, tolerance)


def scan_settings(measurement_interval=None, n_measurements=None, write_timeout=None, settling_time=None,
                  progress_callback=None):
    if not measurement_interval or measurement_interval < 0:
        measurement_interval = 0

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

    return SCAN_SETTINGS(measurement_interval, n_measurements, write_timeout, settling_time, progress_callback)
