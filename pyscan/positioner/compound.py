from copy import copy


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
