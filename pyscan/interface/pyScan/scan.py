from copy import deepcopy
from datetime import datetime
from time import sleep

import numpy as np

from pyscan.interface.pyScan.dal import PyCafeEpicsDal
from pyscan.interface.pyScan.gui import SubPanel, DummyClass


class Scan:
    def __init__(self, fromGUI=0):

        self.epics_dal = None
        self.fromGUI = fromGUI
        self.outdict = None
        self.n_validations = None
        self.n_observables = None
        self.n_readbacks = None

        if fromGUI:
            self.ProgDisp = SubPanel()
            self.ProgDisp.setVisible(False)
        else:
            self.ProgDisp = DummyClass()

        self.abortScan = 0
        self.pauseScan = 0

    def finalizeScan(self):
        self.epics_dal.groupClose('All')
        if self.inlist[-1]['Monitor']:
            self.epics_dal.groupClose('Monitor')

        print('in pycan finalization', self.epics_dal.groupList())

        self.outdict[
            'ErrorMessage'] = 'Measurement finalized (finished/aborted) normally. ' \
                              'Need initialisation before next measurement.'

        if self.fromGUI:
            self.ProgDisp.showPanel(0)

    def _add_group(self, dic, name, sources, result, close=True):

        temp_handle = self.epics_dal.addGroup(name, sources)
        [output, summary, status] = self.epics_dal.getGroup(temp_handle)
        if summary != 1:  # Something wrong. Try again.
            [output, summary, status] = self.epics_dal.getGroup(temp_handle)
        if summary != 1:
            for si in status:
                if si != 1:
                    wch = sources[status.index(si)]
            self.epics_dal.groupClose(temp_handle)
            raise ValueError('Something wrong in Epics channel: ' + wch)

        if result:
            dic[result] = output

        if close:
            self.epics_dal.groupClose(temp_handle)

    def initializeScan(self, inlist):
        self.epics_dal = PyCafeEpicsDal()

        self.inlist = []

        if not isinstance(inlist, list):  # It is a simple SKS or MKS
            inlist = [inlist]

        try:
            for dic in inlist:
                dic['ID'] = i  # Just in case there are identical input dictionaries. (Normally, it may not happen.)

                if inlist.index(dic) == len(inlist) - 1 and ('Waiting' not in dic.keys()):
                    raise ValueError('Waiting for the scan was not given.')

                if 'Knob' not in dic.keys():
                    raise ValueError('Knob for the scan was not given for the input dictionary' + str(i) + '.')
                else:
                    if not isinstance(dic['Knob'], list):
                        dic['Knob'] = [dic['Knob']]

                if 'KnobReadback' not in dic.keys():
                    dic['KnobReadback'] = dic['Knob']
                if not isinstance(dic['KnobReadback'], list):
                    dic['KnobReadback'] = [dic['KnobReadback']]
                if len(dic['KnobReadback']) != len(dic['Knob']):
                    raise ValueError('The number of KnobReadback does not meet to the number of Knobs.')

                if 'KnobTolerance' not in dic.keys():
                    dic['KnobTolerance'] = [1.0] * len(dic['Knob'])
                if not isinstance(dic['KnobTolerance'], list):
                    dic['KnobTolerance'] = [dic['KnobTolerance']]
                if len(dic['KnobTolerance']) != len(dic['Knob']):
                    raise ValueError('The number of KnobTolerance does not meet to the number of Knobs.')

                if 'KnobWaiting' not in dic.keys():
                    dic['KnobWaiting'] = [10.0] * len(dic['Knob'])
                if not isinstance(dic['KnobWaiting'], list):
                    dic['KnobWaiting'] = [dic['KnobWaiting']]
                if len(dic['KnobWaiting']) != len(dic['Knob']):
                    raise ValueError('The number of KnobWaiting does not meet to the number of Knobs.')

                if 'KnobWaitingExtra' not in dic.keys():
                    dic['KnobWaitingExtra'] = 0.0
                else:
                    try:
                        dic['KnobWaitingExtra'] = float(dic['KnobWaitingExtra'])
                    except:
                        raise ValueError('KnobWaitingExtra is not a number in the input dictionary ' + str(i) + '.')

                self._add_group(dic, str(i), dic['Knob'], 'KnobSaved')

                if 'Series' not in dic.keys():
                    dic['Series'] = 0

                if not dic['Series']:  # Setting up scan values for SKS and MKS
                    if 'ScanValues' not in dic.keys():
                        if 'ScanRange' not in dic.keys():
                            raise ValueError('Neither ScanRange nor ScanValues is given '
                                             'in the input dictionary ' + str(i) + '.')
                        elif not isinstance(dic['ScanRange'], list):
                            raise ValueError('ScanRange is not given in the right format. '
                                             'Input dictionary ' + str(i) + '.')
                        elif not isinstance(dic['ScanRange'][0], list):
                            dic['ScanRange'] = [dic['ScanRange']]

                        if ('Nstep' not in dic.keys()) and ('StepSize' not in dic.keys()):
                            raise ValueError('Neither Nstep nor StepSize is given.')

                        if 'Nstep' in dic.keys():  # StepSize is ignored when Nstep is given
                            if not isinstance(dic['Nstep'], int):
                                raise ValueError('Nstep should be an integer. Input dictionary ' + str(i) + '.')
                            ran = []
                            for r in dic['ScanRange']:
                                s = (r[1] - r[0]) / (dic['Nstep'] - 1)
                                f = np.arange(r[0], r[1], s)
                                f = np.append(f, np.array(r[1]))
                                ran.append(f.tolist())
                            dic['KnobExpanded'] = ran
                        else:  # StepSize given
                            if len(dic['Knob']) > 1:
                                raise ValueError('Give Nstep instead of StepSize for MKS. '
                                                 'Input dictionary ' + str(i) + '.')
                            # StepSize is only valid for SKS
                            r = dic['ScanRange'][0]
                            f = np.arange(r[0], r[1], s)
                            f = np.append(f, np.array(r[1]))
                            dic['Nstep'] = len(f)
                            dic['KnobExpanded'] = [f.tolist()]
                    else:
                        if not isinstance(dic['ScanValues'], list):
                            raise ValueError('ScanValues is not given in the right fromat. '
                                             'Input dictionary ' + str(i) + '.')

                        if len(dic['ScanValues']) != len(dic['Knob']) and len(dic['Knob']) != 1:
                            raise ValueError('The length of ScanValues does not meet to the number of Knobs.')

                        if len(dic['Knob']) > 1:
                            minlen = 100000
                            for r in dic['ScanValues']:
                                if minlen > len(r):
                                    minlen = len(r)
                            ran = []
                            for r in dic['ScanValues']:
                                ran.append(r[0:minlen])  # Cut at the length of the shortest list.
                            dic['KnobExpanded'] = ran
                            dic['Nstep'] = minlen
                        else:
                            dic['KnobExpanded'] = [dic['ScanValues']]
                            dic['Nstep'] = len(dic['ScanValues'])
                else:  # Setting up scan values for Series scan
                    if 'ScanValues' not in dic.keys():
                        raise ValueError('ScanValues should be given for Series '
                                         'scan in the input dictionary ' + str(i) + '.')

                    if not isinstance(dic['ScanValues'], list):
                        raise ValueError('ScanValues should be given as a list (of lists) '
                                         'for Series scan in the input dictionary ' + str(i) + '.')

                    if len(dic['Knob']) != len(dic['ScanValues']):
                        raise ValueError('Scan values length does not match to the '
                                         'number of knobs in the input dictionary ' + str(i) + '.')

                    Nstep = []
                    for vl in dic['ScanValues']:
                        if not isinstance(vl, list):
                            raise ValueError('ScanValue element should be given as a list for '
                                             'Series scan in the input dictionary ' + str(i) + '.')
                        Nstep.append(len(vl))
                    dic['Nstep'] = Nstep

                # End of scan values set up

                if inlist.index(dic) == len(inlist) - 1 and ('Observable' not in dic.keys()):
                    raise ValueError('The observable is not given.')
                elif inlist.index(dic) == len(inlist) - 1:
                    if not isinstance(dic['Observable'], list):
                        dic['Observable'] = [dic['Observable']]

                if inlist.index(dic) == len(inlist) - 1 and ('NumberOfMeasurements' not in dic.keys()):
                    dic['NumberOfMeasurements'] = 1

                if 'PreAction' in dic.keys():
                    if not isinstance(dic['PreAction'], list):
                        raise ValueError('PreAction should be a list. Input dictionary ' + str(i) + '.')
                    for l in dic['PreAction']:
                        if not isinstance(l, list):
                            raise ValueError('Every PreAction should be a list. Input dictionary ' + str(i) + '.')
                        if len(l) != 5:
                            if not l[0] == 'SpecialAction':
                                raise ValueError('Every PreAction should be in a form of '
                                                 '[Ch-set, Ch-read, Value, Tolerance, Timeout]. '
                                                 'Input dictionary ' + str(i) + '.')

                    if 'PreActionWaiting' not in dic.keys():
                        dic['PreActionWaiting'] = 0.0
                    if not isinstance(dic['PreActionWaiting'], float) and not isinstance(dic['PreActionWaiting'], int):
                        raise ValueError('PreActionWating should be a float. Input dictionary ' + str(i) + '.')

                    if 'PreActionOrder' not in dic.keys():
                        dic['PreActionOrder'] = [0] * len(dic['PreAction'])
                    if not isinstance(dic['PreActionOrder'], list):
                        raise ValueError('PreActionOrder should be a list. Input dictionary ' + str(i) + '.')

                else:
                    dic['PreAction'] = []
                    dic['PreActionWaiting'] = 0.0
                    dic['PreActionOrder'] = [0] * len(dic['PreAction'])

                if 'In-loopPreAction' in dic.keys():
                    if not isinstance(dic['In-loopPreAction'], list):
                        raise ValueError('In-loopPreAction should be a list. Input dictionary ' + str(i) + '.')
                    for l in dic['In-loopPreAction']:
                        if not isinstance(l, list):
                            raise ValueError('Every In-loopPreAction should be a list. '
                                             'Input dictionary ' + str(i) + '.')
                        if len(l) != 5:
                            if not l[0] == 'SpecialAction':
                                raise ValueError('Every In-loopPreAction should be in a form of '
                                                 '[Ch-set, Ch-read, Value, Tolerance, Timeout]. '
                                                 'Input dictionary ' + str(i) + '.')

                    if 'In-loopPreActionWaiting' not in dic.keys():
                        dic['In-loopPreActionWaiting'] = 0.0
                    if not isinstance(dic['In-loopPreActionWaiting'], float) and not isinstance(
                            dic['In-loopPreActionWaiting'], int):
                        raise ValueError('In-loopPreActionWating should be a float. Input dictionary ' + str(i) + '.')

                    if 'In-loopPreActionOrder' not in dic.keys():
                        dic['In-loopPreActionOrder'] = [0] * len(dic['In-loopPreAction'])
                    if not isinstance(dic['In-loopPreActionOrder'], list):
                        raise ValueError('In-loopPreActionOrder should be a list. Input dictionary ' + str(i) + '.')

                else:
                    dic['In-loopPreAction'] = []
                    dic['In-loopPreActionWaiting'] = 0.0
                    dic['In-loopPreActionOrder'] = [0] * len(dic['In-loopPreAction'])

                if 'PostAction' in dic.keys():
                    if dic['PostAction'] == 'Restore':
                        PA = []
                        for i in range(0, len(dic['Knob'])):
                            k = dic['Knob'][i]
                            v = dic['KnobSaved'][i]
                            PA.append([k, k, v, 1.0, 10])
                        dic['PostAction'] = PA
                    elif not isinstance(dic['PostAction'], list):
                        raise ValueError('PostAction should be a list. Input dictionary ' + str(i) + '.')
                    Restore = 0
                    for i in range(0, len(dic['PostAction'])):
                        l = dic['PostAction'][i]
                        if l == 'Restore':
                            Restore = 1
                            PA = []
                            for j in range(0, len(dic['Knob'])):
                                k = dic['Knob'][j]
                                v = dic['KnobSaved'][j]
                                PA.append([k, k, v, 1.0, 10])
                        elif not isinstance(l, list):
                            raise ValueError('Every PostAction should be a list. Input dictionary ' + str(i) + '.')
                        elif len(l) != 5:
                            if not l[0] == 'SpecialAction':
                                raise ValueError('Every PostAction should be in a form of '
                                                 '[Ch-set, Ch-read, Value, Tolerance, Timeout]. '
                                                 'Input dictionary ' + str(i) + '.')
                    if Restore:
                        dic['PostAction'].remove('Restore')
                        dic['PostAction'] = dic['PostAction'] + PA

                else:
                    dic['PostAction'] = []

                if 'In-loopPostAction' in dic.keys():
                    if dic['In-loopPostAction'] == 'Restore':
                        PA = []
                        for i in range(0, len(dic['Knob'])):
                            k = dic['Knob'][i]
                            v = dic['KnobSaved'][i]
                            PA.append([k, k, v, 1.0, 10])
                        dic['In-loopPostAction'] = PA
                    elif not isinstance(dic['In-loopPostAction'], list):
                        raise ValueError('In-loopPostAction should be a list. Input dictionary ' + str(i) + '.')
                    Restore = 0
                    for i in range(0, len(dic['In-loopPostAction'])):
                        l = dic['In-loopPostAction'][i]
                        if l == 'Restore':
                            Restore = 1
                            PA = []
                            for j in range(0, len(dic['Knob'])):
                                k = dic['Knob'][j]
                                v = dic['KnobSaved'][j]
                                PA.append([k, k, v, 1.0, 10])
                            dic['In-loopPostAction'][i] = PA
                        elif not isinstance(l, list):
                            raise ValueError('Every In-loopPostAction should be a list. '
                                             'Input dictionary ' + str(i) + '.')
                        elif len(l) != 5:
                            raise ValueError('Every In-loopPostAction should be in a form of '
                                             '[Ch-set, Ch-read, Value, Tolerance, Timeout]. '
                                             'Input dictionary ' + str(i) + '.')
                    if Restore:
                        dic['In-loopPostAction'].remove('Restore')
                        dic['In-loopPostAction'] = dic['In-loopPostAction'] + PA
                else:
                    dic['In-loopPostAction'] = []

                if 'Validation' in dic.keys():
                    if not isinstance(dic['Validation'], list):
                        raise ValueError('Validation should be a list of channels. Input dictionary ' + str(i) + '.')
                else:
                    dic['Validation'] = []

                if inlist.index(dic) == len(inlist) - 1 and ('Monitor' in dic.keys()) and (dic['Monitor']):
                    if isinstance(dic['Monitor'], str):
                        dic['Monitor'] = [dic['Monitor']]

                    self._add_group(dic, 'Monitor', dic['Monitor'], None)

                    if 'MonitorValue' not in dic.keys():
                        [dic['MonitorValue'], summary, status] = self.epics_dal.getGroup('Monitor')
                    elif not isinstance(dic['MonitorValue'], list):
                        dic['MonitorValue'] = [dic['MonitorValue']]
                    if len(dic['MonitorValue']) != len(dic['Monitor']):
                        raise ValueError('The length of MonitorValue does not meet to the length of Monitor.')

                    if 'MonitorTolerance' not in dic.keys():
                        dic['MonitorTolerance'] = []
                        [Value, summary, status] = self.epics_dal.getGroup('Monitor')
                        for v in Value:
                            v = self.epics_dal.get(m)
                            if isinstance(v, str):
                                dic['MonitorTolerance'].append(None)
                            elif v == 0:
                                dic['MonitorTolerance'].append(0.1)
                            else:
                                dic['MonitorTolerance'].append(
                                    abs(v * 0.1))  # 10% of the current value will be the torelance when not given
                    elif not isinstance(dic['MonitorTolerance'], list):
                        dic['MonitorTolerance'] = [dic['MonitorTolerance']]
                    if len(dic['MonitorTolerance']) != len(dic['Monitor']):
                        raise ValueError('The length of MonitorTolerance does not meet to the length of Monitor.')

                    if 'MonitorAction' not in dic.keys():
                        raise ValueError('MonitorAction is not give though Monitor is given.')

                    if not isinstance(dic['MonitorAction'], list):
                        dic['MonitorAction'] = [dic['MonitorAction']]
                    for m in dic['MonitorAction']:
                        if m != 'Abort' and m != 'Wait' and m != 'WaitAndAbort':
                            raise ValueError('MonitorAction shold be Wait, Abort, or WaitAndAbort.')

                    if 'MonitorTimeout' not in dic.keys():
                        dic['MonitorTimeout'] = [30.0] * len(dic['Monitor'])
                    elif not isinstance(dic['MonitorTimeout'], list):
                        dic['MonitorValue'] = [dic['MonitorValue']]
                    if len(dic['MonitorValue']) != len(dic['Monitor']):
                        raise ValueError('The length of MonitorValue does not meet to the length of Monitor.')
                    for m in dic['MonitorTimeout']:
                        try:
                            float(m)
                        except:
                            raise ValueError('MonitorTimeout should be a list of float(or int).')

                elif inlist.index(dic) == len(inlist) - 1:
                    dic['Monitor'] = []
                    dic['MonitorValue'] = []
                    dic['MonitorTolerance'] = []
                    dic['MonitorAction'] = []
                    dic['MonitorTimeout'] = []

                if 'Additive' not in dic.keys():
                    dic['Additive'] = 0

                if inlist.index(dic) == len(inlist) - 1 and ('StepbackOnPause' not in dic.keys()):
                    dic['StepbackOnPause'] = 1

            self.allch = []

            self.n_readbacks = 0
            for d in inlist:
                self.allch.append(d['KnobReadback'])
                self.n_readbacks += len(d['KnobReadback'])

            self.allch.append(inlist[-1]['Validation'])
            self.n_validations = len(inlist[-1]['Validation'])

            self.allch.append(inlist[-1]['Observable'])
            self.n_observables = len(inlist[-1]['Observable'])

            self.allch = [item for sublist in self.allch for item in sublist]  # Recursive in one line!

            self._add_group(dic, 'All', self.allch, None, close=False)

            self.Ntot = 1  # Total number of measurements
            for dic in inlist:
                if not dic['Series']:
                    self.Ntot = self.Ntot * dic['Nstep']
                else:
                    self.Ntot = self.Ntot * sum(dic['Nstep'])

            self.inlist = inlist
            self.ProgDisp.Progress = 0

            # Prealocating the place for the output
            self.outdict = {"ErrorMessage": None,
                            "KnobReadback": self.allocateOutput(),
                            "Validation": self.allocateOutput(),
                            "Observable": self.allocateOutput()}

        except ValueError as e:
            self.outdict = {"ErrorMessage": str(e)}

        return self.outdict

    def startMonitor(self, dic):
        raise NotImplementedError("Monitors not yet supported.")

    #     def cbMonitor(h):
    #         def matchValue(h):
    #             en = self.MonitorInfo[h][1]
    #             c = self.epics_dal.getPVCache(h)
    #             v = c.value[0]
    #             if v == '':
    #                 # To comply with RF-READY-STATUS channle, where ENUM is empty...
    #                 c = self.epics_dal.getPVCache(h, dt='int')
    #                 v = c.value[0]
    #             if isinstance(self.MonitorInfo[h][2], list):  # Monitor value is in list, i.e. several cases are okay
    #                 if v in self.MonitorInfo[h][2]:
    #                     print('value OK')
    #                     return 1
    #                 else:
    #                     print('kkkkkkk', en, self.MonitorInfo[h][2], v)
    #                     print('value NG')
    #                     return 0
    #             elif isinstance(v, str):
    #                 if v == self.MonitorInfo[h][2]:
    #                     print('value OK')
    #                     return 1
    #                 else:
    #                     print('nnnnn', en, self.MonitorInfo[h][2], v)
    #                     print('value NG')
    #                     return 0
    #
    #             elif isinstance(v, int) or isinstance(v, float):
    #                 if abs(v - self.MonitorInfo[h][2]) <= self.MonitorInfo[h][3]:
    #                     return 1
    #                 else:
    #                     print('value NG')
    #                     print(v, self.MonitorInfo[h][2], self.MonitorInfo[h][3])
    #                     return 0
    #             else:
    #                 'Return value from getPVCache', v
    #
    #         if matchValue(h):
    #             self.stopScan[self.MonitorInfo[h][0]] = 0
    #         else:
    #             self.stopScan[self.MonitorInfo[h][0]] = 1
    #
    #     dic = self.inlist[-1]
    #     self.stopScan = [0] * len(dic['Monitor'])
    #     self.MonitorInfo = {}
    #
    #     HandleList = self.epics_dal.getHandlesFromWithinGroup(self.MonitorHandle)
    #     # self.cafe.openPrepare()
    #     for i in range(0, len(HandleList)):
    #         h = HandleList[i]
    #         self.MonitorInfo[h] = [i, dic['Monitor'][i], dic['MonitorValue'][i], dic['MonitorTolerance'][i],
    #                                dic['MonitorAction'][i], dic['MonitorTimeout']]
    #
    #     self.epics_dal.openMonitorPrepare()
    #     m0 = self.epics_dal.groupMonitorStartWithCBList(self.MonitorHandle, cb=[cbMonitor] * len(dic['Monitor']))
    #
    #     self.epics_dal.openMonitorNowAndWait(2)

    def PreAction(self, dic, key='PreAction'):

        order = np.array(dic[key + 'Order'])
        maxo = order.max()
        mino = order.min()

        stat = 0
        for i in range(mino, maxo + 1):
            for j in range(0, len(order)):
                od = order[j]
                if i == od:
                    if dic[key][j][0].lower() == 'specialaction':
                        self.ObjectSA.SpecialAction(dic[key][j][1])
                    else:
                        chset = dic[key][j][0]
                        chread = dic[key][j][1]
                        val = dic[key][j][2]
                        tol = dic[key][j][3]
                        timeout = dic[key][j][4]
                        if chset.lower() == 'match':
                            print('****************************----')
                            try:
                                status = self.epics_dal.match(val, chread, tol, timeout, 1)
                                print('--------------', status)
                            except Exception as inst:
                                print('Exception in preAction')
                                print(inst)
                                stat = 1

                        else:
                            try:
                                status = self.epics_dal.setAndMatch(chset, val, chread, tol, timeout, 0)
                                print('===========', status)
                            except Exception as inst:
                                print('Exception in preAction')
                                print(inst)
                                stat = 1

        sleep(dic[key + 'Waiting'])

        return stat  # Future development: Give it to output dictionary

    def PostAction(self, dic, key='PostAction'):

        for act in dic[key]:
            if act[0] == 'SpecialAction':
                self.ObjectSA.SpecialAction(act[1])
            else:
                chset = act[0]
                chread = act[1]
                val = act[2]
                tol = act[3]
                timeout = act[4]
                try:
                    self.epics_dal.setAndMatch(chset, val, chread, tol, timeout, 0)
                except Exception as inst:
                    print(inst)

    def CrossReference(self, Object):
        self.ObjectSA = Object

    def allocateOutput(self, l=None):

        l = []
        for i in range(0, len(self.inlist)):
            ir = len(self.inlist) - i - 1  # Start from the last library
            Nstep = self.inlist[ir]['Nstep']
            if not self.inlist[ir]['Series']:
                ll = []
                for j in range(0, Nstep):
                    ll.append(deepcopy(l))
                l = ll
            else:
                Nknob = len(self.inlist[ir]['Knob'])
                lll = []
                for k in range(0, Nknob):
                    ll = []
                    for j in range(0, Nstep[k]):  # Nstep is list for Series scan
                        ll.append(deepcopy(l))
                    lll.append(deepcopy(ll))
                l = lll

        return l

    def startScan(self):

        if self.outdict['ErrorMessage']:
            if 'After the last scan,' not in self.outdict['ErrorMessage']:
                self.outdict[
                    'ErrorMessage'] = 'It seems that the initialization was not successful... No scan was performed.'
            return self.outdict

        self.outdict['TimeStampStart'] = datetime.now()

        self.stopScan = []
        self.abortScan = 0
        self.pauseScan = 0

        if self.inlist[-1]['Monitor']:
            self.startMonitor(self.inlist[-1])

        if self.fromGUI:
            self.ProgDisp.showPanel(1)
            self.ProgDisp.abortScan = 0
            self.ProgDisp.emit("pb")

        self.Ndone = 0
        self.Scan(self.outdict['KnobReadback'], self.outdict['Validation'], self.outdict['Observable'], None)

        if self.fromGUI:
            self.ProgDisp.showPanel(0)
        self.finalizeScan()

        self.outdict['TimeStampEnd'] = datetime.now()

        return self.outdict

    def Scan(self, Rback, Valid, Obs, dic=None):

        if dic == None:
            dic = self.inlist[0]

        print('*****************', dic)
        ind = self.inlist.index(dic)

        # Execute pre actions.
        if len(dic['PreAction']):
            self.PreAction(dic)

        if ind != len(self.inlist) - 1:

            if not dic['Series']:
                self.range_scan(Obs, Rback, Valid, dic, ind)
            else:  # Series scan
                self.series_scan(Obs, Rback, Valid, dic, ind)

        else:  # The last dictionary is the most inside loop

            if not dic['Series']:
                self.last_range_scan(Obs, Rback, Valid, dic)
            else:  # Series scan
                self.last_series_scan(Obs, Rback, Valid, dic)

        # Execute post actions.
        if len(dic['PostAction']):
            self.PostAction(dic)

    def last_series_scan(self, Obs, Rback, Valid, dic):
        Kscan = 0
        while Kscan < len(dic['Knob']):
            Iscan = 0
            while Iscan < dic['Nstep'][Kscan]:
                print(Kscan, Iscan)

                # set knob for this loop
                for j in range(0, len(dic['Knob'])):  # Replace later with a group method, setAndMatchGroup?
                    if j == Kscan:
                        if dic['Additive']:
                            KV = dic['KnobSaved'][j] + dic['ScanValues'][j][Iscan]
                        else:
                            KV = dic['KnobValues'][j][Iscan]
                    else:
                        KV = dic['KnobSaved'][j]
                    try:
                        self.epics_dal.setAndMatch(dic['Knob'][j], KV, dic['KnobReadback'][j],
                                                   dic['KnobTolerance'][j], dic['KnobWaiting'][j], 0)
                    except Exception as inst:
                        print('Exception in preAction')
                        print(inst)
                if dic['KnobWaitingExtra']:
                    sleep(dic['KnobWaitingExtra'])

                if len(dic['In-loopPreAction']):
                    self.PreAction(dic, 'In-loopPreAction')

                for j in range(0, dic['NumberOfMeasurements']):
                    [v, s, sl] = self.epics_dal.getGroup('All')

                    if self.n_readbacks == 1:
                        rback_result = v[0]
                    else:
                        rback_result = v[0:self.n_readbacks]

                    if len(dic['Validation']) == 1:
                        valid_result = v[self.n_readbacks]
                    else:
                        valid_result = v[self.n_readbacks:self.n_readbacks + self.n_validations]

                    if len(dic['Observable']) == 1:
                        obs_result = v[-1]
                    else:
                        obs_result = v[self.n_readbacks + self.n_validations:
                                       self.n_readbacks + self.n_validations + self.n_observables]

                    if dic['NumberOfMeasurements'] > 1:
                        Rback[Kscan][Iscan].append(rback_result)
                        Valid[Kscan][Iscan].append(valid_result)
                        Obs[Kscan][Iscan].append(obs_result)
                    else:
                        Rback[Kscan][Iscan] = rback_result
                        Valid[Kscan][Iscan] = valid_result
                        Obs[Kscan][Iscan] = obs_result

                    sleep(dic['Waiting'])

                Iscan = Iscan + 1
                self.Ndone = self.Ndone + 1

                Stepback = 0
                count = [0] * len(self.stopScan)
                k_stop = None
                p_stop = None
                while self.stopScan.count(1):  # Problem detected in the channel under monitoring
                    for k in range(0, len(self.stopScan)):
                        Stepback = 1
                    sleep(1.0)
                    for k in range(0, len(self.stopScan)):
                        if self.stopScan[k]:
                            k_stop = k
                            if dic['MonitorAction'][k] == 'Abort':
                                self.abortScan = 1
                            count[k] = count[k] + 1
                        else:
                            count[k] = 0
                        if dic['MonitorAction'][k] == 'WaitAndAbort' and count[k] > dic['MonitorTimeout'][k]:
                            self.abortScan = 1

                    if self.abortScan:
                        if len(dic['PostAction']):
                            self.PostAction(dic)
                        raise Exception("Scan aborted")

                    if self.pauseScan:
                        p_stop = 1

                if k_stop and dic['MonitorAction'][k_stop] == 'WaitAndNoStepBack':
                    Stepback = 0

                if p_stop and not dic['StepbackOnPause']:
                    Stepback = 0

                if Stepback:
                    print('Stepping back')
                    Iscan = Iscan - 1
                    self.Ndone = self.Ndone - 1
                    Rback[Iscan].pop()
                    Valid[Iscan].pop()
                    Obs[Iscan].pop()

                if self.fromGUI and self.ProgDisp.abortScan:
                    self.abortScan = 1
                if self.abortScan:
                    if len(dic['PostAction']):
                        self.PostAction(dic)
                    raise Exception("Scan aborted")

                if len(dic['In-loopPostAction']):
                    self.In - loopPostAction(dic)

                self.ProgDisp.Progress = 100.0 * self.Ndone / self.Ntot
                if self.fromGUI:
                    self.ProgDisp.emit("pb")
            Kscan = Kscan + 1

    def last_range_scan(self, Obs, Rback, Valid, dic):
        Iscan = 0
        while Iscan < dic['Nstep']:
            print(Iscan)

            # set knob for this loop
            for j in range(0, len(dic['Knob'])):  # Replace later with a group method, setAndMatchGroup?
                if dic['Additive']:
                    KV = np.array(dic['KnobExpanded'][j]) + dic['KnobSaved'][j]
                else:
                    KV = dic['KnobExpanded'][j]
                print('Knob value', dic['KnobSaved'], dic['KnobExpanded'], KV[Iscan])
                try:
                    self.epics_dal.setAndMatch(dic['Knob'][j], KV[Iscan], dic['KnobReadback'][j],
                                               dic['KnobTolerance'][j], dic['KnobWaiting'][j], 0)
                except Exception as inst:
                    print('Exception in Scan loop')
                    print(inst)
            if dic['KnobWaitingExtra']:
                sleep(dic['KnobWaitingExtra'])

            if len(dic['In-loopPreAction']):
                self.PreAction(dic, 'In-loopPreAction')

            for j in range(0, dic['NumberOfMeasurements']):
                [v, s, sl] = self.epics_dal.getGroup('All')
                if dic['NumberOfMeasurements'] > 1:
                    if self.n_readbacks == 1:
                        Rback[Iscan].append(v[0])
                    else:
                        Rback[Iscan].append(v[0:self.n_readbacks])

                    if len(dic['Validation']) == 1:
                        Valid[Iscan].append(v[self.n_readbacks])
                    else:
                        Valid[Iscan].append(v[self.n_readbacks:self.n_readbacks + self.n_validations])

                    if len(dic['Observable']) == 1:
                        Obs[Iscan].append(v[-1])
                    else:
                        Obs[Iscan].append(
                            v[
                            self.n_readbacks + self.n_validations:self.n_readbacks + self.n_validations + self.n_observables])
                else:
                    if self.n_readbacks == 1:
                        Rback[Iscan] = v[0]
                    else:
                        Rback[Iscan] = v[0:self.n_readbacks]

                    if len(dic['Validation']) == 1:
                        Valid[Iscan] = v[self.n_readbacks]
                    else:
                        Valid[Iscan] = v[self.n_readbacks:self.n_readbacks + self.n_validations]

                    if len(dic['Observable']) == 1:
                        Obs[Iscan] = v[-1]
                    else:
                        Obs[Iscan] = v[self.n_readbacks + self.n_validations:self.n_readbacks + self.n_validations +
                                                                             self.n_observables]

                sleep(dic['Waiting'])

            Iscan = Iscan + 1
            self.Ndone = self.Ndone + 1

            Stepback = 0
            count = [0] * len(self.stopScan)
            k_stop = None
            p_stop = None
            while self.stopScan.count(1) + self.pauseScan:  # Problem detected in the channel under monitoring
                Stepback = 1
                sleep(1.0)
                for k in range(0, len(self.stopScan)):
                    if self.stopScan[k]:
                        k_stop = k
                        if dic['MonitorAction'][k] == 'Abort':
                            self.abortScan = 1
                        count[k] = count[k] + 1
                    else:
                        count[k] = 0
                    if dic['MonitorAction'][k] == 'WaitAndAbort' and count[k] > dic['MonitorTimeout'][k]:
                        self.abortScan = 1

                if self.abortScan:
                    if len(dic['PostAction']):
                        self.PostAction(dic)
                    raise Exception("Scan aborted")
                print('Monitor??')
                print(self.stopScan)
                if self.pauseScan:
                    p_stop = 1

            if k_stop and dic['MonitorAction'][k_stop] == 'WaitAndNoStepBack':
                # Take the action of the most persisting monitor...
                Stepback = 0

            if p_stop and not dic['StepbackOnPause']:
                Stepback = 0

            if Stepback:
                print('Stepping back')
                Iscan = Iscan - 1
                self.Ndone = self.Ndone - 1
                Rback[Iscan].pop()
                Valid[Iscan].pop()
                Obs[Iscan].pop()

            if self.fromGUI and self.ProgDisp.abortScan:
                self.abortScan = 1
            if self.abortScan:
                if len(dic['PostAction']):
                    self.PostAction(dic)
                raise Exception("Scan aborted")

            if len(dic['In-loopPostAction']):
                self.PostAction(dic, 'In-loopPostAction')

            self.ProgDisp.Progress = 100.0 * self.Ndone / self.Ntot
            if self.fromGUI:
                self.ProgDisp.emit("pb")

    def range_scan(self, Obs, Rback, Valid, dic, ind):
        for step_index in range(dic['Nstep']):
            print('Dict' + str(ind) + '  Loop' + str(step_index))

            for knob_index in range(len(dic['Knob'])):
                if dic['Additive']:
                    KV = np.array(dic['KnobExpanded'][knob_index]) + dic['KnobSaved'][knob_index]
                else:
                    KV = dic['KnobExpanded'][knob_index]
                try:
                    set_pv_name = dic['Knob'][knob_index]
                    readback_pv_name = dic['KnobReadback'][knob_index]
                    pv_value = KV[step_index]
                    pv_tolerance = dic['KnobTolerance'][knob_index]
                    pv_wait_time = dic['KnobWaiting'][knob_index]

                    self.epics_dal.setAndMatch(set_pv_name, pv_value, readback_pv_name, pv_tolerance, pv_wait_time, 0)
                except Exception as inst:
                    print('Exception in range_scan')
                    print(inst)

            # Delay between setting the position and reading the values.
            if dic['KnobWaitingExtra']:
                sleep(dic['KnobWaitingExtra'])

            self.Scan(Rback[step_index], Valid[step_index], Obs[step_index], self.inlist[ind + 1])

            if self.abortScan:
                if len(dic['PostAction']):
                    self.PostAction(dic)
                raise Exception("Scan aborted")

    def series_scan(self, Obs, Rback, Valid, dic, ind):
        # For every PV.
        for i in range(0, len(dic['Knob'])):
            # For the number of steps for this PV.
            for step_index in range(dic['Nstep'][i]):
                # For every PV.
                for knob_index in range(len(dic['Knob'])):
                    #
                    if knob_index == i:
                        if dic['Additive']:
                            KV = dic['KnobSaved'] + dic['ScanValues'][knob_index][step_index]
                        else:
                            KV = dic['ScanValues'][knob_index][step_index]
                    else:
                        KV = dic['KnobSaved'][knob_index]
                    try:
                        set_pv_name = dic['Knob'][knob_index]
                        readback_pv_name = dic['KnobReadback'][step_index]
                        pv_value = KV[i]
                        pv_tolerance = dic['KnobTolerance'][step_index]
                        pv_wait_time = dic['KnobWaiting'][step_index]

                        self.epics_dal.setAndMatch(set_pv_name, pv_value, readback_pv_name, pv_tolerance, pv_wait_time,
                                                   0)
                    except Exception as inst:
                        print('Exception in series_scan')
                        print(inst)

                if dic['KnobWaitingExtra']:
                    sleep(dic['KnobWaitingExtra'])

                self.Scan(Rback[i][step_index], Valid[i][step_index], Obs[i][step_index], self.inlist[ind + 1])

            if self.abortScan:
                if len(dic['PostAction']):
                    self.PostAction(dic)
                raise Exception("Scan aborted")
