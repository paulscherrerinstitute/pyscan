from time import time

import math
from bsread import Source

from pyscan.utils import convert_to_list


class ReadGroupInterface(object):
    """
    Provide a beam synchronous acquisition for PV data.
    """

    default_n_measurements = 1
    default_waiting = 0
    default_queue_size = 20
    default_read_timeout = 5
    default_receive_timeout = 1

    def __init__(self, read_pv_names, monitor_pv_names=None, n_measurements=None, waiting=None, host=None, port=None):
        """
        Create the bsread group read interface.
        :param read_pv_names: List of PVs to read for processing.
        :param monitor_pv_names: List of PVs to read as monitors.
        """
        self.read_pv_names = convert_to_list(read_pv_names)
        self.monitor_pv_names = convert_to_list(monitor_pv_names)
        self.n_measurements = n_measurements or self.default_n_measurements
        self.waiting = waiting or self.default_waiting

        self._message_cache = None
        self._message_cache_timestamp = None

        self._connect_bsread(host, port)

    def _connect_bsread(self, host, port):
        self.stream = Source(host=host,
                             port=port,
                             channels=self.read_pv_names+self.monitor_pv_names,
                             queue_size=self.default_queue_size,
                             receive_timeout=self.default_receive_timeout)
        self.stream.connect()

    @staticmethod
    def is_message_after_timestamp(message, timestamp):
        """
        Check if the received message was captured after the provided timestamp.
        :param message: Message to inspect.
        :param timestamp: Timestamp to compare the message to.
        :return: True if the message is after the timestamp, False otherwise.
        """
        # Receive might timeout, in this case we have nothing to compare.
        if not message:
            return False

        # This is how BSread encodes the timestamp.
        current_epoch = int(timestamp)
        current_ns = int(math.modf(timestamp)[0] * 1e9)

        message_epoch = message.data.global_timestamp["sec"]
        message_ns = message.data.global_timestamp["ns"]

        # If the seconds are the same, the nanoseconds must be equal or larger.
        if message_epoch == current_epoch:
            return message_ns >= current_ns
        # If the seconds are not the same, the message seconds need to be larger than the current seconds.
        else:
            return message_epoch > current_epoch

    def _read_pvs_from_cache(self, pvs_to_read):
        """
        Read the requested PVs from the cache.
        :param pvs_to_read: List of PVs to read.
        :return: List with PV values.
        """
        if not self._message_cache:
            raise ValueError("Message cache is empty, cannot read PVs %s." % pvs_to_read)

        pv_values = []
        for pv_name in pvs_to_read:
            pv_values.append(self._message_cache.data.data[pv_name])

        return pv_values

    def read(self):
        """
        Reads the PV values from BSread. It uses the first PVs data sampled after the invocation of this method.
        :return: List of values for read pvs. Note: Monitor PVs are excluded.
        """
        read_timestamp = time()
        while time()-read_timestamp < self.default_queue_size:
            message = self.stream.receive()
            if self.is_message_after_timestamp(message, read_timestamp):
                self._message_cache = message
                self._message_cache_timestamp = read_timestamp
                return self._read_pvs_from_cache(self.read_pv_names)
        else:
            raise Exception("Read timeout exceeded for BS read stream. Could not find the desired package in time.")

    def read_cached_monitors(self):
        """
        Returns the monitors associated with the last read command.
        :return: List of monitor values.
        """
        return self._read_pvs_from_cache(self.monitor_pv_names)

    def close(self):
        """
        Disconnect from the stream and clear the message cache.
        """
        if self.stream:
            self.stream.disconnect()

        self._message_cache = None
        self._message_cache_timestamp = None
