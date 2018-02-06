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

    @staticmethod
    def _load_raw_data(server_url, data_path):
        return b'\x00\x00\x00\x87{"htype":"bsr_m-1.1","hash":"37c5215f52eb7d0aeeb2a520d0c613",' \
               b'"global_timestamp":{"sec":1946920,"ns":787198131},"dh_compression":"none"}' \
               b'\x00\x00\x00?{"htype":"bsr_d-1.1","channels":[{"name":"data","shape":[10]}]}' \
               b'\x00\x00\x00P\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0?\x00' \
               b'\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x08@\x00\x00\x00\x00\x00\x00' \
               b'\x10@\x00\x00\x00\x00\x00\x00\x14@\x00\x00\x00\x00\x00\x00\x18@\x00\x00\x00\x00' \
               b'\x00\x00\x1c@\x00\x00\x00\x00\x00\x00 @\x00\x00\x00\x00\x00\x00"@\x00\x00\x00\x10;' \
               b'\xd9yZ\x00\x00\x00\x00\xc0rL\x12\x00\x00\x00\x00'
