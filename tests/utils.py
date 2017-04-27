class TestWriter(object):
    def __init__(self, buffer=None):
        """
        Initiate the test writer.
        :param buffer: Buffer to write to.
        """
        if buffer is None:
            buffer = []

        self.buffer = buffer

    def write(self, value):
        """
        Save the values to write to the buffer.
        :param value: 
        :return: 
        """
        self.buffer.append(value)


class TestReader(object):
    def __init__(self, data_source):
        """
        Initiate the test reader.
        :param data_source: List of values to return.
        """
        self.data_source = data_source
        self.iter = iter(self.data_source)

    def read(self):
        """
        Return the next element from the data_source list.
        :return: 
        """
        return next(self.iter)


def is_close(list1, list2, epsilon=0.00001):
    """
    Comparator 2 lists of floats.
    Since we are dealing with floats, an exact match cannot be enforced.
    :param list1: First list to compare.
    :param list2: Second list to compare.
    :param epsilon: Maximum difference we allow at each step. Default 10e-5
    :return: True if all elements are in the specified error range.
    """
    return all((value1 - value2) < epsilon for value1, value2 in zip(list1, list2))


class TestPyScanDal(object):
    def __init__(self, initial_values=None):
        self.groups = {}
        self.values = initial_values or {}
        self.positions = []

    def get_positions(self):
        return self.positions

    def add_group(self, group_name, pvs):
        print("Creating group %s with PVs %s." % (group_name, pvs))
        self.groups[group_name] = pvs

        # Create mock values for each given PV, if the value was not provided in the initial values.
        for pv in pvs:
            if pv not in self.values:
                self.values[pv] = pv

        return group_name

    def close_group(self, handle):
        del(self.groups[handle])
        print("Close group %s." % handle)

    def get_group(self, group_name):
        result = []
        for pv in self.groups[group_name]:
            result.append(self.values[pv])

        if group_name == "All":
            self.positions.append(result)

        print("Getting group %s: %s." % (group_name, result))
        return result, 1, [0] * len(result)

    def set_and_match(self, chset, val, chread, tol, timeout, num):
        self.values[chset] = val
        print("Move %s to position %s" % (chset, val))
