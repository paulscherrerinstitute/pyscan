from time import sleep


class Scanner(object):
    """
    Perform discrete and continues scans.
    """

    # Interval to sleep while in pause.
    pause_sleep_interval = 1

    def __init__(self, positioner, writer, data_processor, reader, before_executer=None, after_executer=None,
                 initialization_executer=None, finalization_executer=None):
        """
        Initialize scanner.
        :param positioner: Positioner should provide a generator to get the positions to move to.
        :param writer: Object that implements the write(position) method and sets the positions.
        :param data_processor: How to store and handle the data.
        :param reader: Object that implements the read() method to return data to the data_processor.
        :param before_executer: Callbacks executor that executed before measurements.
        :param after_executer: Callbacks executor that executed after measurements.
        """
        self.positioner = positioner
        self.writer = writer
        self.data_processor = data_processor
        self.reader = reader
        self.before_executer = before_executer
        self.after_executer = after_executer
        self.initialization_executer = initialization_executer
        self.finalization_executer = finalization_executer

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

    def setup_monitors(self):
        pass

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
            sleep(self.pause_sleep_interval)

    def discrete_scan(self, settling_time=0):
        """
        Perform a discrete scan - set a position, read, continue. Return value at the end.
        :param settling_time: Interval between the writing of the position and the reading of data. Default = 0.
        """
        try:
            # Set up the experiment.
            if self.initialization_executer:
                self.initialization_executer(self)

            for next_positions in self.positioner.get_generator():
                # Position yourself before reading.
                self.writer.set_and_match(next_positions)
                sleep(settling_time)

                # Pre reading callbacks.
                if self.before_executer:
                    self.before_executer(self)

                # Collect and process the data.
                position_data = self.reader.read()
                self.data_processor.process(position_data)

                # Post reading callbacks.
                if self.after_executer:
                    self.after_executer(self)

                # Verify is the scan should continue.
                self._verify_scan_status()
        finally:
            # Clean up after yourself.
            if self.finalization_executer:
                self.finalization_executer(self)

        return self.data_processor.get_data()

    def continuous_scan(self):
        # TODO: Needs implementation.
        pass
