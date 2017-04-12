from threading import Thread
from time import sleep

from pcaspy import Driver, SimpleServer


class MotorTestDriver(Driver):
    prefix = 'PYSCAN:TEST:'
    pvdb = {
        'MOTOR1': {},
        'MOTOR2': {},
        'MOTOR3': {},
        'MOTOR4': {},
        'MOTOR5': {}
    }

    ALL_MOTORS = ['PYSCAN:TEST:' + motor_name for motor_name in pvdb.keys()]

    def __init__(self):
        super(MotorTestDriver, self).__init__()
        self.values = {}

    def read(self, reason):
        return self.values.get(reason, 0)

    def write(self, reason, value):
        thread = Thread(target=self.move_slowly, args=(reason, value))
        thread.daemon = True
        thread.start()

    def move_slowly(self, attribute, value, steps=10, latency=0.2):
        current_value = self.values.get(attribute, 0)
        step_size = (value - current_value) / steps

        for _ in range(steps):
            current_value += step_size
            self.values[attribute] = current_value
            sleep(latency)


def run(driver_class):
    server = SimpleServer()
    server.createPV(driver_class.prefix, driver_class.pvdb)
    driver = driver_class()

    # process CA transactions
    while True:
        server.process(0.1)


if __name__ == '__main__':
    run(MotorTestDriver)
