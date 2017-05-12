from itertools import cycle, chain

from pyscan.utils import convert_to_list


class VectorPositioner(object):
    """
    Moves over the provided positions.
    """

    def _validate_parameters(self):
        if not all(len(convert_to_list(x)) == len(convert_to_list(self.positions[0])) for x in self.positions):
            raise ValueError("All positions %s must have the same number of axis." % self.positions)

        if not isinstance(self.passes, int) or self.passes < 1:
            raise ValueError("Passes must be a positive integer value, but %s was given." % self.passes)

        if self.offsets and (not len(self.offsets) == len(self.positions[0])):
            raise ValueError("Number of offsets %s does not match the number of positions %s." %
                             (self.offsets, self.positions[0]))

    def __init__(self, positions, passes=1, offsets=None):
        self.positions = convert_to_list(positions)
        self.passes = passes
        self.offsets = convert_to_list(offsets)

        self._validate_parameters()

        # Number of positions to move to.
        self.n_positions = len(self.positions)

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
