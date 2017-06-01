from collections import namedtuple
from pyscan import config
from pyscan.scan import EPICS_WRITER, EPICS_READER
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
    _, pv_name, readback_pv_name, tolerance, readback_pv_value = epics_pv(pv_name, readback_pv_name, tolerance)

    if value is None:
        raise ValueError("pv value not specified.")

    if not timeout or timeout < 0:
        timeout = config.epics_default_set_and_match_timeout

    def execute():
        writer = EPICS_WRITER(pv_name, readback_pv_name, tolerance, timeout)
        writer.set_and_match(value)
        writer.close()

    return execute


def action_restore(writables):
    """
    Restore the initial state of the writable PVs.
    :return: Empty tuple, to be replaced with the initial values.
    """
    writables = convert_to_list(writables)
    pv_names = [pv.pv_name for pv in writables]
    readback_pv_names = [pv.readback_pv_name for pv in writables]
    tolerances = [pv.tolerance for pv in writables]

    # Get the initial values.
    reader = EPICS_READER(pv_names)
    initial_values = reader.read()
    reader.close()

    def execute():
        writer = EPICS_WRITER(pv_names, readback_pv_names, tolerances)
        writer.set_and_match(initial_values)
        writer.close()

    return execute

