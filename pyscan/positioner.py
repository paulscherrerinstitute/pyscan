from copy import copy

import math
from itertools import chain, cycle


class LinePositioner(object):
    def __init__(self, start, end, steps, passes=1, offsets=None):
        self.offsets = offsets
        self.passes = passes
        self.end = end
        self.start = start

        # Fix the offsets if provided.
        if self.offsets:
            self.start = [offset + original_value for original_value, offset in zip(self.start, self.offsets)]
            self.end = [offset + original_value for original_value, offset in zip(self.end, self.offsets)]

        # Number of steps case.
        if isinstance(steps[0], int):
            # TODO: Verify that each axis has the same number of steps and that steps are positive.
            self.n_steps = steps[0]
            self.step_size = [(end - start) / steps for start, end, steps in zip(self.start, self.end, steps)]
        # Step size case.
        elif isinstance(steps[0], float):
            # TODO: Verify that each axis has the same number of steps and that the step_size is correct (positive etc.)
            self.n_steps = math.floor((end[0] - start[0]) / steps[0])
            self.step_size = steps
        # Something went wrong
        else:
            # TODO: Raise an exception.
            pass

    def get_generator(self):
        for _ in range(self.passes):
            # The initial position is always the start position.
            current_positions = copy(self.start)
            yield current_positions

            for __ in range(self.n_steps):
                current_positions = [position + step_size for position, step_size
                                     in zip(current_positions, self.step_size)]

                yield current_positions


class ZigZagLinePositioner(LinePositioner):
    def get_generator(self):
        # The initial position is always the start position.
        current_positions = copy(self.start)
        yield current_positions

        for pass_number in range(self.passes):
            # Positive direction means we increase the position each step, negative we decrease.
            direction = 1 if pass_number % 2 == 0 else -1

            for __ in range(self.n_steps):
                current_positions = [position + (step_size * direction) for position, step_size
                                     in zip(current_positions, self.step_size)]

                yield current_positions


class AreaPositioner(object):
    def __init__(self, start, end, steps, passes=1, offsets=None):
        self.offsets = offsets
        self.passes = passes
        self.end = end
        self.start = start

        # Get the number of axis to scan.
        self.n_axis = len(self.start)

        # Fix the offsets if provided.
        if self.offsets:
            self.start = [offset + original_value for original_value, offset in zip(self.start, self.offsets)]
            self.end = [offset + original_value for original_value, offset in zip(self.end, self.offsets)]

        # Number of steps case.
        if isinstance(steps[0], int):
            # TODO: Verify that each axis has positive steps and that all are ints (all steps or step_size)
            self.n_steps = steps
            self.step_size = [(end - start) / steps for start, end, steps in zip(self.start, self.end, steps)]
        # Step size case.
        elif isinstance(steps[0], float):
            # TODO: Verify that each axis has the same number of steps and that the step_size is correct (positive etc.)
            self.n_steps = [math.floor((end - start) / step)
                            for start, end, step in zip(self.start, self.end, steps)]
            self.step_size = steps
        # Something went wrong
        else:
            raise ValueError("Steps '%s' is not a list of int or float." % steps)

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


class VectorPositioner(object):
    def __init__(self, positions, passes=1, offsets=None):
        self.positions = positions
        self.passes = passes
        self.offsets = offsets

        # TODO: Verify that all the axis have the same number of positions - also offsets.
        self.n_positions = len(self.positions)

        # TODO: Verify that passes is positive.

        # Fix the offset if provided.
        if self.offsets:
            for step_positions in self.positions:
                step_positions[:] = [original_position + offset
                                     for original_position, offset in zip(step_positions, self.offsets)]

    def get_generator(self):
        for _ in range(self.passes):
            for position in self.positions:
                yield position


class ZigZagVectorPositioner(VectorPositioner):
    def get_generator(self):
        # This creates a generator for [0, 1, 2, 3... n, n-1, n-2.. 2, 1, 0.....]
        indexes = cycle(chain(range(0, self.n_positions, 1), range(self.n_positions - 2, 0, -1)))
        # First pass has the full number of items, each subsequent has one less (extreme sequence item).
        n_indexes = self.n_positions + ((self.passes - 1) * (self.n_positions - 1))

        for x in range(n_indexes):
            yield self.positions[next(indexes)]


class StepByStepVectorPositioner(VectorPositioner):
    """
    Scan over all provided points, one by one, returning the previous to the initial state.
    """
    def __init__(self, positions, initial_positions, passes=1, offsets=None):
        super(StepByStepVectorPositioner, self).__init__(positions, passes, offsets)
        self.initial_positions = initial_positions

    def get_generator(self):
        # Number of steps for each axis.
        n_steps = len(self.positions)
        n_axis = len(self.positions[0]) if isinstance(self.positions, list) else 1

        for _ in range(self.passes):
            # For each axis.
            for axis_index in range(n_axis):
                current_state = copy(self.initial_positions)
                for step_index in range(n_steps):
                    current_state[axis_index] = self.positions[step_index][axis_index]
                    yield copy(current_state)


class CompoundPositioner(object):
    def __init__(self, positioners):
        self.positioners = positioners
        self.n_positioners = len(positioners)

    def get_generator(self):
        def walk_positioner(index, output_positions):
            if index == self.n_positioners:
                yield copy(output_positions)
            else:
                for current_positions in self.positioners[index].get_generator():
                    yield from walk_positioner(index+1, output_positions + current_positions)

        yield from walk_positioner(0, [])
