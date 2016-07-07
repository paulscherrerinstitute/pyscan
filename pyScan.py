import sys


from PyQt4.QtCore import *
from PyQt4.QtGui import *

import PyCafe

import numpy as np
from time import sleep
from datetime import datetime
from copy import deepcopy

import threading as thr



class SubPanelContents(QDialog):
    def __init__(self, parent=None):
        super(SubPanelContents, self).__init__(parent)
        self.exitbutton=QPushButton('Abort measurement')
        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)

        self.connect(self.exitbutton, SIGNAL("ex"), self.vis)
        self.appearing=1

        self.connect(self.exitbutton, SIGNAL("pb"), self.updatePB)
        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)

        self.abortScan=0
        self.connect(self.exitbutton, SIGNAL("clicked()"), self.abort)


    def abort(self):
        self.abortScan=1

    def updatePB(self):
        self.pbar.setValue(self.Progress)


    def vis(self):
        'Dummy'


class SubPanel(QDialog):
    def __init__(self, parent=None):
        super(SubPanel, self).__init__(parent)
        self.exitbutton=QPushButton('Abort measurement')

        self.connect(self.exitbutton, SIGNAL("ex"), self.vis)
        self.appearing=1

        self.connect(self.exitbutton, SIGNAL("pb"), self.updatePB)
        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)

        self.abortScan=0
        self.connect(self.exitbutton, SIGNAL("clicked()"), self.abort)

        layout=QGridLayout()
        layout.addWidget(self.pbar,0,0)

        layout.addWidget(self.exitbutton,1,0)
        layout.addWidget(QLabel("Don't close this window but use the button above to abort the measurement."),2,0)

        self.setLayout(layout)

        self.setWindowTitle("pyScan progress")

    def abort(self):
        self.abortScan=1

    def updatePB(self):
        self.pbar.setValue(self.Progress)


    def vis(self):
        if self.appearing==0:
            self.setVisible(False)
        else:
            self.setVisible(True)



class Scan:
    def __init__(self,fromGUI=0):
        
        self.fromGUI=fromGUI

        if fromGUI:
            self.ProgDisp=SubPanel()
            #self.ProgDisp.show()
            self.ProgDisp.setVisible(False)
        else:
            self.ProgDisp=None
           
            #self.launchPanel()
            #sleep(3.0)
            #self.showPanel(0)


        self.abortScan=0
        self.pauseScan=0


    def Panel(self):
        app=QApplication(sys.argv)
        self.ProgDisp=SubPanel()
        self.ProgDisp.show()
        app.exec_()

    def launchPanel(self): 
        self.thrUpdate = thr.Thread(target=self.Panel)
        self.thrUpdate.setDaemon(True)
        self.thrUpdate.start()
        sleep(3.0)

    def showPanel(self,s):
        self.ProgDisp.appearing=s

        self.ProgDisp.exitbutton.emit(SIGNAL("ex"))        



    def addGroup(self,GroupName,ChList):
        self.cafe.openGroupPrepare()
        h=self.cafe.grouping(GroupName, ChList) # Grouping does GroupOpen
        #pvg=self.cafe.getPVGroup(GroupName)
        #pvg.show()
        #h=self.cafe.groupOpen(GroupName) # Grouping does GroupOpen
        self.cafe.openGroupNowAndWait(1.0)
        #sleep(1.0)
        return h
        


    def finalizeScan(self):
 
        #for h in self.MonitorRunning:
        #    self.cafe.close(h)
        #self.MonitorRunning=[]
        #self.cafe.terminate()
        #del(self.cafe)
        
        self.cafe.groupClose('All')
        if self.inlist[-1]['Monitor']:
            self.cafe.groupClose('Monitor')


        self.outdict['ErrorMessage']='Measurement finalized (finished/aborted) normally. Need initialisation before next measruement.'

        if self.fromGUI:
            self.showPanel(0)

    def initializeScan(self,inlist):
        self.cafe=PyCafe.CyCafe()
        self.cafe.init()
        self.cyca=PyCafe.CyCa()

        self.inlist=[]
        self.outdict={}
        self.outdict['ErrorMessage']=None


        if not isinstance(inlist,list): # It is a simple SKS or MKS
            inlist=[inlist]



        for i in range(0,len(inlist)):
            dic=inlist[i]

            dic['ID']=i # Just in case there are identical input dictionaries. (Normally, it may not happen.)


            if 'Knob' not in dic.keys():
                self.outdict['ErrorMessage']='Knob for the scan was not given for the input dictionary'+str(i)+'.'
                return self.outdict
            else:
                if not isinstance(dic['Knob'],list):
                    dic['Knob']=[dic['Knob']]

            if 'KnobReadback' not in dic.keys():
                dic['KnobReadback']=dic['Knob']
            if not isinstance(dic['KnobReadback'],list):
                dic['KnobReadback']=[dic['KnobReadback']]
            if len(dic['KnobReadback'])!=len(dic['Knob']):
                self.outdict['ErrorMessage']='The number of KnobReadback does not meet to the number of Knobs.'
                return self.outdict

            if 'KnobTolerance' not in dic.keys():
                dic['KnobTolerance']=[1.0]*len(dic['Knob'])
            if not isinstance(dic['KnobTolerance'],list):
                dic['KnobTolerance']=[dic['KnobTolerance']]
            if len(dic['KnobTolerance'])!=len(dic['Knob']):
                    self.outdict['ErrorMessage']='The number of KnobTolerance does not meet to the number of Knobs.'
                    return self.outdict
            
            if 'KnobWaiting' not in dic.keys():
                dic['KnobWaiting']=[10.0]*len(dic['Knob'])
            if not isinstance(dic['KnobWaiting'],list):
                dic['KnobWaiting']=[dic['KnobWaiting']]
            if len(dic['KnobWaiting'])!=len(dic['Knob']):
                    self.outdict['ErrorMessage']='The number of KnobWaiting does not meet to the number of Knobs.'
                    return self.outdict
                 
            if 'KnobWaitingExtra' not in dic.keys():
                dic['KnobWaitingExtra']=0.0
            else:
                try:
                    dic['KnobWaitingExtra']=float(dic['KnobWaitingExtra'])
                except:
                    self.outdict['ErrorMessage']='KnobWaitingExtra is not a number in the input dictionary '+str(i)+'.'
                    return self.outdict

            
            TempHandle=self.addGroup(str(i),dic['Knob'])
            [dic['KnobSaved'],summary,status]=self.cafe.getGroup(TempHandle)
            self.cafe.groupClose(TempHandle)
            
            
            if 'Series' not in dic.keys():
                dic['Series']=0
                
            if not dic['Series']: # Setting up scan values for SKS and MKS
                if 'ScanValues' not in dic.keys():
                    if 'ScanRange' not in dic.keys():
                        self.outdict['ErrorMessage']='Neither ScanRange nor ScanValues is given in the input dictionary '+str(i)+'.'
                        return self.outdict
                    elif not isinstance(dic['ScanRange'],list):
                        self.outdict['ErrorMessage']='ScanRange is not given in the right format. Input dictionary '+str(i)+'.'
                        return self.outdict
                    elif not isinstance(dic['ScanRange'][0],list): 
                        dic['ScanRange']=[dic['ScanRange']]

                    if ('Nstep' not in dic.keys()) and ('StepSize' not in dic.keys()):
                        self.outdict['ErrorMessage']='Neither Nstep nor StepSize is given.'
                        return self.outdict

                    if 'Nstep' in dic.keys(): # StepSize is ignored when Nstep is given
                        if not isinstance(dic['Nstep'],int): 
                            self.outdict['ErrorMessage']='Nstep should be an integer. Input dictionary '+str(i)+'.'
                            return self.outdict
                        ran=[]
                        for r in dic['ScanRange']:
                            s=(r[1]-r[0])/(dic['Nstep']-1)
                            f=np.arange(r[0],r[1],s)
                            f=np.append(f,np.array(r[1]))
                            ran.append(f.tolist())
                        dic['KnobExpanded']=ran
                    else: # StepSize given
                        if len(dic['Knob'])>1:
                            self.outdict['ErrorMessage']='Give Nstep instead of StepSize for MKS. Input dictionary '+str(i)+'.'
                            return self.outdict
                        # StepSize is only valid for SKS
                        r=dic['ScanRange'][0]
                        f=np.arange(r[0],r[1],s)
                        f=np.append(f,np.array(r[1]))
                        dic['Nstep']=len(f)
                        #dic['KnobExpanded']=[f]
                        dic['KnobExpanded']=[f.tolist()]
                else:
                    if not isinstance(dic['ScanValues'],list):
                        self.outdict['ErrorMessage']='ScanValues is not given in the right fromat. Input dictionary '+str(i)+'.'
                        return self.outdict


                    if len(dic['ScanValues'])!=len(dic['Knob']) and len(dic['Knob'])!=1:
                        self.outdict['ErrorMessage']='The length of ScanValues does not meet to the number of Knobs.'
                        return self.outdict


                    if len(dic['Knob'])>1:
                        minlen=100000
                        for r in dic['ScanValues']:
                            if minlen>len(r):
                                minlen=len(r)
                        ran=[]
                        for r in dic['ScanValues']:    
                            ran.append(r[0:minlen]) # Cut at the length of the shortest list.
                        dic['KnobExpanded']=ran
                        dic['Nstep']=minlen
                    else:
                        dic['KnobExpanded']=[dic['ScanValues']]
                        dic['Nstep']=len(dic['ScanValues'])
            else: # Setting up scan values for Series scan
                if 'ScanValues' not in dic.keys():
                    self.outdict['ErrorMessage']='ScanValues should be given for Series scan in the input dictionary '+str(i)+'.'
                    return self.outdict

                if not isinstance(dic['ScanValues'],list):
                    self.outdict['ErrorMessage']='ScanValues should be given as a list (of lists) for Series scan in the input dictionary '+str(i)+'.'
                    return self.outdict
                
                if len(dic['Knob'])!=len(dic['ScanValues']):
                    self.outdict['ErrorMessage']='Scan values length does not match to the number of knobs in the input dictionary '+str(i)+'.'
                    return self.outdict
                    

                Nstep=[]
                for vl in dic['ScanValues']:
                    if not isinstance(vl,list):
                        self.outdict['ErrorMessage']='ScanValue element should be given as a list for Series scan in the input dictionary '+str(i)+'.'
                        return self.outdict
                    Nstep.append(len(vl))
                dic['Nstep']=Nstep

                

            # End of scan values set up



            if inlist.index(dic)==len(inlist)-1 and ('Observable' not in dic.keys()):
                self.outdict['ErrorMessage']='The observable is not given.'
                return self.outdict
            elif inlist.index(dic)==len(inlist)-1:
                if not isinstance(dic['Observable'],list):
                    dic['Observable']=[dic['Observable']]

            if inlist.index(dic)==len(inlist)-1 and ('NumberOfMeasurements' not in dic.keys()):
                dic['NumberOfMeasurements']=1

            
            if 'PreAction' in dic.keys():
                if not isinstance(dic['PreAction'],list):
                    self.outdict['ErrorMessage']='PreAction should be a list. Input dictionary '+str(i)+'.' 
                    return self.outdict
                for l in dic['PreAction']:
                    if not isinstance(l,list):
                        self.outdict['ErrorMessage']='Every PreAction should be a list. Input dictionary '+str(i)+'.' 
                        return self.outdict
                    if len(l)!=5:
                        if not l[0]=='SpecialAction':
                            self.outdict['ErrorMessage']='Every PreAction should be in a form of [Ch-set, Ch-read, Value, Tolerance, Timeout]. Input dictionary '+str(i)+'.' 
                            return self.outdict

                if 'PreActionWaiting' not in dic.keys():
                    dic['PreActionWaiting']=0.0
                if not isinstance(dic['PreActionWaiting'],float) and not isinstance(dic['PreActionWaiting'],int):
                    self.outdict['ErrorMessage']='PreActionWating should be a float. Input dictionary '+str(i)+'.' 
                    return self.outdict
                
                if 'PreActionOrder' not in dic.keys():
                    dic['PreActionOrder']=[0]*len(dic['PreAction'])
                if not isinstance(dic['PreActionOrder'],list):
                    self.outdict['ErrorMessage']='PreActionOrder should be a list. Input dictionary '+str(i)+'.' 
                    return self.outdict

            else:
                dic['PreAction']=[]
                dic['PreActionWaiting']=0.0
                dic['PreActionOrder']=[0]*len(dic['PreAction'])

            if 'In-loopPreAction' in dic.keys():
                if not isinstance(dic['In-loopPreAction'],list):
                    self.outdict['ErrorMessage']='In-loopPreAction should be a list. Input dictionary '+str(i)+'.' 
                    return self.outdict
                for l in dic['In-loopPreAction']:
                    if not isinstance(l,list):
                        self.outdict['ErrorMessage']='Every In-loopPreAction should be a list. Input dictionary '+str(i)+'.' 
                        return self.outdict
                    if len(l)!=5:
                        if not l[0]=='SpecialAction':
                            self.outdict['ErrorMessage']='Every In-loopPreAction should be in a form of [Ch-set, Ch-read, Value, Tolerance, Timeout]. Input dictionary '+str(i)+'.' 
                            return self.outdict

                if 'In-loopPreActionWaiting' not in dic.keys():
                    dic['In-loopPreActionWaiting']=0.0
                if not isinstance(dic['In-loopPreActionWaiting'],float) and not isinstance(dic['In-loopPreActionWaiting'],int):
                    self.outdict['ErrorMessage']='In-loopPreActionWating should be a float. Input dictionary '+str(i)+'.' 
                    return self.outdict
                
                if 'In-loopPreActionOrder' not in dic.keys():
                    dic['In-loopPreActionOrder']=[0]*len(dic['In-loopPreAction'])
                if not isinstance(dic['In-loopPreActionOrder'],list):
                    self.outdict['ErrorMessage']='In-loopPreActionOrder should be a list. Input dictionary '+str(i)+'.' 
                    return self.outdict

            else:
                dic['In-loopPreAction']=[]
                dic['In-loopPreActionWaiting']=0.0
                dic['In-loopPreActionOrder']=[0]*len(dic['In-loopPreAction'])



            if 'PostAction' in dic.keys():
                if dic['PostAction']=='Restore':
                    PA=[]
                    for i in range(0,len(dic['Knob'])):
                        k = dic['Knob'][i]
                        v = dic['KnobSaved'][i]
                        PA.append([k,k,v,1.0,10])
                    dic['PostAction']=PA
                elif not isinstance(dic['PostAction'],list):
                    self.outdict['ErrorMessage']='PostAction should be a list. Input dictionary '+str(i)+'.' 
                    return self.outdict
                Restore=0
                for i in range(0,len(dic['PostAction'])):
                    l=dic['PostAction'][i]
                    if l=='Restore':
                        Restore=1
                        PA=[]
                        for j in range(0,len(dic['Knob'])):
                            k = dic['Knob'][j]
                            v = dic['KnobSaved'][j]
                            PA.append([k,k,v,1.0,10])
                        #dic['PostAction'][i]=PA
                    elif not isinstance(l,list):
                        self.outdict['ErrorMessage']='Every PostAction should be a list. Input dictionary '+str(i)+'.' 
                        return self.outdict
                    elif len(l)!=5:
                        if not l[0]=='SpecialAction':
                            self.outdict['ErrorMessage']='Every PostAction should be in a form of [Ch-set, Ch-read, Value, Tolerance, Timeout]. Input dictionary '+str(i)+'.' 
                            return self.outdict
                if Restore:
                    dic['PostAction'].remove('Restore')
                    dic['PostAction']=dic['PostAction']+PA

            else:
                dic['PostAction']=[]

            if 'In-loopPostAction' in dic.keys():
                if dic['In-loopPostAction']=='Restore':
                    PA=[]
                    for i in range(0,len(dic['Knob'])):
                        k = dic['Knob'][i]
                        v = dic['KnobSaved'][i]
                        PA.append([k,k,v,1.0,10])
                    dic['In-loopPostAction']=PA
                elif not isinstance(dic['In-loopPostAction'],list):
                    self.outdict['ErrorMessage']='In-loopPostAction should be a list. Input dictionary '+str(i)+'.' 
                    return self.outdict
                Restore=0
                for i in range(0,len(dic['In-loopPostAction'])):
                    l=dic['In-loopPostAction'][i]
                    if l=='Restore':
                        Restore=1
                        PA=[]
                        for j in range(0,len(dic['Knob'])):
                            k = dic['Knob'][j]
                            v = dic['KnobSaved'][j]
                            PA.append([k,k,v,1.0,10])
                        dic['In-loopPostAction'][i]=PA
                    elif not isinstance(l,list):
                        self.outdict['ErrorMessage']='Every In-loopPostAction should be a list. Input dictionary '+str(i)+'.' 
                        return self.outdict
                    elif len(l)!=5:
                        self.outdict['ErrorMessage']='Every In-loopPostAction should be in a form of [Ch-set, Ch-read, Value, Tolerance, Timeout]. Input dictionary '+str(i)+'.' 
                        return self.outdict
                if Restore:
                    dic['In-loopPostAction'].remove('Restore')
                    dic['In-loopPostAction']=dic['In-loopPostAction']+PA
            else:
                dic['In-loopPostAction']=[]



            if 'Validation' in dic.keys():
                if not isinstance(dic['Validation'],list):
                    self.outdict['ErrorMessage']='Validation should be a list of channels. Input dictionary '+str(i)+'.' 
                    return self.outdict
            else:
                dic['Validation']=[]

     
            if inlist.index(dic)==len(inlist)-1 and ('Monitor' in dic.keys()):
                if isinstance(dic['Monitor'],str):
                    dic['Monitor']=[dic['Monitor']]

                self.MonitorHandle=self.addGroup('Monitor',dic['Monitor'])
                
                if 'MonitorValue' not in dic.keys():
                    #self.outdict['ErrorMessage']='MonitorValue is not give though Monitor is given.' 
                    #return self.outdict
                    #dic['MonitorValue']=[]
                    #for m in dic['Monitor']:
                    #   dic['MonitorValue'].append(self.cafe.get(m))  # Taking MonitorValue from the machine as it is not given.
                    [dic['MonitorValue'],summary,status]=self.cafe.getGroup('Monitor')
                elif not isinstance(dic['MonitorValue'],list):
                    dic['MonitorValue']=[dic['MonitorValue']]
                if len(dic['MonitorValue'])!=len(dic['Monitor']):
                    self.outdict['ErrorMessage']='The length of MonitorValue does not meet to the length of Monitor.' 
                    return self.outdict

                if 'MonitorTolerance' not in dic.keys():
                    dic['MonitorTolerance']=[]
                    [Value,summary,status]=self.cafe.getGroup('Monitor')
                    for v in Value:
                        v=self.cafe.get(m)
                        if isinstance(v,str):
                            dic['MonitorTolerance'].append(None)
                        elif v==0:
                            dic['MonitorTolerance'].append(0.1)
                        else:
                            dic['MonitorTolerance'].append(abs(v*0.1)) # 10% of the current value will be the torelance when not given
                elif not isinstance(dic['MonitorTolerance'],list):
                    dic['MonitorTolerance']=[dic['MonitorTolerance']]
                if len(dic['MonitorTolerance'])!=len(dic['Monitor']):
                    self.outdict['ErrorMessage']='The length of MonitorTolerance does not meet to the length of Monitor.' 
                    return self.outdict
                
                if 'MonitorAction' not in dic.keys():
                    self.outdict['ErrorMessage']='MonitorAction is not give though Monitor is given.' 
                    return self.outdict

                if not isinstance(dic['MonitorAction'],list):
                    dic['MonitorAction']=[dic['MonitorAction']]
                for m in dic['MonitorAction']:
                    if m!='Abort' and  m!='Wait' and m!='WaitAndAbort':
                        self.outdict['ErrorMessage']='MonitorAction shold be Wait, Abort, or WaitAndAbort.' 
                        return self.outdict

                if 'MonitorTimeout' not in dic.keys():
                    dic['MonitorTimeout']=[30.0]*len(dic['Monitor'])
                elif not isinstance(dic['MonitorTimeout'],list):
                    dic['MonitorValue']=[dic['MonitorValue']]
                if len(dic['MonitorValue'])!=len(dic['Monitor']):
                    self.outdict['ErrorMessage']='The length of MonitorValue does not meet to the length of Monitor.' 
                    return self.outdict
                for m in dic['MonitorTimeout']:
                    try:
                        float(m)
                    except:
                        self.outdict['ErrorMessage']='MonitorTimeout shold be a list of float(or int).' 
                        return self.outdict

            elif inlist.index(dic)==len(inlist)-1:
                dic['Monitor']=[]
                dic['MonitorValue']=[]
                dic['MonitorTolerance']=[]
                dic['MonitorAction']=[]
                dic['MonitorTimeout']=[]
                
            #if not dic['Series']:
            #    dic['KnobExpanded']=np.array(dic['KnobExpanded'])

            if 'Additive' not in dic.keys():
                dic['Additive']=0

            if inlist.index(dic)==len(inlist)-1 and ('StepbackOnPause' not in dic.keys()):
                dic['StepbackOnPause']=1
                
            

        self.allch=[]
        self.allchc=[]
        Nrb=0
        for d in inlist:
            self.allch.append(d['KnobReadback'])
            Nrb=Nrb+len(d['KnobReadback'])


        self.allch.append(inlist[-1]['Validation'])
        Nvalid=len(inlist[-1]['Validation'])

        self.allch.append(inlist[-1]['Observable'])
        Nobs=len(inlist[-1]['Observable'])


        self.allchc=[Nrb,Nvalid,Nobs]
        self.allch=[item for sublist in self.allch for item in sublist] # Recursive in one line!
        Handle=self.addGroup('All',self.allch)
        

        self.Ntot=1 # Total number of measurements
        for dic in inlist:
            if not dic['Series']:
                self.Ntot=self.Ntot*dic['Nstep']
            else:
                self.Ntot=self.Ntot*sum(dic['Nstep'])

        self.inlist=inlist
        return self.outdict



    def startMonitor(self,dic):


        def cbMonitor(h):

            def matchValue(h):
                en=self.MonitorInfo[h][1]
                #print ('***********************************')
                #print (HandleList)
                #print (h)
                #print (self.MonitorInfo[h][1])
                #print (en)
                #self.cafe.printHandle(en)
                #print ('***********************************')

                #c=self.cafe.getPVCache(en)
                c=self.cafe.getPVCache(h)
                v=c.value[0]
                if v=='':
                    # To comply with RF-READY-STATUS channle, where ENUM is empty...
                    c=self.cafe.getPVCache(h,dt='int')
                    v=c.value[0]
                #v=self.cafe.get(en)
                if isinstance(v,str):
                    if v==self.MonitorInfo[h][2]:
                        print ('value OK')
                        return 1
                    else:
                        print (en,self.MonitorInfo[h][2],v)
                        print ('value NG')
                        return 0
                elif isinstance(v,int) or isinstance(v,float):
                    if abs(v-self.MonitorInfo[h][2])<=self.MonitorInfo[h][3]:
                        return 1
                    else:
                        print ('value NG')
                        print (v,self.MonitorInfo[h][2],self.MonitorInfo[h][3])
                        return 0
                else:
                    'Return value from getPVCache',v
            
            if matchValue(h):
                self.stopScan[self.MonitorInfo[h][0]]=0
            else:
                #if self.MonitorInfo[h][4]=='Abort':
                #    self.abortScan=1
                self.stopScan[self.MonitorInfo[h][0]]=1


        dic=self.inlist[-1]
        self.stopScan=[0]*len(dic['Monitor'])
        self.MonitorInfo={}

        HandleList=self.cafe.getHandlesFromWithinGroup(self.MonitorHandle)
        #self.cafe.openPrepare()
        for i in range(0,len(HandleList)):
            h=HandleList[i]
            #m=dic['Monitor'][i]
            #h=self.cafe.open(m)
            #self.MonitorRunning.append(h)
            self.MonitorInfo[h]=[i,dic['Monitor'][i],dic['MonitorValue'][i],dic['MonitorTolerance'][i],dic['MonitorAction'][i],dic['MonitorTimeout']]
        #self.cafe.openNowAndWait(2)

        #self.cafe.openMonitorPrepare()
        #for h in self.MonitorRunning:
        #    m0=self.cafe.monitorStart(h, cb=cbMonitor, dbr=self.cyca.CY_DBR_PLAIN, mask=self.cyca.CY_DBE_VALUE)
  
        #self.cafe.openMonitorNowAndWait(2)


        self.cafe.openMonitorPrepare()
        m0=self.cafe.groupMonitorStartWithCBList(self.MonitorHandle, cb=[cbMonitor]*len(dic['Monitor']), dbr=self.cyca.CY_DBR_PLAIN, mask=self.cyca.CY_DBE_VALUE)
        #m0=self.cafe.groupMonitorStart(self.MonitorHandle, cb=[cbMonitor]*len(dic['Monitor']), dbr=self.cyca.CY_DBR_PLAIN, mask=self.cyca.CY_DBE_VALUE)

        self.cafe.openMonitorNowAndWait(2)
        
        
    def PreAction(self,dic,key='PreAction'):

        order=np.array(dic[key+'Order'])
        maxo=order.max()
        mino=order.min()

        stat=0
        for i in range(mino,maxo+1):
            for j in range(0,len(order)):
                od=order[j]
                if i==od:
                    if dic[key][j][0].lower()=='specialaction':
                        self.ObjectSA.SpecialAction(dic[key][j][1])
                    else:
                        chset=dic[key][j][0]
                        chread=dic[key][j][1]
                        val=dic[key][j][2]
                        tol=dic[key][j][3]
                        timeout=dic[key][j][4]
                        if chset.lower()=='match':
                            print ('****************************----')
                            try:
                                status=self.cafe.match(val,chread,tol,timeout,1)
                                print ('--------------',status)
                            except Exception as inst:
                                print ('Exception in preAction')
                                print (inst)
                                stat=1
                                
                        else:
                            try:
                                status=self.cafe.setAndMatch(chset,val,chread,tol,timeout,0)
                                print ('===========',status)
                            except Exception as inst:
                                print ('Exception in preAction')
                                print (inst)
                                stat=1

        sleep(dic[key+'Waiting'])

        return stat # Future development: Give it to output dictionary

    def PostAction(self,dic,key='PostAction'):

        for act in dic[key]:
            if act[0]=='SpecialAction':
                self.ObjectSA.SpecialAction(act[1])
            else:
                chset=act[0]
                chread=act[1]
                val=act[2]
                tol=act[3]
                timeout=act[4]
                try:
                    self.cafe.setAndMatch(chset,val,chread,tol,timeout,0)
                except Exception as inst:
                    print (inst)

    def CrossReference(self,Object):
        self.ObjectSA=Object


    def allocateOutput(self,l=None):
        
        l=[]
        for i in range(0,len(self.inlist)):
            ir=len(self.inlist)-i-1 # Start from the last library
            Nstep=self.inlist[ir]['Nstep']
            if not self.inlist[ir]['Series']:
                ll=[]
                for j in range(0,Nstep):
                    ll.append(deepcopy(l))
                l=ll
            else:
                Nknob=len(self.inlist[ir]['Knob'])
                lll=[]
                for k in range(0,Nknob):
                    ll=[]
                    for j in range(0,Nstep[k]): # Nstep is list for Series scan
                        ll.append(deepcopy(l))
                    lll.append(deepcopy(ll))
                l=lll
                

        return l


    def startScan(self):
        
        if self.outdict['ErrorMessage']:
            if 'After the last scan,' not in self.outdict['ErrorMessage']:
                self.outdict['ErrorMessage']='It seems that the initialization was not successful... No scan was performed.'
            return self.outdict

        self.outdict['TimeStampStart']=datetime.now()

        self.stopScan=[]
        self.abortScan=0
        self.pauseScan=0
        if self.inlist[-1]['Monitor']:
            self.startMonitor(self.inlist[-1])

        # Prealocating the place for the output
        self.outdict['KnobReadback']=self.allocateOutput()
        self.outdict['Validation']=self.allocateOutput()
        self.outdict['Observable']=self.allocateOutput()


        if self.fromGUI:
            self.showPanel(1)
            self.ProgDisp.abortScan=0
            self.ProgDisp.Progress=0
            self.ProgDisp.exitbutton.emit(SIGNAL("pb"))
        self.Ndone=0
        self.Scan(self.outdict['KnobReadback'],self.outdict['Validation'],self.outdict['Observable'],None)
        if self.fromGUI:
            self.showPanel(0)
        self.finalizeScan()

        self.outdict['TimeStampEnd']=datetime.now()
            
        return self.outdict


    def Scan(self,Rback,Valid,Obs,dic=None):        


        

        if dic==None:
            dic=self.inlist[0]

        print ('*****************',dic)
        ind=self.inlist.index(dic)
        if ind!=len(self.inlist)-1:

            if len(dic['PreAction']):
                self.PreAction(dic)

            if not dic['Series']:
                for i in range(0,dic['Nstep']):
                    print ('Dict'+str(ind)+'  Loop'+str(i))

                    #self.cafe.setGroup(dic['KnobHandle'],dic['KnobExpanded'][i])
                    for j in range(0,len(dic['Knob'])): # Replace later with a group method, setAndMatchGroup?
                        if dic['Additive']:
                            KV=np.array(dic['KnobExpanded'][j])+dic['KnobSaved'][j]
                        else:
                            KV=dic['KnobExpanded'][j]
                        try:
                            self.cafe.setAndMatch(dic['Knob'][j],KV[i],dic['KnobReadback'][j],dic['KnobTolerance'][j],dic['KnobWaiting'][j],0)
                        except Exception as inst:
                            print ('Exception in preAction')
                            print (inst)
                    if dic['KnobWaitingExtra']:
                        sleep(dic['KnobWaitingExtra'])
                    self.Scan(Rback[i],Valid[i],Obs[i],self.inlist[ind+1]) # and then going to a deeper layer recursively

                    if self.abortScan:
                        if len(dic['PostAction']):
                            self.PostAction(dic)
                        return
            else: # Series scan 
                
                for i in range(0,len(dic['Knob'])):
                
                  
                    for j in range(0,dic['Nstep'][i]):
                        for k in range(0,len(dic['Knob'])): # Replace later with a group method, setAndMatchGroup?
                            if k==i:
                                if dic['Additive']:
                                    KV=dic['KnobSaved']+dic['ScanValues'][k][j]
                                else:
                                    KV=dic['ScanValues'][k][j]
                            else:
                                KV=dic['KnobSaved'][k]
                            try:
                                self.cafe.setAndMatch(dic['Knob'][k],KV[i],dic['KnobReadback'][j],dic['KnobTolerance'][j],dic['KnobWaiting'][j],0)
                            except Exception as inst:
                                print ('Exception in preAction')
                                print (inst)

                        if dic['KnobWaitingExtra']:
                            sleep(dic['KnobWaitingExtra'])
                          

                        self.Scan(Rback[i][j],Valid[i][j],Obs[i][j],self.inlist[ind+1]) # and then going to a deeper layer recursively

                    if self.abortScan:
                        if len(dic['PostAction']):
                            self.PostAction(dic)
                        return                



            if len(dic['PostAction']):
                self.PostAction(dic)

        else: # The last dictionary is the most inside loop

            if len(dic['PreAction']):
                self.PreAction(dic)            

            if not dic['Series']:

                Iscan=0
                while Iscan<dic['Nstep']:
                    print (Iscan)


                    # set knob for this loop
                    #self.cafe.setGroup(dic['KnobHandle'],dic['KnobExpanded'][i])
                    for j in range(0,len(dic['Knob'])): # Replace later with a group method, setAndMatchGroup?
                        if dic['Additive']:
                            KV=np.array(dic['KnobExpanded'][j])+dic['KnobSaved'][j]
                        else:
                            KV=dic['KnobExpanded'][j]
                        print ('Knob value',dic['KnobSaved'],dic['KnobExpanded'],KV[Iscan])
                        try:
                            self.cafe.setAndMatch(dic['Knob'][j],KV[Iscan],dic['KnobReadback'][j],dic['KnobTolerance'][j],dic['KnobWaiting'][j],0)
                        except Exception as inst:
                            print ('Exception in Scan loop')
                            print (inst)
                    if dic['KnobWaitingExtra']:
                        sleep(dic['KnobWaitingExtra'])

                    if len(dic['In-loopPreAction']):
                        self.PreAction(dic,'In-loopPreAction')            

                    for j in range(0,dic['NumberOfMeasurements']):
                        [v,s,sl]=self.cafe.getGroup('All')
                        if dic['NumberOfMeasurements']>1:
                            if self.allchc[0]==1:
                                Rback[Iscan].append(v[0])
                            else:
                                Rback[Iscan].append(v[0:self.allchc[0]])

                            if len(dic['Validation'])==1:
                                Valid[Iscan].append(v[self.allchc[0]])
                            else:
                                Valid[Iscan].append(v[self.allchc[0]:self.allchc[0]+self.allchc[1]])

                            if len(dic['Observable'])==1:
                                Obs[Iscan].append(v[-1])
                            else:
                                Obs[Iscan].append(v[self.allchc[0]+self.allchc[1]:self.allchc[0]+self.allchc[1]+self.allchc[2]])
                        else:
                            if self.allchc[0]==1:
                                Rback[Iscan]=v[0]
                            else:
                                Rback[Iscan]=v[0:self.allchc[0]]

                            if len(dic['Validation'])==1:
                                Valid[Iscan]=v[self.allchc[0]]
                            else:
                                Valid[Iscan]=v[self.allchc[0]:self.allchc[0]+self.allchc[1]]

                            if len(dic['Observable'])==1:
                                Obs[Iscan]=v[-1]
                            else:
                                Obs[Iscan]=v[self.allchc[0]+self.allchc[1]:self.allchc[0]+self.allchc[1]+self.allchc[2]]



                        sleep(dic['Waiting'])

                    Iscan=Iscan+1
                    self.Ndone=self.Ndone+1

                    Stepback=0
                    count=[0]*len(self.stopScan)
                    k_stop=None
                    p_stop=None
                    while self.stopScan.count(1)+self.pauseScan: # Problem detected in the channel under monitoring
                        ''' 
                        # This is done by the monitor callback
                        for k in range(0,len(self.stopScan)):
                            if self.stopScan[k]:
                                if dic['MonitorAction'][k]=='Abort':
                                    self.abortScan=1
                                else: #elif dic['MonitorAction'][k]=='Wait' or dic['MonitorAction'][k]=='WaitAndAbort':
                                    count=0
                                    while self.stopScan[k]:
                                         en=dic['Monitor'][k]
                                         v=self.cafe.get(en)
                                         if isinstance(v,str):
                                             if v==dic['MonitorValue'][k]:
                                                 print ('value OK', self.stopScan)
                                                 self.stopScan[k]=0
                                             else:
                                                 print ('value NG')
                                         elif isinstance(v,int) or isinstance(v,float):
                                             if abs(v-dic['MonitorValue'][k])<dic['MonitorTolerance'][k]:
                                                 print ('value OK')
                                                 self.stopScan[k]=0
                                             else:
                                                 print ('value NG')
                                         else:
                                             print ('Return value getPVCache',v)
                                         sleep(1.0)
                                         count=count+1
                                         if dic['MonitorAction'][k]=='WaitAndAbort' and count>dic['MonitorTimeout'][k]:
                                             self.abortScan=1
                                             break
                        '''
                        Stepback=1
                        sleep(1.0)
                        for k in range(0,len(self.stopScan)):
                            if self.stopScan[k]:
                                k_stop=k
                                if dic['MonitorAction'][k]=='Abort':
                                    self.abortScan=1
                                count[k]=count[k]+1
                            else:
                                count[k]=0
                            if dic['MonitorAction'][k]=='WaitAndAbort' and count[k]>dic['MonitorTimeout'][k]:
                                self.abortScan=1
                        
                        if self.abortScan:
                            if len(dic['PostAction']):
                                self.PostAction(dic)
                            return
                        print ('Monitor??')
                        print (self.stopScan)
                        if self.pauseScan:
                            p_stop=1



                    if k_stop and dic['MonitorAction'][k_stop]=='WaitAndNoStepBack':
                        # Take the action of the most persisting monitor...
                        Stepback=0

                    if p_stop and not dic['StepbackOnPause']:
                        Stepback=0

                    if Stepback:
                        print ('Stepping back')
                        Iscan=Iscan-1
                        self.Ndone=self.Ndone-1
                        Rback[Iscan].pop()
                        Valid[Iscan].pop()
                        Obs[Iscan].pop()

                    if self.fromGUI and self.ProgDisp.abortScan:
                        self.abortScan=1
                        if len(dic['PostAction']):
                            self.PostAction(dic)
                        return

                    if len(dic['In-loopPostAction']):
                        self.PostAction(dic,'In-loopPostAction')           

                    if self.fromGUI:
                        self.ProgDisp.Progress=100.0*self.Ndone/self.Ntot
                        self.ProgDisp.exitbutton.emit(SIGNAL("pb")) 


            else: # Series scan
                Kscan=0
                while Kscan<len(dic['Knob']):
                    Iscan=0
                    while Iscan<dic['Nstep'][Kscan]:
                        print (Kscan,Iscan)

                        # set knob for this loop
                        #self.cafe.setGroup(dic['KnobHandle'],dic['KnobExpanded'][i])
                        for j in range(0,len(dic['Knob'])): # Replace later with a group method, setAndMatchGroup?
                            if j==Kscan:
                                if dic['Additive']:
                                    KV=dic['KnobSaved'][j]+dic['ScanValues'][j][Iscan]
                                else:
                                    KV=dic['KnobValues'][j][Iscan]
                            else:
                                KV=dic['KnobSaved'][j]
                            try:
                                self.cafe.setAndMatch(dic['Knob'][j],KV,dic['KnobReadback'][j],dic['KnobTolerance'][j],dic['KnobWaiting'][j],0)
                            except Exception as inst:
                                print ('Exception in preAction')
                                print (inst)
                        if dic['KnobWaitingExtra']:
                            sleep(dic['KnobWaitingExtra'])

                        if len(dic['In-loopPreAction']):
                            self.PreAction(dic,'In-loopPreAction')           

                        for j in range(0,dic['NumberOfMeasurements']):
                            [v,s,sl]=self.cafe.getGroup('All')
                            if dic['NumberOfMeasurements']>1:
                                #if len(dic['Knob'])==1: # Maybe a bug
                                if self.allchc[0]==1:
                                    Rback[Kscan][Iscan].append(v[0])
                                else:
                                    Rback[Kscan][Iscan].append(v[0:self.allchc[0]])

                                if len(dic['Validation'])==1:
                                    Valid[Kscan][Iscan].append(v[self.allchc[0]])
                                else:
                                    Valid[Kscan][Iscan].append(v[self.allchc[0]:self.allchc[0]+self.allchc[1]])

                                if len(dic['Observable'])==1:
                                    Obs[Kscan][Iscan].append(v[-1])
                                else:
                                    Obs[Kscan][Iscan].append(v[self.allchc[0]+self.allchc[1]:self.allchc[0]+self.allchc[1]+self.allchc[2]])
                            else:
                                if self.allchc[0]==1:
                                    Rback[Kscan][Iscan]=v[0]
                                else:
                                    Rback[Kscan][Iscan]=v[0:self.allchc[0]]

                                if len(dic['Validation'])==1:
                                    Valid[Kscan][Iscan]=v[self.allchc[0]]
                                else:
                                    Valid[Kscan][Iscan]=v[self.allchc[0]:self.allchc[0]+self.allchc[1]]

                                if len(dic['Observable'])==1:
                                    Obs[Kscan][Iscan]=v[-1]
                                else:
                                    Obs[Kscan][Iscan]=v[self.allchc[0]+self.allchc[1]:self.allchc[0]+self.allchc[1]+self.allchc[2]]



                            sleep(dic['Waiting'])

                        Iscan=Iscan+1
                        self.Ndone=self.Ndone+1

                        Stepback=0
                        count=[0]*len(self.stopScan)
                        k_stop=None
                        p_stop=None
                        while self.stopScan.count(1): # Problem detected in the channel under monitoring
                            for k in range(0,len(self.stopScan)):
                                '''
                                if self.stopScan[k]:
                                    if dic['MonitorAction'][k]=='Abort':
                                        self.abortScan=1
                                    else: #elif dic['MonitorAction'][k]=='Wait' or dic['MonitorAction'][k]=='WaitAndAbort':
                                        count=0
                                        while self.stopScan[k]:
                                             en=dic['Monitor'][k]
                                             v=self.cafe.get(en)
                                             if isinstance(v,str):
                                                 if v==dic['MonitorValue'][k]:
                                                     print ('value OK', self.stopScan)
                                                     self.stopScan[k]=0
                                                 else:
                                                     print ('value NG')
                                             elif isinstance(v,int) or isinstance(v,float):
                                                 if abs(v-dic['MonitorValue'][k])<dic['MonitorTolerance'][k]:
                                                     print ('value OK')
                                                     self.stopScan[k]=0
                                                 else:
                                                     print ('value NG')
                                             else:
                                                 print ('Return value getPVCache',v)
                                             sleep(1.0)
                                             count=count+1
                                             if dic['MonitorAction'][k]=='WaitAndAbort' and count>dic['MonitorTimeout'][k]:
                                                 self.abortScan=1
                                                 break
                            if not dic['MonitorAction'][k]=='WaitAndNoStepBack':
                                Stepback=1
                            if self.abortScan:
                                if len(dic['PostAction']):
                                    self.PostAction(dic)
                                return
                            '''
                            Stepback=1
                            sleep(1.0)
                            for k in range(0,len(self.stopScan)):
                                if self.stopScan[k]:
                                    k_stop=k
                                    if dic['MonitorAction'][k]=='Abort':
                                        self.abortScan=1
                                    count[k]=count[k]+1
                                else:
                                    count[k]=0
                                if dic['MonitorAction'][k]=='WaitAndAbort' and count[k]>dic['MonitorTimeout'][k]:
                                    self.abortScan=1
                            
                            if self.abortScan:
                                if len(dic['PostAction']):
                                    self.PostAction(dic)
                                return

                            if self.pauseScan:
                                p_stop=1

                        if k_stop and dic['MonitorAction'][k_stop]=='WaitAndNoStepBack':
                            Stepback=0

                        if p_stop and not dic['StepbackOnPause']:
                            Stepback=0

                        if Stepback:
                            print ('Stepping back')
                            Iscan=Iscan-1
                            self.Ndone=self.Ndone-1
                            Rback[Iscan].pop()
                            Valid[Iscan].pop()
                            Obs[Iscan].pop()

                        if self.fromGUI and self.ProgDisp.abortScan:
                            self.abortScan=1
                            if len(dic['PostAction']):
                                self.PostAction(dic)
                            return

                        if len(dic['In-loopPostAction']):
                            self.In-loopPostAction(dic)           

                        if fromGUI:
                            self.ProgDisp.Progress=100.0*self.Ndone/self.Ntot
                            self.ProgDisp.exitbutton.emit(SIGNAL("pb")) 
                    Kscan=Kscan+1
                        
            
            if len(dic['PostAction']):
                self.PostAction(dic)
