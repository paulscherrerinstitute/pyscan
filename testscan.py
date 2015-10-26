from pyScan import *

pyscan=Scan()



indict1={}
indict1['Knob']=['MA-SARUN04-UIND030-MOT:X-SET']
indict1['KnobReadback']=['MA-SARUN04-UIND030-MOT:X-SET']
indict1['KnobTolerance']=[0.01]
indict1['KnobWaiting']=[10]
#indict0['KnobWaitingExtra']=0

indict1['ScanRange']=[[-0.3,0.3]]
indict1['Nstep']=10

#indict1['StepSize']=
#indict1['Scan Values']=


indict1['Observable']=['MA-SARUN06-DBPM070:X','MA-SARUN06-DBPM070:Y']

indict1['Waiting']=0.1
indict1['Validation']=['MA-SARUN06-DBPM070:POS-VALID','MA-SARUN06-DBPM070:Q-VALID']

indict1['NumberOfMeasurements']=3

indict1['Monitor']=['MA-SINSS-LPSA:SHUTTER']
indict1['MonitorValue']=['Open']
indict1['MonitorTolerance']=[0]
indict1['MonitorAction']=['WaitAndAbort']
indict1['MonitorTimeout']=[5]


indict1['PreAction']=[['MA-SARUN04-MQUA020-MOT:X','MA-SARUN04-MQUA020-MOT:X',1,0.1,10]]
#indict1['PreActionWaiting']=0
#indict1['PreActionOrder']=0

indict1['PostAction']=[['MA-SARUN04-MQUA020-MOT:X','MA-SARUN04-MQUA020-MOT:X',0,0,10]]

indict0={}
indict0['Knob']=['MA-SARUN04-UIND030-MOT:Y-SET']
indict0['KnobReadback']=['MA-SARUN04-UIND030-MOT:Y-SET']
indict0['KnobTolerance']=[0.01]
indict0['KnobWaiting']=[10]
indict0['ScanRange']=[[-0.2,0.2]]
indict0['Nstep']=4

outdict=pyscan.initializeScan([indict0,indict1])

print outdict['ErrorMessage']
print indict1['KnobExpanded']

outdict=pyscan.startScan()


for o in  outdict['Observable']:
    print o


#print pyscan.outdict['KnobReadback']
outdict=pyscan.initializeScan([indict0,indict1])
outdict=pyscan.startScan()


#for o in  outdict['Observable']:
#    print o



print outdict['Validation']
