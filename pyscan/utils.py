from time import sleep

from epics.pv import PV


def connect_to_pv(pv_name, n_connection_attempts=3):
    """
    Start a connection to a PV.
    :param pv_name: PV name to connect to.
    :param n_connection_attempts: How many times you should try to connect before raising an exception.
    :return: PV object.
    :raises ValueError if cannot connect to PV.
    """
    pv = PV(pv_name, auto_monitor=False)
    for i in range(n_connection_attempts):
        if pv.connect():
            return pv
        sleep(0.1)
    raise ValueError("Cannot connect to PV '%s'." % pv_name)


def validate_lists_length(*args):
    """
    Check if all the provided lists are of the same length.
    :param args: Lists.
    :raise ValueError if they are not of the same length.
    """
    if not args:
        raise ValueError("Cannot compare lengths of None.")

    initial_length = len(args[0])
    if not all([len(element) == initial_length for element in args]):
        error = "The provided lists must be of same length.\n"
        for element in args:
            error += "%s\n" % element

        raise ValueError(error)


def convert_to_list(value):
    """
    If the input parameter is not a list, convert to one.
    :return: The value in a list, or None.
    """
    return [value] if (value is not None) and (not isinstance(value, list)) else value


def convert_to_position_list(axis_list):
    """
    # Change the PER KNOB to PER INDEX of positions.
    :param axis_list: PER KNOB list of positions.
    :return: PER INDEX list of positions.
    """
    return [list(positions) for positions in zip(*axis_list)]


def flatten_list(list_to_flatten):
    # Just return the most inner list.
    if (len(list_to_flatten) == 0) or (not isinstance(list_to_flatten[0], list)):
        yield list_to_flatten
    # Otherwise we have to go deeper.
    else:
        for inner_list in list_to_flatten:
            yield from flatten_list(inner_list)


class SimpleExecutor(object):
    """
    Execute all callbacks in the same thread.
    Each callback method should accept 2 parameters: position, sampled values.
    """

    def __init__(self, callbacks):
        self.callbacks = callbacks

    def execute(self, context):
        for callback in self.callbacks:
            callback(context["position"], context["value"])


class SimpleDataProcessor(object):
    """
    Save the position and the received data at this position.
    """

    def __init__(self):
        self.positions = []
        self.data = []

    def process(self, position, data):
        self.positions.append(position)
        self.data.append(data)

    def get_data(self):
        return [(position, data) for position, data in zip(self.positions, self.data)]
