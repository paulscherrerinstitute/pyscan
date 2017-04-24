from pyscan.utils import EpicsWriter, EpicsReader


class PyEpicsDal(object):

    def __init__(self):
        self.groups = {}
        self.channels = {}

    def add_group(self, group_name, pvs):
        self.groups[group_name] = EpicsReader(pvs)
        return group_name

    def close_group(self, handle):
        self.groups[handle].close()

    def get_group(self, handle):
        return self.groups[handle].read()

    def set_and_match(self, pv_name, value, chread, tolerance, timeout, num):
        writer = EpicsWriter(pv_name)
        # TODO: Provide readback capability to write
        writer.write(value, tolerance, timeout)

    def close_all_groups(self):
        for group in self.groups.values():
            group.close()
