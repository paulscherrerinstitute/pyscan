import json
from collections import OrderedDict
import requests
from bsread.data.helpers import get_channel_reader
from pyscan import config

SERVER_URL_PATHS = {
    "run": "/run",
    "data": "/data-bs"
}


class PShellFunction(object):

    def __init__(self, script_name, parameters, server_url=None, scan_in_background=None, multiple_parameters=False,
                 return_values=None):
        if server_url is None:
            server_url = config.pshell_default_server_url

        if scan_in_background is None:
            scan_in_background = config.pshell_default_scan_in_background

        self.script_name = script_name
        self.parameters = parameters
        self.server_url = server_url.rstrip("/")
        self.scan_in_background = scan_in_background
        self.multiple_parameters = multiple_parameters
        self.return_values = return_values

    @staticmethod
    def _load_raw_data(server_url, data_path):
        load_data_url = server_url + SERVER_URL_PATHS["data"] + "/" + data_path

        raw_data = requests.get(url=load_data_url, stream=True).raw.read()

        return raw_data

    @classmethod
    def read_raw_data(cls, data_path, server_url=None):
        if server_url is None:
            server_url = config.pshell_default_server_url

        raw_data_bytes = cls._load_raw_data(server_url, data_path)

        offset = 0

        def read_chunk():
            nonlocal offset
            nonlocal raw_data_bytes

            size = int.from_bytes(raw_data_bytes[offset:offset + 4], byteorder='big', signed=False)

            # Offset for the size of the length.
            offset += 4

            data_chunk = raw_data_bytes[offset:offset + size]

            offset += size

            return data_chunk

        # First chunk is main header.
        main_header = json.loads(read_chunk().decode(), object_pairs_hook=OrderedDict)

        # Second chunk is data header.
        data_header = json.loads(read_chunk().decode(), object_pairs_hook=OrderedDict)

        result_data = {}

        for channel in data_header["channels"]:
            raw_channel_data = read_chunk()
            raw_channel_timestamp = read_chunk()

            channel_name = channel["name"]
            # Default encoding is small, other valid value is 'big'.
            channel["encoding"] = "<" if channel.get("encoding", "little") else ">"

            channel_value_reader = get_channel_reader(channel)

            result_data[channel_name] = channel_value_reader(raw_channel_data)

        return result_data

    def read(self, current_position_index=None):
        parameters = self.get_scan_parameters(current_position_index)

        run_request = {"script": self.script_name,
                       "pars": parameters,
                       "background": self.scan_in_background}

        raw_scan_result = self._execute_scan(run_request)
        scan_result = json.loads(raw_scan_result)

        return scan_result

    def get_scan_parameters(self, current_position_index):

        if self.multiple_parameters:
            try:
                position_parameters = self.parameters[current_position_index]
            except IndexError:
                raise ValueError("Cannot find parameters for position index %s. Parameters: " %
                                 (current_position_index, self.parameters))

            return position_parameters

        else:
            return self.parameters

    def _execute_scan(self, execution_parameters):
        run_url = self.server_url + SERVER_URL_PATHS["run"]

        result = requests.put(url=run_url, json=execution_parameters)

        if result.status_code != 200:
            raise Exception(result.text)

        return result.text
