import unittest

import numpy as np

from tests.interface.old_scan import Scan as CurrentScan
from tests.utils import TestPyScanDal as CurrentMockDal


# Comment this 2 lines to test with the old dal.
from pyscan.interface.pyScan import Scan as CurrentScan, np
from tests.mock_epics_dal import MockPyEpicsDal as CurrentMockDal

class IntegrationTests(unittest.TestCase):
    def test_EmitMeasTool(self):
        # Initialize the values.
        Images = 5
        QuadIch = ["PYSCAN:TEST:MOTOR1:SET", "PYSCAN:TEST:MOTOR2:SET"]
        QuadI = [[0, 1, 2, 3], [0, 1, 2, 3]]

        test_dal = CurrentMockDal(initial_values={"PYSCAN:TEST:OBS1": 1,
                                                  "PYSCAN:TEST:OBS2": 2,
                                                  "PYSCAN:TEST:OBS3": 1,
                                                  "PYSCAN:TEST:OBS4": 1,
                                                  "PYSCAN:TEST:MONITOR1": 9.95},
                                  pv_fixed_values={"PYSCAN:TEST:OBS1": [0.8, 0.9, 1.0, 1.1, 1.2],
                                                   "PYSCAN:TEST:OBS2": [-0.8, -0.9, -1.0, -1.1, -1.2]},)
        pyscan = CurrentScan()

        indict1 = {}
        # Knob setup
        indict1['Knob'] = QuadIch
        indict1['KnobReadback'] = [c.replace('SET', 'GET') for c in QuadIch]
        indict1['KnobTolerance'] = [0.01] * len(QuadIch)
        indict1['KnobWaiting'] = [10] * len(QuadIch)
        indict1['KnobWaitingExtra'] = 0.5
        indict1['ScanValues'] = QuadI

        # Measurement setup.
        indict1['Observable'] = ["PYSCAN:TEST:OBS1",
                                 "PYSCAN:TEST:OBS2",
                                 "PYSCAN:TEST:OBS3",
                                 "PYSCAN:TEST:OBS4"]
        indict1['Waiting'] = 0.25
        indict1['NumberOfMeasurements'] = int(Images)

        # Monitor setup
        # only doing the measurement if laser is producing beam, for the moment we do that the frequency is close to 10 Hz
        indict1['Monitor'] = ['PYSCAN:TEST:MONITOR1']
        indict1['MonitorValue'] = [10]
        indict1['MonitorTolerance'] = [0.1]
        indict1['MonitorAction'] = ['WaitAndAbort']
        indict1['MonitorTimeout'] = [15]

        # inserting the screen before measuring - to be defined as a variable depending on the PM
        indict1['PreAction'] = [["PYSCAN:TEST:PRE1:SET", "PYSCAN:TEST:PRE1:GET", 1, 0, 10]]

        # removing the screen after doing the measurement, to be added possible cycling
        indict1['PostAction'] = [["PYSCAN:TEST:PRE1:SET", "PYSCAN:TEST:PRE1:GET", 0, 0, 10], 'Restore']

        outdict = pyscan.initializeScan(indict1, dal=test_dal)
        outdict = pyscan.startScan()

        if int(Images) == 1:
            sigx = np.array([v[0] for v in outdict['Observable']])
            sigy = np.array([v[1] for v in outdict['Observable']])
            errx = np.ones(len(sigx)) * 0
            erry = errx

            jitx = np.ones(len(sigx)) * 0
            jity = np.ones(len(sigx)) * 0
            rel_jitx = np.ones(len(sigx)) * 0
            rel_jity = np.ones(len(sigx)) * 0
        else:
            sigx = np.zeros(len(outdict['Observable']))
            sigy = np.zeros(len(outdict['Observable']))
            errx = np.zeros(len(outdict['Observable']))
            erry = np.zeros(len(outdict['Observable']))

            for i in range(0, len(outdict['Observable'])):
                sigx[i] = np.mean(np.array([v[0] for v in outdict['Observable'][i]]), axis=0)
                errx[i] = np.std(np.array([v[0] for v in outdict['Observable'][i]]), axis=0)
                sigy[i] = np.mean(np.array([v[1] for v in outdict['Observable'][i]]), axis=0)
                erry[i] = np.std(np.array([v[1] for v in outdict['Observable'][i]]), axis=0)

            jitx = np.zeros(len(outdict['Observable']))
            jity = np.zeros(len(outdict['Observable']))
            for i in range(0, len(outdict['Observable'])):
                jitx[i] = np.std(np.array([v[2] for v in outdict['Observable'][i]]), axis=0)
                jity[i] = np.std(np.array([v[3] for v in outdict['Observable'][i]]), axis=0)

            rel_jitx = 100 * jitx / sigx
            rel_jity = 100 * jity / sigy

        errx[errx == 0] = 1e-99
        erry[erry == 0] = 1e-99

        self.assertTrue(all(abs(i1 - i2) < 0.0001 for i1, i2 in zip(sigx, [1] * 4)), "Unexpected result.")
        self.assertTrue(all(abs(i1 - i2) < 0.0001 for i1, i2 in zip(sigy, [-1] * 4)), "Unexpected result.")

        self.assertTrue(all(abs(i1 - i2) < 0.0001 for i1, i2 in zip(errx, [0.1414] * 4)),
                        "Standard error does not match the expected one.")
        self.assertTrue(all(abs(i1 - i2) < 0.0001 for i1, i2 in zip(erry, [0.1414] * 4)),
                        "Standard error does not match the expected one.")

        self.assertTrue(all(abs(i1 - i2) < 0.0001 for i1, i2 in zip(jitx, [0, 0, 0, 0])), "Unexpected result.")
        self.assertTrue(all(abs(i1 - i2) < 0.0001 for i1, i2 in zip(jity, [0, 0, 0, 0])), "Unexpected result.")
        self.assertTrue(all(abs(i1 - i2) < 0.0001 for i1, i2 in zip(rel_jitx, [0, 0, 0, 0])), "Unexpected result.")
        self.assertTrue(all(abs(i1 - i2) < 0.0001 for i1, i2 in zip(rel_jity, [0, 0, 0, 0])), "Unexpected result.")
