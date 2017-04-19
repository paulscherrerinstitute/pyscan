import time
from itertools import count

from epics import PV


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


def connect_to_pv(pv_name):
    """
    Start a connection to a PV.
    :param pv_name: PV name to connect to.
    :return: PV object.
    :raises ValueError if cannot connect to PV.
    """
    pv = PV(pv_name, auto_monitor=False)
    if not pv.connect():
        raise ValueError("Cannot connect to PV '%s'." % pv_name)

    return pv


class EpicsWriter(object):
    """
    Sequentially write the PV value and wait for the PV to reach the desired value.
    """

    def __init__(self, list_of_pvs):
        self.pvs = [connect_to_pv(pv_name) for pv_name in convert_to_list(list_of_pvs)]

    def write(self, values, tolerance=0.00001, timeout=5):
        """
        Write values and wait for PVs to reach set value.
        :param values: Values to set.
        :param tolerance: Tolerance that needs to be reached.
        :param timeout: Timeout to reach the desired position.
        :raise ValueError if position cannot be reached in time
        """
        values = convert_to_list(values)

        for pv, value in zip(self.pvs, values):
            pv.put(value)

        # Boolean array to represent which PVs have reached their target value.s
        within_tolerance = [False] * len(self.pvs)
        initial_timestamp = time.time()

        # Read values until all PVs have reached the desired value or time has run out.
        while not all(within_tolerance) and time.time() - initial_timestamp < timeout:
            for index, pv in ((index, pv) for index, reached, pv
                              in zip(count(), within_tolerance, self.pvs) if not reached):
                # The get method might return a None. In this case we do not care about the method.
                current_value = pv.get()
                if not current_value:
                    continue

                if abs(pv.get() - values[index]) < tolerance:
                    within_tolerance[index] = True

        if not all(within_tolerance):
            raise ValueError("Cannot achieve position in specified time.")


class EpicsReader(object):
    """
    Sequentially read the PVs and return a list of results.
    """

    def __init__(self, list_of_pvs):
        self.pvs = [connect_to_pv(pv_name) for pv_name in convert_to_list(list_of_pvs)]

    def read(self):
        """
        Read PVs one by one.
        :return: List of results.
        """
        result = []
        for pv in self.pvs:
            result.append(pv.get())

        return result


class SimpleExecuter(object):
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


class PyScanDataProcessor(object):
    def __init__(self, output, n_pvs, n_validation, n_observable):
        self.n_pvs = n_pvs
        self.n_validation = n_validation
        self.n_observable = n_observable
        self.output = output

    def process(self, position, data):
        if self.n_readbacks == 1:
            readback_result = data[0]
        else:
            readback_result = data[0:self.n_readbacks]

        if self.n_validation == 1:
            validation_result = data[self.n_readbacks]
        else:
            validation_result = data[self.n_readbacks:self.n_readbacks + self.n_validations]

        if self.n_observable:
            observable_result = data[-1]
        else:
            observable_result = data[self.n_readbacks + self.n_validations:self.n_readbacks +
                                                                           self.n_validations + self.n_observables]

        # TODO: This might not work because of pre-initialization. Remove from original Scan class?
        self.output["KnobReadback"].append(readback_result)
        self.output["Validation"].append(validation_result)
        self.output["Observable"].append(observable_result)
