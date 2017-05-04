from itertools import cycle, chain


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