from pyscan.dal.pshell_dal import PShellFunction


class MockPShellFunction(PShellFunction):
    def __init__(self, script_name, parameters, server_url=None, scan_in_background=None):
        super(MockPShellFunction, self).__init__(script_name, parameters, server_url, scan_in_background)

    def _execute_scan(self, execution_parameters):
        # Example data from the test scan.
        return '[2,"2018/02/06/20180206_122248_DataLink.h5 | scan 1/Sensor"]'

    def _load_scan_data(self, data_path):
        # Example data from the test scan.
        return b'\x00\x00\x00\x87{"htype":"bsr_m-1.1","hash":"85877517a3f81ebcf617b657b87a5a5",' \
               b'"global_timestamp":{"sec":1929316,"ns":80742626},"dh_compression":"none"}\x00\x00\x00>' \
               b'{"htype":"bsr_d-1.1","channels":[{"name":"data","shape":[6]}]}\x00\x00\x000\x00\x00\x00\x00\x00' \
               b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0?\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00' \
               b'\x08@\x00\x00\x00\x00\x00\x00\x10@\x00\x00\x00\x00\x00\x00\x14@\x00\x00\x00\x10v\x94yZ\x00\x00' \
               b'\x00\x00\xc0\xfav#\x00\x00\x00\x00'
