from time import sleep

from epics.pv import PV

from pyscan.config import min_tolerance


def compare_channel_value(current_value, expected_value, tolerance=0.0):
    """
    Check if the pv value is the same as the expected value, within tolerance for int and float.
    :param current_value: Current value to compare it to.
    :param expected_value: Expected value of the PV.
    :param tolerance: Tolerance for number comparison. Cannot be less than the minimum tolerance.
    :return: True if the value matches.
    """
    # Minimum tolerance allowed.
    tolerance = max(tolerance, min_tolerance)

    def compare_value(value):
        # If we set a string, we expect the result to match exactly.
        if isinstance(expected_value, str):
            if value == expected_value:
                return True

        # For numbers we compare them within tolerance.
        elif isinstance(expected_value, (float, int)):
            if abs(current_value - expected_value) <= tolerance:
                return True

        # We cannot set and match other than strings and numbers.
        else:
            raise ValueError("Do not know how to compare %s with the expected value %s"
                             % (current_value, expected_value))

        return False

    if isinstance(expected_value, list):
        # In case of a list, any of the provided values will do.
        return any((compare_value(value) for value in expected_value))
    else:
        return compare_value(current_value)


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


def flat_list_generator(list_to_flatten):
    # Just return the most inner list.
    if (len(list_to_flatten) == 0) or (not isinstance(list_to_flatten[0], list)):
        yield list_to_flatten
    # Otherwise we have to go deeper.
    else:
        for inner_list in list_to_flatten:
            yield from flat_list_generator(inner_list)


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
