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
