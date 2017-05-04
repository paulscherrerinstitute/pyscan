from collections import namedtuple

from pyscan.epics_dal import default_read_write_timeout
from pyscan.utils import minimum_tolerance

EPICS_PV = namedtuple("EPICS_PV", ["pv_name", "readback_pv_name", "tolerance"])
EPICS_MONITOR = namedtuple("EPICS_MONITOR", ["pv_name", "value", "action", "tolerance", "timeout"])
BS_PROPERTY = namedtuple("BS_PROPERTY", ["camera", "property"])
BS_MONITOR = namedtuple("BS_MONITOR", ["camera", "property", "value", "tolerance"])
SET_EPICS_PV = namedtuple("SET_EPICS_PV", ["pv_name", "value", "readback_pv_name", "tolerance", "timeout"])
RESTORE_WRITABLE_PVS = namedtuple("RESTORE_WRITABLE_PVS")
SCAN_SETTINGS = namedtuple("SCAN_SETTINGS", ["measurement_interval", "n_measurements",
                                             "write_timeout", "settling_time"])


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

    if not tolerance or tolerance < minimum_tolerance:
        tolerance = minimum_tolerance

    return EPICS_PV(pv_name, readback_pv_name, tolerance)


def epics_monitor(pv_name, value, action=None, tolerance=None, timeout=None):
    """
    Construct a tuple for an epics monitor representation.
    :param pv_name: Name of the PV to monitor.
    :param value: Value we expect the PV to be in.
    :param action: What to do when the monitor fails ('Abort' and 'WaitAndAbort' supporteds)
    :param tolerance: Tolerance within which the monitor needs to be.
    :param timeout: Timeout before the WaitAndAbort monitor aborts the scan.
    :return: Tuple of ("pv_name", "value", "action", "tolerance", "timeout")
    """

    if not pv_name:
        raise ValueError("pv_name not specified.")

    if not value:
        raise ValueError("pv value not specified.")

    # the default action is Abort.
    if not action:
        action = "Abort"

    if not tolerance or tolerance < minimum_tolerance:
        tolerance = minimum_tolerance

    if not timeout or timeout < 0:
        timeout = default_read_write_timeout

    return EPICS_MONITOR(pv_name, value, action, tolerance, timeout)


def bs_property(name):
    """
    Construct a tuple for bs read property representation.
    :param name: Complete property name.
    """
    if not name:
        raise ValueError("name not specified.")

    if not name.count(":") == 2:
        raise ValueError("Property name needs to be in format 'camera_name:property_name', but %s was provided" % name)

    camera_name, property_name = name.split(":")
    return BS_PROPERTY(camera_name, property_name)


def bs_monitor(name, value, tolerance=None):
    """
    Construct a tuple for bs monitor property representation.
    :param name: Complete property name.
    :param value: Expected value.
    :param tolerance: Tolerance within which the monitor needs to be.
    :return:  Tuple of ("camera", "property", "value", "action", "tolerance")
    """
    if not name:
        raise ValueError("name not specified.")

    if not name.count(":") == 2:
        raise ValueError("Property name needs to be in format 'camera_name:property_name', but %s was provided" % name)

    if not value:
        raise ValueError("value not specified.")

    if not tolerance or tolerance < minimum_tolerance:
        tolerance = minimum_tolerance

    camera_name, property_name = name.split(":")

    return BS_MONITOR(camera_name, property_name, value, tolerance)


def action_set_epics_pv(pv_name, value, readback_pv_name=None, tolerance=None, timeout=None):
    """
    Construct a tuple for set PV representation.
    :param pv_name: Name of the PV.
    :param value: Value to set the PV to.
    :param readback_pv_name: Name of the readback PV.
    :param tolerance: Tolerance if the PV is writable.
    :param timeout: Timeout for setting the pv value.
    :return: Tuple of (pv_name, pv_readback, tolerance)
    """
    pv_name, readback_pv_name, tolerance = epics_pv(pv_name, readback_pv_name, tolerance)

    if not value:
        raise ValueError("pv value not specified.")

    if not timeout or timeout < 0:
        timeout = default_read_write_timeout

    return SET_EPICS_PV(pv_name, value, readback_pv_name, tolerance, timeout)


def action_restore():
    """
    Restore the initial state of the writable PVs.
    :return: Empty tuple, to be replaced with the initial values.
    """
    return RESTORE_WRITABLE_PVS()


def scan_settings(measurement_interval=None, n_measurements=None, write_timeout=None, settling_time=None):
    if not measurement_interval or measurement_interval < 0:
        measurement_interval = 0

    if not n_measurements or n_measurements < 1:
        n_measurements = 1

    if not write_timeout or write_timeout < 0:
        write_timeout = default_read_write_timeout

    if not settling_time or settling_time < 0:
        settling_time = 0

    return SCAN_SETTINGS(measurement_interval, n_measurements, write_timeout, settling_time)