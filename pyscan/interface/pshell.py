from enum import Enum

from pyscan.positioner import ZigZagLinePositioner, LinePositioner, AreaPositioner, ZigZagAreaPositioner
from pyscan.scan import Scanner
from pyscan.utils import convert_to_list, EpicsReader, EpicsWriter, SimpleExecuter, SimpleDataProcessor


class Config(Enum):
    READER = "reader"
    WRITER = "writer"
    BEFORE_EXECUTOR = "before_executor"
    AFTER_EXECUTOR = "after_executor"
    DATA_PROCESSOR = "data_processor"

config = {Config.READER: EpicsReader,
          Config.WRITER: EpicsWriter,
          Config.BEFORE_EXECUTOR: SimpleExecuter,
          Config.AFTER_EXECUTOR: SimpleExecuter,
          Config.DATA_PROCESSOR: SimpleDataProcessor}


def set_config(key, value):
    """
    Configure the pshell interface module.
    :param key: Key enum from the Config class.
    :type key: Config
    :param value: Value to add to the key.
    """
    config[key] = value


def lscan(writables, readables, start, end, steps, latency=0.0, relative=False,
          passes=1, zigzag=False, before_read=None, after_read=None, title=None):
    """
    Line Scan: positioners change together, linearly from start to end positions.
    :param writables: List of identifiers to write to at each step.
    :param readables: List of identifiers to read from at each step.
    :param start: Start position for writables.
    :param end: Stop position for writables.
    :param steps: Number of scan steps(integer) or step size (float).
    :param latency: Settling time before each readout. Default = 0.
    :param relative: Start and stop positions are relative to the current position.
    :param passes: Number of passes for each scan.
    :param zigzag: If True and passes > 1, invert moving direction on each pass.
    :param before_read: List of callback functions on each step before readback.
    :param after_read: List of callback functions on each step after readback.
    :return: Data from the scan.
    """
    # TODO: On all interfaces: Check if readablers and writables are already objects with methods to call.

    # Allow the user to specify a single item or a list of items, but always convert to a list of items.
    writables = convert_to_list(writables)
    readables = convert_to_list(readables)
    start = convert_to_list(start)
    end = convert_to_list(end)
    steps = convert_to_list(steps)

    writer = config[Config.WRITER](writables)
    reader = config[Config.READER](readables)

    offsets = reader.read() if relative else None

    if zigzag:
        positioner = ZigZagLinePositioner(start, end, steps, passes, offsets)
    else:
        positioner = LinePositioner(start, end, steps, passes, offsets)

    before_executer = config[Config.BEFORE_EXECUTOR](before_read)
    after_executer = config[Config.AFTER_EXECUTOR](after_read)

    scanner = Scanner(positioner, writer, reader, before_executer, after_executer)
    scanner.discrete_scan(latency)


def ascan(writables, readables, start, end, steps, latency=0.0, relative=False,
          passes=1, zigzag=False, before_read=None, after_read=None, title=None):
    """
    Area Scan: multi-dimentional scan, each positioner is a dimention.
    :param writables: List of identifiers to write to at each step.
    :param readables: List of identifiers to read from at each step.
    :param start: Start position for writables.
    :param end: Stop position for writables.
    :param steps: Number of scan steps(integer) or step size (float).
    :param latency: Settling time before each readout. Default = 0.
    :param relative: Start and stop positions are relative to the current position.
    :param passes: Number of passes for each scan.
    :param zigzag: If True and passes > 1, invert moving direction on each pass.
    :param before_read: List of callback functions on each step before readback.
    :param after_read: List of callback functions on each step after readback.
    :return: Data from the scan.
    """

    # Allow the user to specify a single item or a list of items, but always convert to a list of items.
    writables = convert_to_list(writables)
    readables = convert_to_list(readables)
    start = convert_to_list(start)
    end = convert_to_list(end)
    steps = convert_to_list(steps)

    writer = config[Config.WRITER](writables)
    reader = config[Config.READER](readables)

    offsets = reader.read() if relative else None

    if zigzag:
        positioner = AreaPositioner(start, end, steps, passes, offsets)
    else:
        positioner = ZigZagAreaPositioner(start, end, steps, passes, offsets)

    before_executer = config[Config.BEFORE_EXECUTOR](before_read)
    after_executer = config[Config.AFTER_EXECUTOR](after_read)

    scanner = Scanner(positioner, writer, reader, before_executer, after_executer)
    scanner.discrete_scan(latency)
