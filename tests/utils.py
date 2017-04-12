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