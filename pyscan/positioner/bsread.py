
class BsreadPositioner(object):
    def __init__(self, n_messages):
        """
        Acquire N consecutive messages from the stream.
        :param n_messages: Number of messages to acquire.
        """
        self.n_messages = n_messages
        self.bs_reader = None

    def set_bs_reader(self, bs_reader):
        self.bs_reader = bs_reader

    def get_generator(self):

        if self.bs_reader is None:
            raise RuntimeError("Set bs_reader before using this generator.")

        for index in range(self.n_messages):
            self.bs_reader.read(index)
            yield index
