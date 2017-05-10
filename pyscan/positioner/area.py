import math
from copy import copy

from pyscan.utils import convert_to_list


class AreaPositioner(object):
    def _validate_parameters(self):
        if not len(self.start) == len(self.end):
            raise ValueError("Number of start %s and end %s positions do not match." %
                             (self.start, self.end))

        if (self.n_steps and self.step_size) or (not self.n_steps and not self.step_size):
            raise ValueError("N_steps (%s) or step_sizes (%s) must be set, but not none "
                             "or both of them at the same time." % (self.step_size, self.n_steps))

        if self.n_steps and (not len(self.n_steps) == len(self.start)):
            raise ValueError("The number of n_steps %s does not match the number of start positions %s." %
                             (self.n_steps, self.start))

        if self.n_steps and not all(isinstance(x, int) for x in self.n_steps):
            raise ValueError("The n_steps %s must have only integers." % self.n_steps)

        if self.step_size and (not len(self.step_size) == len(self.start)):
            raise ValueError("The number of step sizes %s does not match the number of start positions %s." %
                             (self.step_size, self.start))

        if not isinstance(self.passes, int) or self.passes < 1:
            raise ValueError("Passes must be a positive integer value, but %s was given." % self.passes)

        if self.offsets and (not len(self.offsets) == len(self.start)):
            raise ValueError("Number of offsets %s does not match the number of start positions %s." %
                             (self.offsets, self.start))

    def __init__(self, start, end, n_steps=None, step_size=None, passes=1, offsets=None):
        self.start = convert_to_list(start)
        self.end = convert_to_list(end)
        self.n_steps = convert_to_list(n_steps)
        self.step_size = convert_to_list(step_size)
        self.passes = passes
        self.offsets = convert_to_list(offsets)

        self._validate_parameters()

        # Get the number of axis to scan.
        self.n_axis = len(self.start)

        # Fix the offsets if provided.
        if self.offsets:
            self.start = [offset + original_value for original_value, offset in zip(self.start, self.offsets)]
            self.end = [offset + original_value for original_value, offset in zip(self.end, self.offsets)]

        # Number of steps case.
        if self.n_steps:
            self.step_size = [(end - start) / steps for start, end, steps
                              in zip(self.start, self.end, self.n_steps)]
        # Step size case.
        elif self.step_size:
            self.n_steps = [math.floor((end - start) / step_size) for start, end, step_size
                            in zip(self.start, self.end, self.step_size)]

    def get_generator(self):
        for _ in range(self.passes):
            positions = copy(self.start)
            # Return the initial state.
            yield copy(positions)

            # Recursive call to print all axis values.
            def scan_axis(axis_number):
                # We should not scan axis that do not exist.
                if not axis_number < self.n_axis:
                    return

                # Output all position on the next axis while this axis is still at the start position.
                yield from scan_axis(axis_number + 1)

                # Move axis step by step.
                for _ in range(self.n_steps[axis_number]):
                    positions[axis_number] = positions[axis_number] + self.step_size[axis_number]
                    yield copy(positions)
                    # Output all positions from the next axis for each value of this axis.
                    yield from scan_axis(axis_number + 1)

                # Clean up after the loop - return the axis value back to the start value.
                positions[axis_number] = self.start[axis_number]

            yield from scan_axis(0)


class ZigZagAreaPositioner(AreaPositioner):
    def get_generator(self):
        for pass_number in range(self.passes):
            # Directions (positive ascending, negative descending) for each axis.
            directions = [1] * self.n_axis
            positions = copy(self.start)

            # Return the initial state.
            yield copy(positions)

            # Recursive call to print all axis values.
            def scan_axis(axis_number):
                # We should not scan axis that do not exist.
                if not axis_number < self.n_axis:
                    return

                # Output all position on the next axis while this axis is still at the start position.
                yield from scan_axis(axis_number + 1)

                # Move axis step by step.
                for _ in range(self.n_steps[axis_number]):
                    positions[axis_number] = positions[axis_number] + (self.step_size[axis_number]
                                                                       * directions[axis_number])
                    yield copy(positions)
                    # Output all positions from the next axis for each value of this axis.
                    yield from scan_axis(axis_number + 1)

                # Invert the direction for the next iteration on this axis.
                directions[axis_number] *= -1

            yield from scan_axis(0)


class MultiAreaPositioner(object):
    def __init__(self, start, end, steps, passes=1, offsets=None):
        self.offsets = offsets
        self.passes = passes
        self.end = end
        self.start = start

        # Get the number of axis to scan.
        self.n_axis = len(self.start)

        # Fix the offsets if provided.
        if self.offsets:
            self.start = [[original_value + offset for original_value, offset in zip(original_values, offsets)]
                          for original_values, offsets in zip(self.start, self.offsets)]
            self.end = [[original_value + offset for original_value, offset in zip(original_values, offsets)]
                        for original_values, offsets in zip(self.end, self.offsets)]

        # Number of steps case.
        if isinstance(steps[0][0], int):
            # TODO: Verify that each axis has positive steps and that all are ints (all steps or step_size)
            self.n_steps = steps
            self.step_size = [[(end - start) / steps for start, end, steps in zip(starts, ends, line_steps)]
                              for starts, ends, line_steps in zip(self.start, self.end, steps)]
        # Step size case.
        elif isinstance(steps[0][0], float):
            # TODO: Verify that each axis has the same number of steps and that the step_size is correct (positive etc.)
            self.n_steps = [[math.floor((end - start) / step) for start, end, step in zip(starts, ends, line_steps)]
                            for starts, ends, line_steps in zip(self.start, self.end, steps)]
            self.step_size = steps
        # Something went wrong
        else:
            # TODO: Raise an exception.
            pass

    def get_generator(self):
        for _ in range(self.passes):
            positions = copy(self.start)
            # Return the initial state.
            yield copy(positions)

            # Recursive call to print all axis values.
            def scan_axis(axis_number):
                # We should not scan axis that do not exist.
                if not axis_number < self.n_axis:
                    return

                # Output all position on the next axis while this axis is still at the start position.
                yield from scan_axis(axis_number + 1)

                # Move axis step by step.
                # TODO: Figure out what to do with this steps.
                for _ in range(self.n_steps[axis_number][0]):
                    positions[axis_number] = [position + step_size for position, step_size
                                              in zip(positions[axis_number], self.step_size[axis_number])]
                    yield copy(positions)
                    # Output all positions from the next axis for each value of this axis.
                    yield from scan_axis(axis_number + 1)

                # Clean up after the loop - return the axis value back to the start value.
                positions[axis_number] = self.start[axis_number]

            yield from scan_axis(0)
