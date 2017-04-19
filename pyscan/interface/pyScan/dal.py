try:
    import PyCafe
except:
    pass


class PyEpicsDal(object):
    def __init__(self):
        self.cafe = PyCafe.CyCafe()
        self.cafe.init()
        self.cyca = PyCafe.CyCa()

    def addGroup(self, GroupName, ChList):
        self.cafe.openGroupPrepare()
        h = self.cafe.grouping(GroupName, ChList)  # Grouping does GroupOpen
        # pvg=self.cafe.getPVGroup(GroupName)
        # pvg.show()
        # h=self.cafe.groupOpen(GroupName) # Grouping does GroupOpen
        self.cafe.openGroupNowAndWait(1.0)
        # sleep(1.0)
        return h

    def groupClose(self, handle):
        return self.cafe.groupClose(handle)

    def groupList(self):
        return self.cafe.groupList()

    def getGroup(self, handle):
        return self.cafe.getGroup(handle)

    def get(self, m):
        return self.cafe.get(m)

    def getPVCache(self, h):
        return self.cafe.getPVCache(h)

    def getHandlesFromWithinGroup(self, handle):
        return self.cafe.getHandlesFromWithinGroup(handle)

    def openMonitorPrepare(self):
        return self.cafe.openMonitorPrepare()

    def openMonitorNowAndWait(self, time):
        return self.cafe.openMonitorNowAndWait(time)

    def groupMonitorStartWithCBList(self, handle, cb):
        dbr = self.cyca.CY_DBR_PLAIN
        mask = self.cyca.CY_DBE_VALUE
        return self.cafe.groupMonitorStartWithCBList(handle, cb=cb, dbr=dbr, mask=mask)

    def match(self, val, chread, tol, timeout, num):
        return self.cafe.match(val, chread, tol, timeout, num)

    def setAndMatch(self, chset, val, chread, tol, timeout, num):
        return self.cafe.setAndMatch(chset, val, chread, tol, timeout, num)
