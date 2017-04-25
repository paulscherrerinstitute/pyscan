from threading import Thread
from time import sleep

from pcaspy import Driver, SimpleServer


class MotorTestDriver(Driver):
    prefix = 'PYSCAN:TEST:'
    pvdb = {
        'MOTOR1:SET': {},
        'MOTOR1:GET': {},
        'MOTOR2:SET': {},
        'MOTOR2:GET': {},
        'MOTOR:PRE1:SET': {},
        'MOTOR:PRE1:GET': {},
        'MOTOR:POST1': {},
        'VALID1': {},
        'VALID2': {},
        'OBS1': {},
        'OBS2': {}
    }

    ALL_MOTORS = ['PYSCAN:TEST:' + motor_name for motor_name in pvdb.keys()]

    def __init__(self):
        super(MotorTestDriver, self).__init__()
        self.values = {}

    def read(self, reason):
        return self.values.get(reason, reason)

    def write(self, reason, value):
        # Only motors should move slowly.
        print(reason)
        if reason.startswith("MOTOR"):
            thread = Thread(target=self.move_slowly, args=(reason, value))
            thread.daemon = True
            thread.start()
        else:
            self.values[reason] = value

    def move_slowly(self, attribute, value, steps=10, latency=0.2):
        current_value = self.values.get(attribute, 0)
        step_size = (value - current_value) / steps

        readback = None
        if attribute.endswith("SET"):
            readback = attribute.replace("SET", "GET")

        for _ in range(steps):
            current_value += step_size
            self.values[attribute] = current_value
            if readback is not None:
                self.values[readback] = current_value
            print(self.values)
            sleep(latency)


def run(driver_class, prefix=None, pvdb=None):
    prefix = driver_class.prefix if prefix is None else prefix
    pvdb = driver_class.pvdb if pvdb is None else pvdb

    server = SimpleServer()
    server.createPV(prefix, pvdb)
    driver = driver_class()

    # process CA transactions
    while True:
        server.process(0.1)


if __name__ == '__main__':
    run(MotorTestDriver)
