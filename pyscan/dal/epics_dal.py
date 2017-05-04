import time
from itertools import count
from pyscan.utils import convert_to_list, validate_lists_length, connect_to_pv, compare_channel_value
from pyscan.config import min_tolerance


class PyEpicsDal(object):
    """
    Provide a high level abstraction over PyEpics with group support.
    """

    def __init__(self):
        self.groups = {}
        self.pvs = {}

    def add_group(self, group_name, group_interface):
        # Do not allow to overwrite the group.
        if group_name in self.groups:
            raise ValueError("Group with name %s already exists. "
                             "Use different name of close existing group first." % group_name)

        self.groups[group_name] = group_interface
        return group_name

    def add_reader_group(self, group_name, pv_names, n_measurements=None, waiting=None):
        self.add_group(group_name, ReadGroupInterface(pv_names, n_measurements, waiting))

    def add_writer_group(self, group_name, pv_names, readback_pv_names=None, tolerances=None, timeout=None):
        self.add_group(group_name, WriteGroupInterface(pv_names, readback_pv_names, tolerances, timeout))

    def get_group(self, handle):
        return self.groups.get(handle)

    def close_group(self, group_name):
        if group_name not in self.groups:
            raise ValueError("Group does not exist. Available groups:\n%s" % self.groups.keys())

        # Close the PV connection.
        self.groups[group_name].close()
        del self.groups[group_name]

    def close_all_groups(self):
        for group in self.groups.values():
            group.close()
        self.groups.clear()


class WriteGroupInterface(object):
    """
    Manage a group of Write PVs.
    """
    default_timeout = 5
    default_get_sleep = 0.1

    def __init__(self, pv_names, readback_pv_names=None, tolerances=None, timeout=None):
        """
        Initialize the write group.
        :param pv_names: PV names (or name, list or single string) to connect to. 
        :param readback_pv_names: PV names (or name, list or single string) of readback PVs to connect to. 
        :param tolerances: Tolerances to be used for set_and_match. You can also specify them on the set_and_match
        :param timeout: Timeout to reach the destination.
        """
        self.pv_names = convert_to_list(pv_names)
        self.pvs = [self.connect(pv_name) for pv_name in self.pv_names]

        if readback_pv_names:
            self.readback_pv_name = convert_to_list(readback_pv_names)
            self.readback_pvs = [self.connect(pv_name) for pv_name in self.readback_pv_name]
        else:
            self.readback_pv_name = self.pv_names
            self.readback_pvs = self.pvs

        self.tolerances = self._setup_tolerances(tolerances)

        # We also do not allow timeout to be zero.
        self.timeout = timeout or self.default_timeout

        # Verify if all provided lists are of same size.
        validate_lists_length(self.pvs, self.readback_pvs, self.tolerances)

        # Check if timeout is int or float.
        if not isinstance(self.timeout, (int, float)):
            raise ValueError("Timeout must be int or float, but %s was provided." % self.timeout)

    def _setup_tolerances(self, tolerances):
        """
        Construct the list of tolerances. No tolerance can be less then the minimal tolerance.
        :param tolerances: Input tolerances.
        :return: Tolerances adjusted to the minimum value, if needed.
        """
        # If the provided tolerances are empty, substitute them with a list of default tolerances.
        tolerances = convert_to_list(tolerances) or [min_tolerance] * len(self.pvs)
        # Each tolerance needs to be at least the size of the minimum tolerance.
        tolerances = [max(min_tolerance, tolerance) for tolerance in tolerances]

        return tolerances

    def set_and_match(self, values, tolerances=None, timeout=None):
        """
        Set the value and wait for the PV to reach it, within tollerance.
        :param values: Values to set (Must match the number of PVs in this group)
        :param tolerances: Tolerances for each PV (Must match the number of PVs in this group)
        :param timeout: Timeout, single value, to wait until the value is reached.
        :raise ValueError if any position cannot be reached.
        """
        values = convert_to_list(values)
        if not tolerances:
            tolerances = self.tolerances
        else:
            # We do not allow tolerances to be less than the default tolerance.
            tolerances = self._setup_tolerances(tolerances)
        if not timeout:
            timeout = self.timeout

        # Verify if all provided lists are of same size.
        validate_lists_length(self.pvs, values, tolerances)

        # Check if timeout is int or float.
        if not isinstance(timeout, (int, float)):
            raise ValueError("Timeout must be int or float, but %s was provided." % timeout)

        # Write all the PV values.
        for pv, value in zip(self.pvs, values):
            pv.put(value)

        # Boolean array to represent which PVs have reached their target value.s
        within_tolerance = [False] * len(self.pvs)
        initial_timestamp = time.time()

        # Read values until all PVs have reached the desired value or time has run out.
        while (not all(within_tolerance)) and (time.time() - initial_timestamp < timeout):
            # Get only the PVs that have not yet reached the final position.
            for index, pv, tolerance in ((index, pv, tolerance) for index, pv, tolerance, values_reached
                                         in zip(count(), self.readback_pvs, tolerances, within_tolerance)
                                         if not values_reached):

                current_value = pv.get()
                expected_value = values[index]

                if compare_channel_value(current_value, expected_value, tolerance):
                    within_tolerance[index] = True

            time.sleep(self.default_get_sleep)

        if not all(within_tolerance):
            error_message = ""
            # Get the indexes that did not reach the supposed values.
            for index in [index for index, reached_value in enumerate(within_tolerance) if not reached_value]:
                expected_value = values[index]
                pv_name = self.pv_names[index]
                tolerance = tolerances[index]

                error_message += "Cannot achieve value %s, on PV %s, with tolerance %s.\n" % \
                         (expected_value, pv_name, tolerance)

            raise ValueError(error_message)

    @staticmethod
    def connect(pv_name):
        return connect_to_pv(pv_name)

    def close(self):
        """
        Close all PV connections.
        """
        for pv in self.pvs:
            pv.disconnect()


class ReadGroupInterface(object):
    """
    Manage group of read PVs.
    """
    default_n_measurements = 1
    default_waiting = 0

    def __init__(self, pv_names, n_measurements=None, waiting=None):
        """
        Initialize the group.
        :param pv_names: PV names (or name, list or single string) to connect to. 
        :param n_measurements: How many times to measure each time. Default = 1.
        """
        self.pv_names = convert_to_list(pv_names)
        self.pvs = [self.connect(pv_name) for pv_name in self.pv_names]

        if not n_measurements:
            self.n_measurements = self.default_n_measurements
        else:
            self.n_measurements = n_measurements

        if waiting is None:
            self.waiting = self.default_waiting
        else:
            self.waiting = waiting

        # Check if n_measurements is int or float.
        if not isinstance(self.n_measurements, (int, float)):
            raise ValueError("Number of measurements must be int or float, but %s was provided." % self.n_measurements)

        # Check if n_measurements is int or float.
        if not isinstance(self.waiting, (int, float)):
            raise ValueError(
                "Waiting time must be int or float, but %s was provided." % self.waiting)

    def read(self, n_measurements=None, waiting=None):
        """
        Read PVs one by one.
        :return: List of results.
        """
        # We do not allow the number of measurements to be 0.
        if not n_measurements:
            n_measurements = self.n_measurements

        if waiting is None:
            waiting = self.waiting

        # Check if n_measurements is int or float.
        if not isinstance(n_measurements, (int, float)):
            raise ValueError("Number of measurements must be int or float, but %s was provided." % n_measurements)

        result = []
        for i in range(n_measurements):
            single_measurement = []
            for pv in self.pvs:
                single_measurement.append(pv.get())

            result.append(single_measurement)

            # Wait between measurements.
            time.sleep(waiting)

        # Return first element, if we only have 1 measurement.
        if n_measurements == 1:
            return result[0]
        else:
            return result

    @staticmethod
    def connect(pv_name):
        return connect_to_pv(pv_name)

    def close(self):
        """
        Close all PV connections.
        """
        for pv in self.pvs:
            pv.disconnect()


