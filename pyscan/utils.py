import time
from itertools import count

from epics import PV


def convert_to_list(value):
    """
    If the input parameter is not a list, convert to one.
    :return: The value in a list, or None.
    """
    return [value] if (value is not None) and (not isinstance(value, list)) else value


class EpicsWriter(object):
    """
    Sequentially write the PV value and wait for the PV to reach the desired value.
    """
    def __init__(self, list_of_pvs):
        self.pvs = []
        for pv_name in convert_to_list(list_of_pvs):
            self.pvs.append(PV(pv_name, auto_monitor=False))

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
        self.pvs = []
        for pv_name in convert_to_list(list_of_pvs):
            self.pvs.append(PV(pv_name, auto_monitor=False))

    def read(self):
        """
        Read PVs one by one.
        :return: List of results.
        """
        result = []
        for pv in self.pvs:
            result.append(pv.get())

        return result

