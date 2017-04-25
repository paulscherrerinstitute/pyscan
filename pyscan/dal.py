import time
from itertools import count
from epics.pv import PV
from pyscan.utils import convert_to_list


class PyEpicsDal(object):
    """
    Provide a high level abstraction over PyEpics with group support.
    """

    def __init__(self):
        self.groups = {}
        self.pvs = {}

    def add_pv(self, pv_name):
        # Do not allow to overwrite the group.
        if pv_name in self.pvs:
            raise ValueError("PV with name %s already exists. "
                             "Use different name of close existing PV first." % pv_name)

        self.pvs[pv_name] = EpicsInterface(pv_name)

    def add_group(self, group_name, pvs):
        # Do not allow to overwrite the group.
        if group_name in self.groups:
            raise ValueError("Group with name %s already exists. "
                             "Use different name of close existing group first." % group_name)

        # Start the group.
        self.groups[group_name] = EpicsInterface(pvs)
        return group_name

    def close_group(self, group_name):
        if group_name not in self.groups:
            raise ValueError("Group does not exist. Available groups:\n%s" % self.groups.keys())

        # Close the PV connection.
        self.groups[group_name].close()

    def get_group(self, handle):
        return self.groups[handle].read()

    def set_and_match(self, pv_name, value, chread, tolerance, timeout, num):
        writer = self.pvs[pv_name]
        writer.set_and_match(value, tolerance, timeout)

    def close_group(self, group_name):
        self.groups[group_name].close()

    def close_all_groups(self):
        for group in self.groups.values():
            group.close()

    def read(self):
        return self.get_group("All")

    def write(self, values):
        # TODO: Implement tolerance, timeout ETC.
        self.groups["Knobs"].write_and_match(values)


class EpicsInterface(object):
    """
    PyEpics wrapper for easier communication.
    """
    def __init__(self, list_of_pvs, n_measurments=1, list_of_readback_pvs=None):
        self.pv_names = list_of_pvs
        self.readback_pv_names = list_of_readback_pvs
        self.pvs = [self.connect_to_pv(pv_name) for pv_name in convert_to_list(list_of_pvs)]

        if list_of_readback_pvs:
            self.readback_pvs = [self.connect_to_pv(pv_name) for pv_name in convert_to_list(list_of_readback_pvs)]
        else:
            self.readback_pvs = self.pvs

        self.n_measurements = n_measurments

    @staticmethod
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
            time.sleep(0.1)

        raise ValueError("Cannot connect to PV '%s'." % pv_name)

    def read(self):
        """
        Read PVs one by one.
        :return: List of results.
        """
        result = []
        for pv in self.pvs:
            if self.n_measurements == 1:
                result.append(pv.get())
            else:
                pv_result = []
                for i in range(self.n_measurements):
                    pv_result.append(pv.get())
                result.append(pv_result)

        return result

    def set_and_match(self, values, tolerance=0.00001, timeout=5):
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
                              in zip(count(), within_tolerance, self.readback_pvs) if not reached):
                # The get method might return a None. In this case we do not care about the method.
                current_value = pv.get()
                if not current_value:
                    continue

                pv_value = pv.get()
                abs_difference = abs(pv_value - values[index])
                if abs_difference < tolerance:
                    within_tolerance[index] = True

        if not all(within_tolerance):
            raise ValueError("Cannot achieve position in specified time %d and tolerance %d." % (timeout, tolerance))

    def close(self):
        for pv in self.pvs:
            pv.disconnect()
