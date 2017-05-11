from copy import copy

from pyscan.utils import convert_to_list


class SerialPositioner(object):
    """
    Scan over all provided points, one by one, returning the previous to the initial state.
    Each axis is treated as a separate line.
    """
    def __init__(self, positions, initial_positions, passes=1, offsets=None):
        self.positions = positions
        self.passes = passes
        self.offsets = offsets

        if passes < 1:
            raise ValueError("Number of passes cannot be less than 1, but %d was provided." % passes)

        self.initial_positions = initial_positions
        self.n_axis = len(self.initial_positions)

        # In case only 1 axis is provided, still wrap it in a list, because it makes the generator code easier.
        if self.n_axis == 1:
            self.positions = [positions]

        # Fix the offset if provided.
        if self.offsets:
            for axis_positions, offset in zip(self.positions, self.offsets):
                axis_positions[:] = [original_position + offset for original_position in axis_positions]

    def get_generator(self):
        for _ in range(self.passes):
            # For each axis.
            for axis_index in range(self.n_axis):
                current_state = copy(self.initial_positions)

                n_steps_in_axis = len(self.positions[axis_index])
                for axis_position_index in range(n_steps_in_axis):
                    current_state[axis_index] = convert_to_list(self.positions[axis_index])[axis_position_index]
                    yield copy(current_state)

    def get_positions_count(self):
        return sum(1 for _ in self.get_generator())
