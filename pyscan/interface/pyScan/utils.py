
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
    def __init__(self, output, n_pvs, n_validation, n_observable):
        self.n_pvs = n_pvs
        self.n_validation = n_validation
        self.n_observable = n_observable
        self.output = output

        # Reset the pre-allocated variables.
        self.outdict["KnobReadback"] = []
        self.outdict["Validation"] = []
        self.outdict["Observable"] = []

    def process(self, position, data):
        if self.n_readbacks == 1:
            readback_result = data[0]
        else:
            readback_result = data[0:self.n_readbacks]

        if self.n_validation == 1:
            validation_result = data[self.n_readbacks]
        else:
            validation_result = data[self.n_readbacks:self.n_readbacks + self.n_validations]

        if self.n_observable:
            observable_result = data[-1]
        else:
            observable_result = data[self.n_readbacks + self.n_validations:self.n_readbacks +
                                                                           self.n_validations + self.n_observables]

        # TODO: This might not work because of pre-initialization. Remove from original Scan class?
        self.output["KnobReadback"].append(readback_result)
        self.output["Validation"].append(validation_result)
        self.output["Observable"].append(observable_result)