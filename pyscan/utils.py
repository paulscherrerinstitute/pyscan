import inspect
from collections import OrderedDict
from time import sleep

from epics.pv import PV

from pyscan import config
from pyscan.scan_parameters import convert_input, ConditionComparison


def compare_channel_value(current_value, expected_value, tolerance=0.0, operation=ConditionComparison.EQUAL):
    """
    Check if the pv value is the same as the expected value, within tolerance for int and float.
    :param current_value: Current value to compare it to.
    :param expected_value: Expected value of the PV.
    :param tolerance: Tolerance for number comparison. Cannot be less than the minimum tolerance.
    :param operation: Operation to perform on the current and expected value - works for int and floats.
    :return: True if the value matches.
    """
    # Minimum tolerance allowed.
    tolerance = max(tolerance, config.max_float_tolerance)

    def compare_value(value):
        # If we set a string, we expect the result to match exactly.
        if isinstance(current_value, str):
            if value == expected_value:
                return True

        # For numbers we compare them within tolerance.
        elif isinstance(current_value, (float, int)):

            if operation == ConditionComparison.EQUAL:
                if abs(current_value - expected_value) <= tolerance:
                    return True

            elif operation == ConditionComparison.HIGHER:
                if (current_value - expected_value) > tolerance:
                    return True

            elif operation == ConditionComparison.HIGHER_OR_EQUAL:
                if (current_value - expected_value) >= tolerance:
                    return True

            elif operation == ConditionComparison.LOWER:
                if (current_value - expected_value) < tolerance:
                    return True

            elif operation == ConditionComparison.LOWER_OR_EQUAL:
                if (current_value - expected_value) <= tolerance:
                    return True

            elif operation == ConditionComparison.NOT_EQUAL:
                if abs(current_value - expected_value) > tolerance:
                    return True

        # We cannot set and match other than strings and numbers.
        else:
            try:
                return current_value == expected_value
            except:
                raise ValueError("Do not know how to compare %s with the expected value %s."
                                 % (current_value, expected_value))

        return False

    if isinstance(current_value, list):
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
    # If None or a list, just return the value as it is.
    if (value is None) or isinstance(value, list):
        return value

    # Otherwise treat the value as the first element in a list.
    return [value]


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


class ActionExecutor(object):
    """
    Execute all callbacks in the same thread.
    Each callback method should accept 2 parameters: position, sampled values.
    """

    def __init__(self, actions):
        """
        Initialize the action executor.
        :param actions: Actions to execute. Single action or list of.
        """
        self.actions = convert_to_list(actions)

    def execute(self, position, position_data=None):
        for action in self.actions:
            n_parameters = len(inspect.signature(action).parameters)

            if n_parameters == 2:
                action(position, position_data)

            elif n_parameters == 1:
                action(position)

            else:
                action()


class SimpleDataProcessor(object):
    """
    Save the position and the received data at this position.
    """

    def __init__(self, positions=None, data=None):
        """
        Initialize the simple data processor.
        :param positions: List to store the visited positions. Default: internal list.
        :param data: List to store the data at each position. Default: internal list.
        """
        self.positions = positions if positions is not None else []
        self.data = data if data is not None else []

    def process(self, position, data):
        self.positions.append(position)
        self.data.append(data)

    def get_data(self):
        return self.data

    def get_positions(self):
        return self.positions


class DictionaryDataProcessor(SimpleDataProcessor):
    """
    Save the positions and the received data for each position in a dictionary.
    """
    def __init__(self, readables, positions=None, data=None):
        """
        Readables specified in the scan.
        :param readables: Same readables that were passed to the scan function.
        """
        super(DictionaryDataProcessor, self).__init__(positions=positions, data=data)

        readables = convert_input(readables)
        self.readable_ids = [x.identifier for x in readables]

    def process(self, position, data):
        self.positions.append(position)
        # Create a dictionary with the results.
        values = OrderedDict(zip(self.readable_ids, data))
        self.data.append(values)
