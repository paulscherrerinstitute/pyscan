import unittest

from pyscan.interface.pyScan import Scan


class PyScan(unittest.TestCase):

    def test_initializeScan(self):
        indict1 = dict()
        indict1['Knob'] = ["1.1", "1.2"]
        indict1['ScanRange'] = [[-2, 2], [-2, 2]]
        indict1['Nstep'] = 5
        indict1['Observable'] = ["READ1", "READ2"]
        indict1['Waiting'] = 0.1

        indict2 = dict()
        indict2['Knob'] = ["2.1", "2.2"]
        indict2['ScanRange'] = [[-2, 2], [-2, 2]]
        indict2['Nstep'] = 5
        indict2['Observable'] = ["READ3", "READ4"]
        indict2['Waiting'] = 0.1

        pyscan = Scan()
        pyscan.initializeScan([indict1, indict2])
        result = pyscan.startScan()
