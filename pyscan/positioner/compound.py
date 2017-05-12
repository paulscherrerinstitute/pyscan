from copy import copy
from pyscan.utils import convert_to_list


class CompoundPositioner(object):
    """
    Given a list of positioners, it compounds them in given order, getting values from each of them at every step.
    """
    def __init__(self, positioners):
        self.positioners = positioners
        self.n_positioners = len(positioners)

    def get_generator(self):
        def walk_positioner(index, output_positions):
            if index == self.n_positioners:
                yield copy(output_positions)
            else:
                for current_positions in self.positioners[index].get_generator():
                    yield from walk_positioner(index+1, output_positions + convert_to_list(current_positions))

        yield from walk_positioner(0, [])
