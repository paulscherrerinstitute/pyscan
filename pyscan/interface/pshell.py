from pyscan.positioner import ZigZagLinePositioner, LinePositioner, AreaPositioner, ZigZagAreaPositioner
from pyscan.scan import Scanner
from pyscan.utils import convert_to_list, EpicsInterface, SimpleExecutor


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

    # Allow the user to specify a single item or a list of items, but always convert to a list of items.
    writables = convert_to_list(writables)
    readables = convert_to_list(readables)
    start = convert_to_list(start)
    end = convert_to_list(end)
    steps = convert_to_list(steps)

    writer = EpicsInterface(writables)
    reader = EpicsInterface(readables)

    offsets = reader.read() if relative else None

    if zigzag:
        positioner = ZigZagLinePositioner(start, end, steps, passes, offsets)
    else:
        positioner = LinePositioner(start, end, steps, passes, offsets)

    before_executer = SimpleExecutor(before_read)
    after_executer = SimpleExecutor(after_read)

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

    writer = EpicsInterface(writables)
    reader = EpicsInterface(readables)

    offsets = reader.read() if relative else None

    if zigzag:
        positioner = AreaPositioner(start, end, steps, passes, offsets)
    else:
        positioner = ZigZagAreaPositioner(start, end, steps, passes, offsets)

    before_executer = SimpleExecutor(before_read)
    after_executer = SimpleExecutor(after_read)

    scanner = Scanner(positioner, writer, reader, before_executer, after_executer)
    scanner.discrete_scan(latency)
