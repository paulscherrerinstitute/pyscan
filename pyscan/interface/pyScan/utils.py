from pyscan.utils import flat_list_generator


def match_monitor_value(value, expected_value, tolerance):
    # We have a NON-ZERO tolerance policy.
    if not tolerance:
        tolerance = 0.00001

    # Monitor value is in list, i.e. several cases are okay
    if isinstance(expected_value, list):
        if value in expected_value:
            return True
    # String values must match exactly.
    elif isinstance(value, str):
        if value == expected_value:
            return True
    # Numbers have to take into account the tolerance.
    elif isinstance(value, int) or isinstance(value, float):
        if abs(value - expected_value) < tolerance:
            return True
    else:
        raise ValueError("Unexpected case.\nvalue = %s\nexpected_value = %s\ntolerance = %s" %
                         (value, expected_value, tolerance))

    return False

class PyScanDataProcessor(object):
    def __init__(self, output, n_readbacks, n_validations, n_observables, n_measurements):
        self.n_readbacks = n_readbacks
        self.n_validations = n_validations
        self.n_observables = n_observables
        self.n_measurements = n_measurements
        self.output = output
        self.KnobReadback_output_position = flat_list_generator(self.output["KnobReadback"])
        self.Validation_output_position = flat_list_generator(self.output["Validation"])
        self.Observable_output_position = flat_list_generator(self.output["Observable"])

    def process(self, position, data):
        # Just we can always iterate over it.
        if self.n_measurements == 1:
            data = [data]

        # Cells for each measurement are already prepared.
        readback_result = [measurement[0:self.n_readbacks]
                           for measurement in data]
        validation_result = [measurement[self.n_readbacks:self.n_readbacks + self.n_validations]
                             for measurement in data]

        interval_start = self.n_readbacks + self.n_validations
        interval_end = self.n_readbacks + self.n_validations + self.n_observables
        observable_result = [measurement[interval_start:interval_end]
                             for measurement in data]

        if self.n_measurements == 1:
            next(self.KnobReadback_output_position).extend(readback_result[0])
            next(self.Validation_output_position).extend(validation_result[0])
            next(self.Observable_output_position).extend(observable_result[0])
        else:
            next(self.KnobReadback_output_position).extend(readback_result)
            next(self.Validation_output_position).extend(validation_result)
            next(self.Observable_output_position).extend(observable_result)

    def get_data(self):
        return self.output
