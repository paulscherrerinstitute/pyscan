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

    def __init__(self, script_name, parameters, server_url=None, scan_in_background=None):
        if server_url is None:
            server_url = config.pshell_default_server_url

        if scan_in_background is None:
            scan_in_background = config.pshell_default_scan_in_background

        self.script_name = script_name
        self.parameters = parameters
        self.server_url = server_url.rstrip("/")
        self.scan_in_background = scan_in_background

    def read(self, current_position_index=None):
        parameters = self.get_scan_parameters(current_position_index)

        run_request = {"script": self.script_name,
                       "pars": parameters,
                       "background": self.scan_in_background}

        raw_scan_response_text = self._execute_scan(run_request)
        _, data_path = json.loads(raw_scan_response_text)

        raw_data_bytes = self._load_scan_data(data_path)

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
            channel["encoding"] = ">" if channel.get("encoding", "big") else "<"
            
            channel_value_reader = get_channel_reader(channel)

            result_data[channel_name] = channel_value_reader(raw_channel_data)

        return result_data

    def get_scan_parameters(self, current_position_index):

        if isinstance(self.parameters, (list, tuple)):
            return self.parameters[current_position_index]
        else:
            return self.parameters

    def _execute_scan(self, execution_parameters):
        run_url = self.server_url + SERVER_URL_PATHS["run"]

        result = requests.put(url=run_url, json=execution_parameters)

        if result.status_code != 200:
            raise Exception(result.text)

        return result.text

    def _load_scan_data(self, data_path):
        load_data_url = self.server_url + SERVER_URL_PATHS["data"] + "/" + data_path

        raw_data = requests.get(url=load_data_url, stream=True).raw.read()

        return raw_data
