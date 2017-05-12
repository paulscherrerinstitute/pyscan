from itertools import count
from time import sleep

from pyscan import config
from pyscan.scan_parameters import scan_settings


class Scanner(object):
    """
    Perform discrete and continues scans.
    """

    def __init__(self, positioner, writer, data_processor, reader, before_executor=None, after_executor=None,
                 initialization_executor=None, finalization_executor=None, data_validator=None, settings=None):
        """
        Initialize scanner.
        :param positioner: Positioner should provide a generator to get the positions to move to.
        :param writer: Object that implements the write(position) method and sets the positions.
        :param data_processor: How to store and handle the data.
        :param reader: Object that implements the read() method to return data to the data_processor.
        :param before_executor: Callbacks executor that executed before measurements.
        :param after_executor: Callbacks executor that executed after measurements.
        """
        self.positioner = positioner
        self.writer = writer
        self.data_processor = data_processor
        self.reader = reader
        self.before_executor = before_executor
        self.after_executor = after_executor
        self.initialization_executor = initialization_executor
        self.finalization_executor = finalization_executor
        self.settings = settings or scan_settings()

        # If no data validator is provided, data is always valid.
        self.data_validator = data_validator or (lambda position, data: True)

        self._user_abort_scan_flag = False
        self._user_pause_scan_flag = False

    def abort_scan(self):
        """
        Abort the scan after the next measurement.
        """
        self._user_abort_scan_flag = True

    def pause_scan(self):
        """
        Pause the scan after the next measurement.
        """
        self._user_pause_scan_flag = True

    def resume_scan(self):
        """
        Resume the scan.
        """
        self._user_pause_scan_flag = False

    def _verify_scan_status(self):
        """
        Check if the conditions to pause or abort the scan are met.
        :raise Exception in case the conditions are met.
        """
        # Check if the abort flag is set.
        if self._user_abort_scan_flag:
            raise Exception("User aborted scan.")

        # If the scan is in pause, wait until it is resumed or the user aborts the scan.
        while self._user_pause_scan_flag:
            if self._user_abort_scan_flag:
                raise Exception("User aborted scan in pause.")
            sleep(config.scan_pause_sleep_interval)

    def _perform_single_read(self, current_position):
        """
        Read a single result from the channel.
        :param current_position: Current position, passed to the validator.
        :return: Single result (all channels).
        """
        n_current_acquisition = 0
        # Collect data until acquired data is valid or retry limit reached.
        while n_current_acquisition < config.scan_acquisition_retry_limit:
            single_measurement = self.reader()

            # If the data is valid, break out of the loop.
            if self.data_validator(current_position, single_measurement):
                return single_measurement

            n_current_acquisition += 1
            sleep(config.scan_acquisition_retry_delay)
        # Could not read the data within the retry limit.
        else:
            raise Exception("Number of maximum read attempts (%d) exceeded. Cannot read valid data at position %s."
                            % (config.scan_acquisition_retry_limit, current_position))

    def _read_and_process_data(self, current_position):
        """
        Read the data and pass it on only if valid.
        :param current_position: Current position reached by the scan.
        :return: Current position scan data.
        """
        # We do a single acquisition per position.
        if self.settings.n_measurements == 1:
            result = self._perform_single_read(current_position)

        # Multiple acquisitions.
        else:
            result = []
            for n_measurement in range(self.settings.n_measurements):
                result.append(self._perform_single_read(current_position))
                sleep(self.settings.measurement_interval)

        # Process only valid data.
        self.data_processor.process(current_position, result)

        return result

    def discrete_scan(self):
        """
        Perform a discrete scan - set a position, read, continue. Return value at the end.
        """
        try:
            # Get how many positions we have in total.
            n_of_positions = sum(1 for _ in self.positioner.get_generator())
            # Report the 0% completed.
            self.settings.progress_callback(0, n_of_positions)

            # Set up the experiment.
            if self.initialization_executor:
                self.initialization_executor(self)

            for position_index, next_positions in zip(count(1), self.positioner.get_generator()):
                # Position yourself before reading.
                self.writer(next_positions)
                # Settling time, wait after positions has been reached.
                sleep(self.settings.settling_time)

                # Pre reading callbacks.
                if self.before_executor:
                    self.before_executor(self)

                # Read and process the data in the current position.
                position_data = self._read_and_process_data(next_positions)

                # Post reading callbacks.
                if self.after_executor:
                    self.after_executor(self)

                # Report about the progress.
                self.settings.progress_callback(position_index, n_of_positions)

                # Verify is the scan should continue.
                self._verify_scan_status()
        finally:
            # Clean up after yourself.
            if self.finalization_executor:
                self.finalization_executor(self)

        return self.data_processor.get_data()

    def continuous_scan(self):
        # TODO: Needs implementation.
        pass
