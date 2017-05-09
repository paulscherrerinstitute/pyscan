from collections import namedtuple

from pyscan.config import epics_default_read_write_timeout, EPICS_WRITER, EPICS_READER
from pyscan.scan_parameters import epics_pv
from pyscan.utils import convert_to_list

SET_EPICS_PV = namedtuple("SET_EPICS_PV", ["pv_name", "value", "readback_pv_name", "tolerance", "timeout"])
RESTORE_WRITABLE_PVS = namedtuple("RESTORE_WRITABLE_PVS", [])


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

    if value is None:
        raise ValueError("pv value not specified.")

    if not timeout or timeout < 0:
        timeout = epics_default_read_write_timeout

    def execute():
        writer = EPICS_WRITER(pv_name, readback_pv_name, tolerance, timeout)
        writer.set_and_match(value)
        writer.close()

    return execute


def action_restore(pv_names):
    """
    Restore the initial state of the writable PVs.
    :return: Empty tuple, to be replaced with the initial values.
    """
    pv_names = convert_to_list(pv_names)

    reader = EPICS_READER(pv_names)
    current_values = reader.read()
    reader.close()

    def execute():
        print("restore %s" % pv_names)

    return execute
