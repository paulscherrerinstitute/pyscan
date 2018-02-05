from pyscan.dal.pshell_dal import PShellFunction


class MockPShellFunction(PShellFunction):
    def __init__(self, script_name, parameters, server_url=None, scan_in_background=None):
        super(MockPShellFunction, self).__init__(script_name, parameters, server_url, scan_in_background)

    def _execute_scan(self, execution_parameters):
        # Example data from the test scan.
        return '[0.3627235580357685,"2018/02/05/20180205_173200_DataLink.h5 | scan 1/Sensor"]'

    def _load_scan_data(self, data_path):
        # Example data from the test scan.
        return b'\x00\x00\x00\x89{"htype":"bsr_m-1.1","hash":"f7977dd9531f6d52f42371342ea656a8",' \
               b'"global_timestamp":{"sec":1860483,"ns":552702938},"dh_compression":"none"}\x00\x00\x00>' \
               b'{"htype":"bsr_d-1.1","channels":[{"name":"data","shape":[2]}]}\x00\x00\x00\x10\xe9D\x85\x1e8' \
               b'\xc7\xea\xbf\xc3\xa8\xa0\x0f0\xfc\xe7\xbf\x00\x00\x00\x10\x96\x87xZ\x00\x00\x00\x00\xc0V\xfe\x03\
               x00\x00\x00\x00'
