from copy import copy

import math


class LinearDiscreetPositioner(object):
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

    def next_position(self):
        for _ in range(self.passes):
            # The initial position is always the start position.
            current_positions = copy(self.start)
            yield current_positions

            for __ in range(self.n_steps):
                current_positions = [position + step_size for position, step_size
                                     in zip(current_positions, self.step_size)]

                yield current_positions


class ZigZagLinearDiscreetPositioner(LinearDiscreetPositioner):
    def next_position(self):
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


class VectorPositioner(object):
    def __init__(self, positions, passes=1, offsets=None):
        self.positions = positions
        self.passes = passes
        self.offsets = offsets

        # TODO: Verify that all the axis have the same number of positions - also offsets.
        # Since all the axis have the same number of elements, we can use the first one.
        self.n_positions = len(self.positions[0])

        # Fix the offset if provided.
        if self.offsets:
            for step_positions in self.positions:
                # step_positions[:] =
                for index in range(self.n_positions):
                    step_positions[index] = step_positions[index] + offsets[index]

    def next_position(self):
        for _ in range(self.passes):
            for position in self.positions:
                yield position

