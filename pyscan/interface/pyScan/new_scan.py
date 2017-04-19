from pyscan.interface import pyScan
from pyscan.positioner import VectorPositioner, StepByStepVectorPositioner, CompoundPositioner
from pyscan.scan import Scanner
from pyscan.utils import PyScanDataProcessor, EpicsReader, convert_to_list, EpicsWriter, convert_to_position_list


class Scan(pyScan.Scan):
    def execute_scan(self):
        # The number of measurments is sampled only from the last dimension.
        n_measurments = self.inlist[-1]["NumberOfMeasurements"]

        # Knob PVs defined in all dimensions.
        write_pvs = [[pvs for pvs in dimension["Knob"]] for dimension in self.inlist]
        # Readback PVs defined in all dimensions.
        readback_pvs = [[pvs for pvs in dimension["KnobReadback"]] for dimension in self.inlist]
        # Only validation PVs defined in the last dimension.
        validation_pvs = [pvs for pvs in self.inlist[-1].get("Validation", [])]
        # Only observable PVs defined in the last dimension.
        observable_pvs = [pvs for pvs in self.inlist[-1].get("Observable", [])]

        # Concatenate readback, validation, and observable PVs.
        all_read_pvs = readback_pvs + validation_pvs + observable_pvs

        data_processor = PyScanDataProcessor(self.outdict,
                                             n_pvs=len(readback_pvs),
                                             n_validation=len(validation_pvs),
                                             n_observable=len(observable_pvs))
        reader = EpicsReader(all_read_pvs)
        writer = EpicsWriter(write_pvs)

        # Read and store the initial values.
        data_processor.process(reader.read())

        positioners = []
        for dimension in self.inlist:
            is_additive = bool(dimension.get("Additive", 0))
            is_series = bool(dimension.get("Series", 0))

            # This dimension uses relative positions, read the PVs initial state.
            # We also need initial positions for the series scan.
            if is_additive or is_series:
                offsets = EpicsReader(dimension["KnobReadback"]).read()
            else:
                offsets = None

            # Change the PER KNOB to PER INDEX of positions.
            positions = convert_to_position_list(convert_to_list(dimension["KnobExpanded"]))

            # Series scan in this dimension, use StepByStepVectorPositioner.
            if is_series:
                # In the StepByStep positioner, the initial values need to be added to the steps.
                positioners.append(StepByStepVectorPositioner(positions, initial_positions=offsets,
                                                              offsets=offsets if is_additive else None))
            # Line scan in this dimension, use VectorPositioner.
            else:
                positioners.append(VectorPositioner(positions, offsets=offsets))

        positioner = CompoundPositioner(positioners)

        scanner = Scanner(positioner, writer, data_processor, reader)
        # TODO: Latency from KnobWaitingExtra if per dimension, which is not supported right now.
        scanner.discrete_scan()

