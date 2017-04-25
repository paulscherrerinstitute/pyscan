# Before running this test, start the epics_test_server.py

from pyscan.interface.pyScan import Scan


pyscan=Scan()
indict1 = {}

indict1['Knob'] = ["PYSCAN:TEST:MOTOR1:SET", "PYSCAN:TEST:MOTOR2:SET"]
indict1['KnobReadback'] = ["PYSCAN:TEST:MOTOR1:GET", "PYSCAN:TEST:MOTOR2:GET"]
indict1['KnobTolerance'] = [0.01, 0.01]
indict1['KnobWaiting'] = [10, 10]
indict1['KnobWaitingExtra'] = 0.5
indict1['ScanValues'] = [[0, 1, 2], [3, 4, 5]]
indict1['Observable'] = ["PYSCAN:TEST:OBS1", "PYSCAN:TEST:OBS2"]
indict1['Waiting'] = 0.25
indict1['NumberOfMeasurements'] = 3
indict1['PreAction'] = [["PYSCAN:TEST:MOTOR:PRE1:SET", "PYSCAN:TEST:MOTOR:PRE1:GET", 1, 0.1, 10]]
indict1['PostAction'] = ['Restore']

print(indict1['KnobReadback'])
print(indict1['Knob'])

outdict = pyscan.initializeScan(indict1)

print(outdict['ErrorMessage'])
print(indict1['KnobExpanded'])

outdict = pyscan.startScan()

print(outdict['Observable'])
