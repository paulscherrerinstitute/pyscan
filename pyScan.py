import sys
sys.path.insert(0, '/afs/psi.ch/intranet/SF/Applications/Development/OnlineModel/lib')
import PyCafe

import numpy as np
from time import sleep
from copy import deepcopy


class Scan:
    def __init__(self):
        #self.cafe=PyCafe.CyCafe()
        #self.cafe.init()
        #self.cyca=PyCafe.CyCa()

        self.MonitorRunning=[]




    def addGroup(self,GroupName,ChList):
        self.cafe.openGroupPrepare()
        h=self.cafe.grouping(GroupName, ChList)
        self.cafe.openGroupNowAndWait(0.1)
        return h
        


    def finalizeScan(self):
        #for dic in self.inlist:
        #    self.cafe.close(dic['KnobHandle'])
            
        #for h in self.MonitorRunning:
        #    self.cafe.close(h)
        self.cafe.terminate()

        self.outdict['ErrorMessage']='After the last scan, no initialization is done.'

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
                self.outdict['ErrorMessage']='Knob for the scan was not givenfor the input dictionary'+str(i)+'.'
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

            
            dic['KnobHandle']=self.addGroup(str(i),dic['Knob'])
            [dic['KnobSaved'],summary,status]=self.cafe.getGroup(dic['KnobHandle'])
            


            if 'ScanValues' not in dic.keys():
                if 'ScanRange' not in dic.keys():
                    self.outdict['ErrorMessage']='Neither ScanRange nor ScanValues is given in the input dictionary '+str(i)+'.'
                    return self.outdict
                elif not isinstance(dic['ScanRange'],list):
                    self.outdict['ErrorMessage']='ScanRange is not given in the right format '+str(i)+'.'
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
                        ran.append(f)
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
                    dic['KnobExpanded']=[f]
            else:
                if not isinstance(dic['ScanValues'],list):
                    self.outdict['ErrorMessage']='ScanValues is not given in the right fromat. Input dictionary '+str(i)+'.'
                    return self.outdict
                if len(dic['ScanValues'])!=len(dic['Knob']):
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
                    dic['Nstep']=len(dic['ScanValues'])

            if inlist.index(dic)==len(inlist)-1 and ('Observable' not in dic.keys()):
                self.outdict['ErrorMessage']='The observable is not given.'
                return self.outdict

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
                        self.outdict['ErrorMessage']='Every PreAction should be in a form of [Ch-set, Ch-read, Value, Tolerance, Timeout]. Input dictionary '+str(i)+'.' 
                        return self.outdict

                if 'PreActionWaiting' not in dic.keys():
                    dic['PreActionWaiting']=0.0
                if not isinstance(dic['PreActionWaiting'],float):
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


            if 'PostAction' in dic.keys():
                if not isinstance(dic['PostAction'],list):
                    self.outdict['ErrorMessage']='PostAction should be a list. Input dictionary '+str(i)+'.' 
                    return self.outdict
                for l in dic['PostAction']:
                    if not isinstance(l,list):
                        self.outdict['ErrorMessage']='Every PostAction should be a list. Input dictionary '+str(i)+'.' 
                        return self.outdict
                    if len(l)!=5:
                        self.outdict['ErrorMessage']='Every PostAction should be in a form of [Ch-set, Ch-read, Value, Tolerance, Timeout]. Input dictionary '+str(i)+'.' 
                        return self.outdict
            else:
                dic['PostAction']=[]

     
            if inlist.index(dic)==len(inlist)-1 and ('Monitor' in dic.keys()):
                if isinstance(dic['Monitor'],str):
                    dic['Monitor']=[dic['Monitor']]
                
                if 'MonitorValue' not in dic.keys():
                    #self.outdict['ErrorMessage']='MonitorValue is not give though Monitor is given.' 
                    #return self.outdict
                    dic['MonitorValue']=[]
                    for m in dic['Monitor']:
                        dic['MonitorValue'].append(self.cafe.get(m))  # Taking MonitorValue from the machine as it is not given.
                elif not isinstance(dic['MonitorValue'],list):
                    dic['MonitorValue']=[dic['MonitorValue']]
                if len(dic['MonitorValue'])!=len(dic['Monitor']):
                    self.outdict['ErrorMessage']='The length of MonitorValue does not meet to the length of Monitor.' 
                    return self.outdict

                if 'MonitorTolerance' not in dic.keys():
                    dic['MonitorTolerance']=[]
                    for m in dic['Monitor']:
                        v=self.cafe.get(m)
                        if isinstance(v,str):
                            dic['MonitorTolerance'].append(None)
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
                

            dic['KnobExpanded']=np.array(dic['KnobExpanded'])


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
        self.allch=[item for sublist in self.allch for item in sublist]
        self.allchh=self.addGroup('All',self.allch)
        

        self.inlist=inlist
        return self.outdict



    def startMonitor(self,dic):


        def cbMonitor(h):

            def matchValue(h):
                en=self.MonitorInfo[h][1]
                c=self.cafe.getPVCache(en)
                v=c.value[0]
                #v=self.cafe.get(en)
                if isinstance(v,str):
                    if v==self.MonitorInfo[h][2]:
                        print 'value OK'
                        return 1
                    else:
                        print 'value NG'
                        return 0
                elif isinstance(v,int) or isinstance(v,float):
                    if abs(v-self.MonitorInfo[h][2])<self.MonitorInfo[h][3]:
                        return 1
                    else:
                        return 0
                else:
                    'Return value from getPVCache',v
            
            if matchValue(h):
                self.stopScan[self.MonitorInfo[h][0]]=0
            else:
                if self.MonitorInfo[h][4]=='Abort':
                    self.abortScan=1
                self.stopScan[self.MonitorInfo[h][0]]=1



        dic=self.inlist[-1]
        self.stopScan=[0]*len(dic['Monitor'])
        self.MonitorInfo={}
        self.cafe.openPrepare()
        for i in range(0,len(dic['Monitor'])):
            m=dic['Monitor'][i]
            h=self.cafe.open(m)
            self.MonitorRunning.append(h)
            self.MonitorInfo[h]=[i,dic['Monitor'][i],dic['MonitorValue'][i],dic['MonitorTolerance'][i],dic['MonitorAction'][i],dic['MonitorTimeout']]
        self.cafe.openNowAndWait(2)

        self.cafe.openMonitorPrepare()
        for h in self.MonitorRunning:
            m0=self.cafe.monitorStart(h, cb=cbMonitor, dbr=self.cyca.CY_DBR_PLAIN, mask=self.cyca.CY_DBE_VALUE)
  
        self.cafe.openMonitorNowAndWait(2)

    def PreAction(self,dic):
        order=np.array(dic['PreActionOrder'])
        maxo=order.max()
        mino=order.min()

        for i in range(mino,maxo+1):
            for j in order:
                if i==j:
                    chset=dic['PreAction'][j][0]
                    chread=dic['PreAction'][j][1]
                    val=dic['PreAction'][j][2]
                    tol=dic['PreAction'][j][3]
                    timeout=dic['PreAction'][j][4]
                    self.cafe.setAndMatch(chset,val,chread,tol,timeout,0)
            
        sleep(dic['PreActionWaiting'])

    
    def PostAction(self,dic):

        for act in dic['PostAction']:
            chset=act[0]
            chread=act[1]
            val=act[2]
            tol=act[3]
            timeout=act[4]
            self.cafe.setAndMatch(chset,val,chread,tol,timeout,0)

    def allocateOutput(self,l=None):
        
        l=[]
        for i in range(0,len(self.inlist)):
            N=self.inlist[len(self.inlist)-i-1]['Nstep']
            if i==0:
                l=l*N
            else:
                ll=[]
                for j in range(0,N):
                    ll.append(deepcopy(l))
                l=ll

        return l


    def startScan(self):
        
        if self.outdict['ErrorMessage']:
            if 'After the last scan,' not in self.outdict['ErrorMessage']:
                self.outdict['ErrorMessage']='It seems that the initialization was not successful... No scan was performed.'
            return self.outdict

        self.stopScan=[]
        self.abortScan=0
        if self.inlist[-1]['Monitor']:
            self.startMonitor(self.inlist[-1])

        # Prealocating the place for the output
        self.outdict['KnobReadback']=self.allocateOutput()
        self.outdict['Validation']=self.allocateOutput()
        self.outdict['Observable']=self.allocateOutput()




        self.Scan(self.outdict['KnobReadback'],self.outdict['Validation'],self.outdict['Observable'],None)

        self.finalizeScan()
            
        return self.outdict


    def Scan(self,Rback,Valid,Obs,dic=None):        


        

        if dic==None:
            dic=self.inlist[0]
            print 'kkk'

        print dic
        print '*****************',self.inlist.index(self.inlist[0])
        ind=self.inlist.index(dic)
        if ind!=len(self.inlist)-1:

            if len(dic['PreAction']):
                self.PreAction(dic)

            for i in range(0,dic['Nstep']):
                print 'Dict'+str(ind)+'  Loop'+str(i)
                
                #self.cafe.setGroup(dic['KnobHandle'],dic['KnobExpanded'][i])
                
                for j in range(0,len(dic['Knob'])): # Replace later with a group method (sedAndMatchGroup?)
                    KV=dic['KnobExpanded'][j]
                    self.cafe.setAndMatch(dic['Knob'][j],KV[i],dic['KnobReadback'][j],dic['KnobTolerance'][j],dic['KnobWaiting'][j],0)
                if dic['KnobWaitingExtra']:
                    sleep(dic['KnobWaitingExtra'])
                self.Scan(Rback[i],Valid[i],Obs[i],self.inlist[ind+1]) # and then going to a deeper layer recursively
                if self.abortScan:
                    return

            if len(dic['PostAction']):
                self.PostAction(dic)

        else: # The last dictionary is the most inside loop
            Iscan=0

            if len(dic['PreAction']):
                self.PreAction(dic)            

            while Iscan<dic['Nstep']:
                print Iscan


                # set knob for this loop
                #self.cafe.setGroup(dic['KnobHandle'],dic['KnobExpanded'][i])
                for j in range(0,len(dic['Knob'])): # Replace later with a group method (sedAndMatchGroup?)
                    KV=dic['KnobExpanded'][j]
                    print 'Knob value',KV[Iscan]
                    self.cafe.setAndMatch(dic['Knob'][j],KV[Iscan],dic['KnobReadback'][j],dic['KnobTolerance'][j],dic['KnobWaiting'][j],0)
                if dic['KnobWaitingExtra']:
                    sleep(dic['KnobWaitingExtra'])
         
                    
                for j in range(0,dic['NumberOfMeasurements']):
                    [v,s,sl]=self.cafe.getGroup(self.allchh)
                    Rback.append(v[0:self.allchc[0]])
                    Valid.append(v[self.allchc[0]:self.allchc[0]+self.allchc[1]])
                    if len(dic['Observable'])==1:
                        Obs.append(v[-1])
                    else:
                        Obs.append(v[self.allchc[0]+self.allchc[1]:self.allchc[0]+self.allchc[1]+self.allchc[2]])



                    sleep(dic['Waiting'])

                Iscan=Iscan+1
        
                Stepback=0
                while self.stopScan.count(1): # Problem detected in the channel under monitoring
                    for k in range(0,len(self.stopScan)):
                        if self.stopScan[k]:
                            if dic['MonitorAction'][k]=='Abort':
                                self.abortScan=1
                            elif dic['MonitorAction'][k]=='Wait' or dic['MonitorAction'][k]=='WaitAndAbort':
                                ngflag=1
                                count=0
                                while self.stopScan[k]:
                                     en=dic['Monitor'][k]
                                     v=self.cafe.get(en)
                                     if isinstance(v,str):
                                         if v==dic['MonitorValue'][k]:
                                             print 'value OK', self.stopScan
                                             self.stopScan[k]=0
                                         else:
                                             print 'value NG'
                                     elif isinstance(v,int) or isinstance(v,float):
                                         if abs(v-dic['MonitorValue'][k])<dic['MonitorTolerance'][k]:
                                             print 'value OK'
                                             self.stopScan[k]=0
                                         else:
                                             print 'value NG'
                                     else:
                                         'Return value getPVCache',v
                                     sleep(1.0)
                                     count=count+1
                                     if dic['MonitorAction'][k]=='WaitAndAbort' and count>dic['MonitorTimeout'][k]:
                                         self.abortScan=1
                                         break

                    Stepback=1
                    if self.abortScan:
                        return


                if Stepback:
                    print 'Stpping back'
                    Iscan=Iscan-1
                    Rback.pop()
                    Valid.pop()
                    Obs.pop()


            
            if len(dic['PostAction']):
                self.PostAction(dic)
