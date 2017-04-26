from itertools import count

import time
from pyscan.utils import convert_to_list, validate_lists_length, connect_to_pv


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

    def close_group(self, group_name):
        if group_name not in self.groups:
            raise ValueError("Group does not exist. Available groups:\n%s" % self.groups.keys())

        # Close the PV connection.
        self.groups[group_name].close()

    def get_group(self, handle):
        return self.groups[handle].read()

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


class WriteGroupInterface(object):
    """
    Manage a group of Write PVs.
    """
    default_tolerance = 0.00001
    default_timeout = 5
    default_get_sleep = 0.1

    def __init__(self, pv_names, readback_pv_names=None, tolerances=None, timeout=None):
        self.pv_names = convert_to_list(pv_names)
        self.pvs = [connect_to_pv(pv_name) for pv_name in self.pv_names]

        if readback_pv_names:
            self.readback_pv_name = convert_to_list(readback_pv_names)
            self.readback_pvs = [connect_to_pv(pv_name) for pv_name in self.readback_pv_name]
        else:
            self.readback_pv_name = self.pv_names
            self.readback_pvs = self.pvs

        # We never allow tolerance to be zero.
        self.tolerances = convert_to_list(tolerances) or [self.default_tolerance] * len(self.pvs)
        # We also do not allow timeout to be zero.
        self.timeout = timeout or self.default_timeout

        # Verify if all provided lists are of same size.
        validate_lists_length(self.pvs, self.readback_pvs, self.tolerances)

        # Check if timeout is int or float.
        if not isinstance(self.timeout, (int, float)):
            raise ValueError("Timeout must be int or float, but %s was provided." % self.timeout)

    def set_and_match(self, values, tolerances=None, timeout=None):
        values = convert_to_list(values)
        if not tolerances:
            tolerances = self.tolerances
        else:
            tolerances = convert_to_list(tolerances)
        if not timeout:
            timeout = self.timeout

        # Verify if all provided lists are of same size.
        validate_lists_length(self.pvs, values, tolerances, timeout)

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

                current_pv_value = pv.get()
                abs_difference = abs(current_pv_value - values[index])
                if abs_difference < tolerance:
                    within_tolerance[index] = True

            time.sleep(self.default_get_sleep)

        if not all(within_tolerance):
            raise ValueError("Cannot achieve position for %s in specified time %f and tolerance %f."
                             % (self.pv_names, timeout, tolerance))

    def close(self):
        for pv in self.pvs:
            pv.disconnect()


class ReadGroupInterface(object):
    """
    Manage group of read PVs.
    """
    default_n_measurements = 1

    def __init__(self, pv_names, n_measurements=None):
        self.pv_names = convert_to_list(pv_names)
        self.pvs = [connect_to_pv(pv_name) for pv_name in self.pv_names]

        if not n_measurements:
            self.n_measurements = self.default_n_measurements
        else:
            self.n_measurements = n_measurements

        # Check if n_measurements is int or float.
        if not isinstance(self.n_measurements, (int, float)):
            raise ValueError("Number of measurements must be int or float, but %s was provided." % self.n_measurements)

    def read(self, n_measurements=None):
        """
        Read PVs one by one.
        :return: List of results.
        """
        # We do not allow the number of measurements to be 0.
        if not n_measurements:
            n_measurements = self.n_measurements

        # Check if n_measurements is int or float.
        if not isinstance(n_measurements, (int, float)):
            raise ValueError("Number of measurements must be int or float, but %s was provided." % n_measurements)

        result = []
        for pv in self.pvs:
            if self.n_measurements == 1:
                measurement = pv.get()
            else:
                measurement = []
                for i in range(self.n_measurements):
                    measurement.append(pv.get())

            result.append(measurement)
        return result

    def close(self):
        for pv in self.pvs:
            pv.disconnect()
