from pyscan.dal.epics_dal import WriteGroupInterface, ReadGroupInterface
from pyscan.positioner.area import AreaPositioner, ZigZagAreaPositioner
from pyscan.positioner.line import ZigZagLinePositioner, LinePositioner
from pyscan.scan_parameters import scan_settings
from pyscan.scanner import Scanner
from pyscan.utils import convert_to_list, ActionExecutor


def lscan(writables, readables, start, end, steps, latency=0.0, relative=False,
          passes=1, zigzag=False, before_read=None, after_read=None, title=None):
    """Line Scan: positioners change together, linearly from start to end positions.

    Args:
        writables(list of Writable): Positioners set on each step.
        readables(list of Readable): Sensors to be sampled on each step.
        start(list of float): start positions of writables.
        end(list of float): final positions of writables.
        steps(int or float or list of float): number of scan steps (int) or step size (float).
        relative (bool, optional): if true, start and end positions are relative to 
            current at start of the scan
        latency(float, optional): settling time for each step before readout, defaults to 0.0.
        passes(int, optional): number of passes
        zigzag(bool, optional): if true writables invert direction on each pass.
        before_read (function, optional): callback on each step, before each readout. Callback may have as 
            optional parameters list of positions.
        after_read (function, optional): callback on each step, after each readout. Callback may have as 
            optional parameters a ScanRecord object. 
        title(str, optional): plotting window name.

    Returns:
        ScanResult object.

    """

    # Allow the user to specify a single item or a list of items, but always convert to a list of items.
    writables = convert_to_list(writables)
    readables = convert_to_list(readables)
    start = convert_to_list(start)
    end = convert_to_list(end)
    steps = convert_to_list(steps)

    writer = WriteGroupInterface(writables)
    reader = ReadGroupInterface(readables)

    offsets = reader.read() if relative else None

    # TODO: Figure out if steps is n_step or step_sizes

    if zigzag:
        positioner = ZigZagLinePositioner(start, end, steps, passes, offsets)
    else:
        positioner = LinePositioner(start, end, steps, passes, offsets)

    before_executer = ActionExecutor(before_read)
    after_executer = ActionExecutor(after_read)

    settings = scan_settings(settling_time=latency)

    scanner = Scanner(positioner=positioner,
                      writer=writer,
                      reader=reader,
                      before_executor=before_executer,
                      after_executor=after_executer,
                      settings=settings)

    return scanner.discrete_scan()


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
    :param title: Not used in this implementation - legacy.
    :return: Data from the scan.
    """

    # Allow the user to specify a single item or a list of items, but always convert to a list of items.
    writables = convert_to_list(writables)
    readables = convert_to_list(readables)
    start = convert_to_list(start)
    end = convert_to_list(end)
    steps = convert_to_list(steps)

    writer = WriteGroupInterface(writables)
    reader = ReadGroupInterface(readables)

    offsets = reader.read() if relative else None

    # TODO: Figure out if steps is n_step or step_sizes

    if zigzag:
        positioner = AreaPositioner(start, end, steps, passes, offsets)
    else:
        positioner = ZigZagAreaPositioner(start, end, steps, passes, offsets)

    before_executer = ActionExecutor(before_read)
    after_executer = ActionExecutor(after_read)

    settings = scan_settings(settling_time=latency)

    scanner = Scanner(positioner, writer, reader, before_executer, after_executer, settings=settings)
    return scanner.discrete_scan()


def vscan(writables, readables, vector, line=False, latency=0.0, relative=False, passes=1, zigzag=False,
          before_read=None, after_read=None, title=None):
    """Vector Scan: positioners change following values provided in a vector.

    Args:
        writables(list of Writable): Positioners set on each step.
        readables(list of Readable): Sensors to be sampled on each step.
        vector(list of list of float): table of positioner values.
        line (bool, optional): if true, processs as line scan (1d)
        relative (bool, optional): if true, start and end positions are relative to current at 
            start of the scan
        latency(float, optional): settling time for each step before readout, defaults to 0.0.        
        passes(int, optional): number of passes
        zigzag(bool, optional): if true writables invert direction on each pass.
        before_read (function, optional): callback on each step, before each readout.
        after_read (function, optional): callback on each step, after each readout.
        title(str, optional): plotting window name.

    Returns:
        ScanResult object.

    """
    latency_ms = int(latency * 1000)
    writables = to_list(string_to_obj(writables))
    readables = to_list(string_to_obj(readables))
    if len(vector) == 0:
        vector.append([])
    elif (not is_list(vector[0])) and (not isinstance(vector[0], PyArray)):
        vector = [[x, ] for x in vector]
    vector = to_array(vector, 'd')
    scan = VectorScan(writables, readables, vector, line, relative, latency_ms, passes, zigzag)
    scan.before_read = before_read
    scan.after_read = after_read
    scan.setPlotTitle(title)
    scan.start()
    return scan.getResult()


def rscan(writable, readables, regions, latency=0.0, relative=False, passes=1, zigzag=False, before_read=None,
          after_read=None, title=None):
    """Region Scan: positioner scanned linearly, from start to end positions, in multiple regions.

    Args:
        writable(Writable): Positioner set on each step, for each region.
        readables(list of Readable): Sensors to be sampled on each step.
        regions (list of tuples (float,float, int)   or (float,float, float)): each tuple define a scan region
                                (start, stop, steps) or (start, stop, step_size)                                  
        relative (bool, optional): if true, start and end positions are relative to 
            current at start of the scan
        latency(float, optional): settling time for each step before readout, defaults to 0.0.
        passes(int, optional): number of passes
        zigzag(bool, optional): if true writable invert direction on each pass.
        before_read (function, optional): callback on each step, before each readout. Callback may have as 
            optional parameters list of positions.
        after_read (function, optional): callback on each step, after each readout. Callback may have as 
            optional parameters a ScanRecord object. 
        title(str, optional): plotting window name.

    Returns:
        ScanResult object.

    """
    start = []
    end = []
    steps = []
    for region in regions:
        start.append(region[0])
        end.append(region[1])
        steps.append(region[2])
    latency_ms = int(latency * 1000)
    writable = string_to_obj(writable)
    readables = to_list(string_to_obj(readables))
    start = to_list(start)
    end = to_list(end)
    steps = to_list(steps)
    scan = RegionScan(writable, readables, start, end, steps, relative, latency_ms, passes, zigzag)
    scan.before_read = before_read
    scan.after_read = after_read
    scan.setPlotTitle(title)
    scan.start()
    return scan.getResult()


def cscan(writables, readables, start, end, steps, latency=0.0, time=None, relative=False, passes=1, zigzag=False,
          before_read=None, after_read=None, title=None):
    """Continuous Scan: positioner change continuously from start to end position and readables are sampled on the fly.

    Args:
        writable(Speedable or list of Motor): A positioner with a  getSpeed method or 
                    a list of motors.
        readables(list of Readable): Sensors to be sampled on each step.
        start(float or list of float): start positions of writables.
        end(float or list of float): final positions of writabless.
        steps(int or float or list of float): number of scan steps (int) or step size (float).
        time (float, seconds): if not None then writables is Motor array and speeds are 
                    set according to time.
        relative (bool, optional): if true, start and end positions are relative to 
            current at start of the scan
        latency(float, optional): sleep time in each step before readout, defaults to 0.0.
        before_read (function, optional): callback on each step, before each readout. 
                    Callback may have as optional parameters list of positions.
        after_read (function, optional): callback on each step, after each readout. 
                    Callback may have as optional parameters a ScanRecord object. 
        title(str, optional): plotting window name.

    Returns:
        ScanResult object.

    """
    raise NotImplementedError("Continuous scan not supported.")


def hscan(config, writable, readables, start, end, steps, passes=1, zigzag=False, before_stream=None, after_stream=None,
          after_read=None, title=None):
    """Hardware Scan: values sampled by external hardware and received asynchronously.

    Args:
        config(dict): Configuration of the hardware scan. The "class" key provides the implementation class.
                      Other keys are implementation specific.
        writable(Writable): A positioner appropriated to the hardware scan type.
        readables(list of Readable): Sensors appropriated to the hardware scan type.
        start(float): start positions of writable.
        end(float): final positions of writables.
        steps(int or float): number of scan steps (int) or step size (float).
        before_stream (function, optional): callback before just before starting positioner move. 
        after_stream (function, optional): callback before just after stopping positioner move. 
        after_read (function, optional): callback on each readout. 
                    Callback may have as optional parameters a ScanRecord object. 
        title(str, optional): plotting window name.

    Returns:
        ScanResult object.

    """
    raise NotImplementedError("Hardware scan not supported.")


def bscan(stream, records, before_read=None, after_read=None, title=None):
    """BS Scan: records all values in a beam synchronous stream.

    Args:
        stream(Stream): stream object
        records(int): number of records to store
        before_read (function, optional): callback on each step, before each readout. 
                    Callback may have as optional parameters list of positions.
        after_read (function, optional): callback on each step, after each readout. 
                    Callback may have as optional parameters a ScanRecord object. 
        title(str, optional): plotting window name.

    Returns:
        ScanResult object.

    """
    stream = string_to_obj(stream)
    scan = BsScan(stream, int(records))
    scan.before_read = before_read
    scan.after_read = after_read
    scan.setPlotTitle(title)
    scan.start()
    return scan.getResult()


def tscan(readables, points, interval, before_read=None, after_read=None, title=None):
    """Time Scan: sensors are sampled in fixed time intervals.

    Args:
        readables(list of Readable): Sensors to be sampled on each step.
        points(int): number of samples.
        interval(float): time interval between readouts. Minimum temporization is 0.001s
        before_read (function, optional): callback on each step, before each readout.
        after_read (function, optional): callback on each step, after each readout.
        title(str, optional): plotting window name.

    Returns:
        ScanResult object.

    """
    interval = max(interval, 0.001)  # Minimum temporization is 1ms
    interval_ms = int(interval * 1000)
    readables = to_list(string_to_obj(readables))
    scan = TimeScan(readables, points, interval_ms)
    scan.before_read = before_read
    scan.after_read = after_read
    scan.setPlotTitle(title)
    scan.start()
    return scan.getResult()


def mscan(trigger, readables, points, timeout=None, async=True, take_initial=False, before_read=None, after_read=None,
          title=None):
    """Monitor Scan: sensors are sampled when received change event of the trigger device.

    Args:
        trigger(Device): Source of the sampling triggering.
        readables(list of Readable): Sensors to be sampled on each step.
                                     If  trigger has cache and is included in readables, it is not read 
                                     for each step, but the change event value is used.
        points(int): number of samples.
        timeout(float, optional): maximum scan time in seconds. 
        async(bool, optional): if True then records are sampled and stored on event change callback. Enforce 
                               reading only cached values of sensors.
                               If False, the scan execution loop waits for trigger cache update. Do not make 
                               cache only access, but may loose change events.
        take_initial(bool, optional): if True include current values as first record (before first trigger).
        before_read (function, optional): callback on each step, before each readout.
        after_read (function, optional): callback on each step, after each readout.
        title(str, optional): plotting window name.

    Returns:
        ScanResult object.

    """
    timeout_ms = int(timeout * 1000) if ((timeout is not None) and (timeout >= 0)) else -1
    readables = to_list(string_to_obj(readables))
    scan = MonitorScan(trigger, readables, points, timeout_ms, async, take_initial)
    scan.before_read = before_read
    scan.after_read = after_read
    scan.setPlotTitle(title)
    scan.start()
    return scan.getResult()


def escan(name, title=None):
    """Epics Scan: execute an Epics Scan Record.

    Args:
        name(str): Name of scan record.
        title(str, optional): plotting window name.

    Returns:
        ScanResult object.

    """
    raise NotImplementedError("Epics scan not supported.")


def bsearch(writables, readable, start, end, steps, maximum=True, strategy="Normal", latency=0.0, relative=False,
            before_read=None, after_read=None, title=None):
    """Binary search: searches writables in a binary search fashion to find a local maximum for the readable.

    Args:
        writables(list of Writable): Positioners set on each step.
        readable(Readable): Sensor to be sampled.
        start(list of float): start positions of writables.
        end(list of float): final positions of writables.
        steps(float or list of float): resolution of search for each writable.
        maximum (bool , optional): if True (default) search maximum, otherwise minimum.
        strategy (str , optional): "Normal": starts search midway to scan range and advance in the best direction.
                                             Uses orthogonal neighborhood (4-neighborhood for 2d)
                                   "Boundary": starts search on scan range.                                              
                                   "FullNeighborhood": Uses complete neighborhood (8-neighborhood for 2d)

        latency(float, optional): settling time for each step before readout, defaults to 0.0.
        relative (bool, optional): if true, start and end positions are relative to current at 
            start of the scan
        before_read (function, optional): callback on each step, before each readout.
        after_read (function, optional): callback on each step, after each readout.
        title(str, optional): plotting window name.

    Returns:
        SearchResult object.

    """
    raise NotImplementedError("Binary search scan not supported.")


def hsearch(writables, readable, range_min, range_max, initial_step, resolution, noise_filtering_steps=1, maximum=True,
            latency=0.0, relative=False, before_read=None, after_read=None, title=None):
    """Hill Climbing search: searches writables in decreasing steps to find a local maximum for the readable.
    Args:
        writables(list of Writable): Positioners set on each step.
        readable(Readable): Sensor to be sampled.
        range_min(list of float): minimum positions of writables.
        range_max(list of float): maximum positions of writables.
        initial_step(float or list of float):initial step size for for each writable.
        resolution(float or list of float): resolution of search for each writable (minimum step size).
        noise_filtering_steps(int): number of aditional steps to filter noise
        maximum (bool , optional): if True (default) search maximum, otherwise minimum.
        latency(float, optional): settling time for each step before readout, defaults to 0.0.
        relative (bool, optional): if true, range_min and range_max positions are relative to current at 
            start of the scan
        before_read (function, optional): callback on each step, before each readout.
        after_read (function, optional): callback on each step, after each readout.
        title(str, optional): plotting window name.

    Returns:
        SearchResult object.

    """
    raise NotImplementedError("Hill climbing scan not supported.")
