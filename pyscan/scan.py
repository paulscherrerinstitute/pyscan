from time import sleep


class Scanner(object):
    """
    Perform discrete and continues scans.
    """
    def __init__(self, positioner, writer, data_processor, reader, before_executer=None, after_executer=None):
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

    def discrete_scan(self, latency=0):
        """
        Perform a discrete scan - set a position, read, continue. Return value at the end.
        :param latency: Interval between the writing of the position and the reading of data. Default = 0.
        """
        for position in self.positioner.get_generator():
            # Position yourself before reading.
            self.writer.write(position)
            sleep(latency)

            # Pre reading callbacks.
            if self.before_executer:
                self.before_executer.execute(position)

            # Collect and process the data.
            position_data = self.reader.read()
            self.data_processor.process(position, position_data)

            # Post reading callbacks.
            if self.after_executer:
                self.after_executer.execute(position)

        return self.data_processor.get_data()

    def continuous_scan(self):
        # TODO: Needs implementation.
        pass
