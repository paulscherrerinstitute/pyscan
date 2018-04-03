import math
from time import time

from bsread import Source, mflow

from pyscan import config
from pyscan.utils import convert_to_list


class ReadGroupInterface(object):
    """
    Provide a beam synchronous acquisition for PV data.
    """

    def __init__(self, properties, conditions=None, host=None, port=None, filter_function=None):
        """
        Create the bsread group read interface.
        :param properties: List of PVs to read for processing.
        :param conditions: List of PVs to read as conditions.
        :param filter_function: Filter the BS stream with a custom function.
        """
        self.host = host
        self.port = port
        self.properties = convert_to_list(properties)
        self.conditions = convert_to_list(conditions)
        self.filter = filter_function

        self._message_cache = None
        self._message_cache_timestamp = None
        self._message_cache_position_index = None

        self._connect_bsread(config.bs_default_host, config.bs_default_port)

    def _connect_bsread(self, host, port):
        # Configure the connection type.
        if config.bs_connection_mode.lower() == "sub":
            mode = mflow.SUB
        elif config.bs_connection_mode.lower() == "pull":
            mode = mflow.PULL

        if host and port:
            self.stream = Source(host=host,
                                 port=port,
                                 queue_size=config.bs_queue_size,
                                 receive_timeout=config.bs_receive_timeout,
                                 mode=mode)
        else:
            channels = [x.identifier for x in self.properties] + [x.identifier for x in self.conditions]
            self.stream = Source(channels=channels,
                                 queue_size=config.bs_queue_size,
                                 receive_timeout=config.bs_receive_timeout,
                                 mode=mode)
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
        current_sec = int(timestamp)
        current_ns = int(math.modf(timestamp)[0] * 1e9)

        message_sec = message.data.global_timestamp
        message_ns = message.data.global_timestamp_offset

        # If the seconds are the same, the nanoseconds must be equal or larger.
        if message_sec == current_sec:
            return message_ns >= current_ns
        # If the seconds are not the same, the message seconds need to be larger than the current seconds.
        else:
            return message_sec > current_sec

    @staticmethod
    def _get_missing_property_default(property_definition):
        """
        In case a bs read value is missing, either return the default value or raise an Exception.
        :param property_definition:
        :return:
        """
        # Exception is defined, raise it.
        if Exception == property_definition.default_value:
            raise property_definition.default_value("Property '%s' missing in bs stream."
                                                    % property_definition.identifier)
        # Else just return the default value.
        else:
            return property_definition.default_value

    def _read_pvs_from_cache(self, properties):
        """
        Read the requested properties from the cache.
        :param properties: List of properties to read.
        :return: List with PV values.
        """
        if not self._message_cache:
            raise ValueError("Message cache is empty, cannot read PVs %s." % properties)

        pv_values = []
        for property_name, property_definition in ((x.identifier, x) for x in properties):
            if property_name in self._message_cache.data.data:
                value = self._message_cache.data.data[property_name].value
            else:
                value = self._get_missing_property_default(property_definition)

            # TODO: Check if the python conversion works in every case?
            # BS read always return numpy, and we always convert it to Python.
            pv_values.append(value)

        return pv_values

    def read(self, current_position_index=None):
        """
        Reads the PV values from BSread. It uses the first PVs data sampled after the invocation of this method.
        :return: List of values for read pvs. Note: Condition PVs are excluded.
        """

        # Message for this position already cached.
        if current_position_index is not None and current_position_index == self._message_cache_position_index:
            return self._read_pvs_from_cache(self.properties)

        read_timestamp = time()
        while time() - read_timestamp < config.bs_read_timeout:

            message = self.stream.receive(filter=self.filter)

            if self.is_message_after_timestamp(message, read_timestamp):

                self._message_cache = message
                self._message_cache_position_index = current_position_index
                self._message_cache_timestamp = read_timestamp

                return self._read_pvs_from_cache(self.properties)

        else:
            raise Exception("Read timeout exceeded for BS read stream. Could not find the desired package in time.")

    def read_cached_conditions(self):
        """
        Returns the conditions associated with the last read command.
        :return: List of condition values.
        """
        return self._read_pvs_from_cache(self.conditions)

    def close(self):
        """
        Disconnect from the stream and clear the message cache.
        """
        if self.stream:
            self.stream.disconnect()

        self._message_cache = None
        self._message_cache_timestamp = None


class ImmediateReadGroupInterface(ReadGroupInterface):

    @staticmethod
    def is_message_after_timestamp(message, timestamp):
        """
        Every message is a good message, expect a NULL one.
        :param message: Message to inspect.
        :param timestamp: Timestamp to compare the message to.
        :return: True if the message is not None.
        """
        # Receive might timeout, in this case we have nothing to compare.
        if not message:
            return False

        return True
