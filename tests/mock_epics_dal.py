from pyscan.epics_dal import PyEpicsDal, ReadGroupInterface, WriteGroupInterface
from pyscan.interface.pyScan import READ_GROUP

pv_cache = {}
read_values = []

class MockPyEpicsDal(PyEpicsDal):
    """
    Provide a mock PyEpics dal.
    """

    def __init__(self):
        super(MockPyEpicsDal, self).__init__()
        pv_cache.clear()
        read_values.clear()

    @staticmethod
    def get_positions():
        return read_values

    def add_reader_group(self, group_name, pv_names, n_measurements=None, waiting=None):
        self.add_group(group_name, MockReadGroupInterface(pv_names, n_measurements, waiting))
        if group_name == READ_GROUP:
            self.get_group(group_name).save_values = True

    def add_writer_group(self, group_name, pv_names, readback_pv_names=None, tolerances=None, timeout=None):
        self.add_group(group_name, MockWriteGroupInterface(pv_names, readback_pv_names, tolerances, timeout))
        # Go over all the PVs that have a different readback PV defined.
        for pv_name, readback_pv_name in [(pv, readback_pv) for pv, readback_pv in
                                          zip(pv_names, readback_pv_names) if pv != readback_pv]:
            # Bind them, so their value can be updated.
            for pv in pv_cache[pv_name]:
                pv.readback_pv_name = readback_pv_name


class MockReadGroupInterface(ReadGroupInterface):
    # This is set by the MockPyEpicsDal to signal if the read result needs to be cached.
    save_values = False

    @staticmethod
    def connect(pv_name):
        return MockPV(pv_name)

    def read(self, n_measurements=None, waiting=None):
        result = super(MockReadGroupInterface, self).read(n_measurements, waiting)
        if self.save_values:
            read_values.append(result)
        return result


class MockWriteGroupInterface(WriteGroupInterface):
    @staticmethod
    def connect(pv_name):
        return MockPV(pv_name)

    def set_and_match(self, values, tolerances=None, timeout=None):
        # This is not ideal, since we are not testing the original set_and_match method.0
        # Write all the PV values.
        for pv, value in zip(self.pvs, values):
            pv.put(value)


class MockPV(object):
    """
    Mock the behaviour of PVs, including readback logic.
    """
    def __init__(self, pv_name, readback_pv_name=None):
        self.pv_name = pv_name
        self.readback_pv_name = readback_pv_name
        self.value = pv_name

        # We need this because the readback PVs need to be updated at every put.
        if pv_name in pv_cache:
            pv_cache[pv_name].append(self)
        else:
            pv_cache[pv_name] = [self]

    def get(self):
        return self.value

    def put(self, value):
        self.value = value

        # If we have a readback PV, update it.
        if self.readback_pv_name:
            for pv in pv_cache[self.readback_pv_name]:
                pv.put(self.value)
        # Otherwise there should be multiple instances with the same pv_name (readback pv is same as write pv).
        else:
            for pv in [pv for pv in pv_cache[self.pv_name] if pv != self]:
                # Do not use PUT, it triggers a recursion.
                pv.value = value

    def disconnect(self):
        pass

    def connect(self):
        pass
