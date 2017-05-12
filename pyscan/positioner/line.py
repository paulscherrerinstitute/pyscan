import math
from copy import copy

from pyscan.utils import convert_to_list


class LinePositioner(object):

    def _validate_parameters(self):
        if not len(self.start) == len(self.end):
            raise ValueError("Number of start %s and end %s positions do not match." %
                             (self.start, self.end))

        # Only 1 among n_steps and step_sizes must be set.
        if (self.n_steps is not None and self.step_size) or (self.n_steps is None and not self.step_size):
            raise ValueError("N_steps (%s) or step_sizes (%s) must be set, but not none "
                             "or both of them at the same time." % (self.step_size, self.n_steps))

        # If n_steps is set, than it must be an integer greater than 0.
        if (self.n_steps is not None) and (not isinstance(self.n_steps, int) or self.n_steps < 1):
            raise ValueError("Steps must be a positive integer value, but %s was given." % self.n_steps)

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
        self.n_steps = n_steps
        self.step_size = convert_to_list(step_size)
        self.passes = passes
        self.offsets = convert_to_list(offsets)

        self._validate_parameters()

        # Fix the offsets if provided.
        if self.offsets:
            self.start = [offset + original_value for original_value, offset in zip(self.start, self.offsets)]
            self.end = [offset + original_value for original_value, offset in zip(self.end, self.offsets)]

        # Number of steps case.
        if self.n_steps:
            self.step_size = [(end - start) / self.n_steps for start, end in zip(self.start, self.end)]
        # Step size case.
        elif self.step_size:
            n_steps_per_axis = [math.floor((end - start) / step_size) for start, end, step_size
                                in zip(self.start, self.end, self.step_size)]
            # Verify that all axis do the same number of steps.
            if not all(x == n_steps_per_axis[0] for x in n_steps_per_axis):
                raise ValueError("The step sizes %s must give the same number of steps for each start %s "
                                 "and end % pair." % (self.step_size, self.start, self.end))

            # All the elements in n_steps_per_axis must be the same anyway.
            self.n_steps = n_steps_per_axis[0]

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
