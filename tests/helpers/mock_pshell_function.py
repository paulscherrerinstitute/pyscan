from pyscan.dal.pshell_dal import PShellFunction


class MockPShellFunction(PShellFunction):
    def __init__(self, script_name, parameters, server_url=None, scan_in_background=None, multiple_parameters=False):
        super(MockPShellFunction, self).__init__(script_name, parameters, server_url,
                                                 scan_in_background, multiple_parameters)

    def _execute_scan(self, execution_parameters):
        # Example data from the test scan.
        return '[[10.0,20.0,50.0,60.0,"/afs/psi.ch/intranet/SF/data/2018/02/06/20180206_' \
               '170413_WireScanMock.h5|x_0001/w_pos","/afs/psi.ch/intranet/SF/data/2018/02/' \
               '06/20180206_170413_WireScanMock.h5|x_0001/blm1"],[10.0,20.0,50.0,60.0,"/' \
               'afs/psi.ch/intranet/SF/data/2018/02/06/20180206_170413_WireScanMock.h5|x' \
               '_0002/w_pos","/afs/psi.ch/intranet/SF/data/2018/02/06/20180206_170413_W' \
               'ireScanMock.h5|x_0002/blm1"],[10.0,20.0,50.0,60.0,"/afs/psi.ch/intranet' \
               '/SF/data/2018/02/06/20180206_170413_WireScanMock.h5|x_0003/w_pos","/afs' \
               '/psi.ch/intranet/SF/data/2018/02/06/20180206_170413_WireScanMock.h5|x_0003/blm1"]]'

    def _load_scan_data(self, data_path):
        return None
