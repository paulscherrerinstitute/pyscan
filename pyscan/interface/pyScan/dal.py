from pyscan.utils import EpicsWriter, EpicsReader


class PyEpicsDal(object):

    def __init__(self):
        self.groups = {}

    def addGroup(self, group_name, pvs):
        self.groups[group_name] = EpicsReader(pvs)
        return group_name

    def groupClose(self, handle):
        for pv in self.groups[handle]:
            # TODO: Close the PVs?
            pass

    def getGroup(self, handle):
        return self.cafe.getGroup(handle)

    def setAndMatch(self, pv_name, value, chread, tolerance, timeout, num):
        writer = EpicsWriter(pv_name)
        # TODO: Provide readback capability to write
        writer.write(value, tolerance, timeout)

    def get(self, m):
        raise NotImplementedError()
        # return self.cafe.get(m)

    def getPVCache(self, h):
        raise NotImplementedError()
        # return self.cafe.getPVCache(h)

    def getHandlesFromWithinGroup(self, handle):
        raise NotImplementedError()
        # return self.cafe.getHandlesFromWithinGroup(handle)

    def openMonitorPrepare(self):
        raise NotImplementedError()
        # return self.cafe.openMonitorPrepare()

    def openMonitorNowAndWait(self, time):
        raise NotImplementedError()
        # return self.cafe.openMonitorNowAndWait(time)

    def groupMonitorStartWithCBList(self, handle, cb):
        raise NotImplementedError()
        dbr = self.cyca.CY_DBR_PLAIN
        mask = self.cyca.CY_DBE_VALUE
        # return self.cafe.groupMonitorStartWithCBList(handle, cb=cb, dbr=dbr, mask=mask)

    def match(self, val, chread, tol, timeout, num):
        raise NotImplementedError()
        # return self.cafe.match(val, chread, tol, timeout, num)


