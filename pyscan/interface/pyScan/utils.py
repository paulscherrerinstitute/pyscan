from time import sleep


class AbortMonitor(object):
    def __init__(self, reader_function, expected_value):
        self.reader_function = reader_function
        self.expected_value = expected_value

    def is_close(self):
        return True

    def execute(self, context):
        if not self.is_close(self.reader_function(), self.expcted_value):
            raise ValueError("it is not close:(")


class PyScanDataProcessor(object):
    def __init__(self, output, n_readbacks, n_validations, n_observable, waiting):
        self.n_readbacks = n_readbacks
        self.n_validations = n_validations
        self.n_observable = n_observable
        self.output = output
        self.waiting = waiting
        self.KnobReadback_output_position = self.output_position_generator(self.output["KnobReadback"])
        self.Validation_output_position = self.output_position_generator(self.output["Validation"])
        self.Observable_output_position = self.output_position_generator(self.output["Observable"])

    @staticmethod
    def output_position_generator(list_to_iterate):
        """
        Since we are pre-allocating the output, we need a "simple" way to know which element is the next to 
        write to.
        :param list_to_iterate: Pre allocated list to iterate over.
        :return: Generator to iterate over the list.
        """
        def flatten(list_to_flatten):
            # If we reached a list of 0 length, this is our next position to write.
            if len(list_to_flatten) == 0:
                yield list_to_flatten
            # Otherwise we have to go deeper.
            else:
                for inner_list in list_to_flatten:
                    yield from flatten(inner_list)

        return flatten(list_to_iterate)

    def process(self, data):
        if self.n_readbacks == 1:
            readback_result = data[0]
        else:
            readback_result = data[0:self.n_readbacks]

        if self.n_validations == 1:
            validation_result = data[self.n_readbacks]
        else:
            validation_result = data[self.n_readbacks:self.n_readbacks + self.n_validations]

        if self.n_observable:
            observable_result = data[-1]
        else:
            interval_start = self.n_readbacks + self.n_validations
            interval_end = self.n_readbacks + self.n_validations + self.n_observables
            observable_result = data[interval_start:interval_end]

        next(self.KnobReadback_output_position).extend(readback_result)
        next(self.Validation_output_position).extend(validation_result)
        next(self.Observable_output_position).extend(observable_result)

        sleep(self.waiting)

    def get_data(self):
        return self.output
