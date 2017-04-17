from pyscan.interface.pyScan.scan import Scan


def scan(prefix="MA-"):

    pyscan = Scan()

    indict1 = dict()
    indict1['Knob'] = [prefix + 'SARUN04-UIND030-MOT:X-SET']
    indict1['KnobReadback'] = [prefix + 'SARUN04-UIND030-MOT:X-SET']
    indict1['KnobTolerance'] = [0.01]
    indict1['KnobWaiting'] = [10]
    indict1['KnobWaitingExtra']=0

    indict1['ScanRange'] = [[-0.3, 0.3]]
    indict1['Nstep'] = 10

    # indict1['StepSize']=
    # indict1['Scan Values']=

    indict1['Observable'] = [prefix + 'SARUN06-DBPM070:X', prefix + 'SARUN06-DBPM070:Y']

    indict1['Waiting'] = 0.1
    indict1['Validation'] = [prefix + 'SARUN06-DBPM070:POS-VALID', prefix + 'SARUN06-DBPM070:Q-VALID']

    indict1['NumberOfMeasurements'] = 3

    indict1['Monitor'] = [prefix + 'SINSS-LPSA:SHUTTER']
    indict1['MonitorValue'] = ['Open']
    indict1['MonitorTolerance'] = [0]
    indict1['MonitorAction'] = ['WaitAndAbort']
    indict1['MonitorTimeout'] = [5]

    indict1['PreAction'] = [[prefix + 'SARUN04-MQUA020-MOT:X', prefix + 'SARUN04-MQUA020-MOT:X', 1, 0.1, 10]]
    # indict1['PreActionWaiting']=0
    # indict1['PreActionOrder']=0

    indict1['PostAction'] = [[prefix + 'SARUN04-MQUA020-MOT:X', prefix + 'SARUN04-MQUA020-MOT:X', 0, 0, 10]]

    indict0 = dict()
    indict0['Knob'] = [prefix + 'SARUN04-UIND030-MOT:Y-SET']
    indict0['KnobReadback'] = [prefix + 'SARUN04-UIND030-MOT:Y-SET']
    indict0['KnobTolerance'] = [0.01]
    indict0['KnobWaiting'] = [10]
    indict0['ScanRange'] = [[-0.2, 0.2]]
    indict0['Nstep'] = 4

    outdict = pyscan.initializeScan([indict0, indict1])

    print(outdict['ErrorMessage'])
    print(indict1['KnobExpanded'])

    outdict = pyscan.startScan()

    for o in outdict['Observable']:
        print(o)

    # print pyscan.outdict['KnobReadback']
    outdict = pyscan.initializeScan([indict0, indict1])
    outdict = pyscan.startScan()

    # for o in  outdict['Observable']:
    #    print o

    print(outdict['Validation'])

if __name__ == "__main__":
    scan()
