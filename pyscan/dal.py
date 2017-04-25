import time
from itertools import count

from epics.pv import PV

from pyscan.utils import convert_to_list


class EpicsInterface(object):
    """
    PyEpics wrapper for easier communication.
    """
    def __init__(self, list_of_pvs, n_measurments=1):
        self.pvs = [self.connect_to_pv(pv_name) for pv_name in convert_to_list(list_of_pvs)]
        self.n_measurements = n_measurments

    @staticmethod
    def connect_to_pv(pv_name, n_connection_attempts=3):
        """
        Start a connection to a PV.
        :param pv_name: PV name to connect to.
        :param n_connection_attempts: How many times you should try to connect before raising an exception.
        :return: PV object.
        :raises ValueError if cannot connect to PV.
        """
        pv = PV(pv_name, auto_monitor=False)
        for i in range(n_connection_attempts):
            if pv.connect():
                return pv
            time.sleep(0.1)

        raise ValueError("Cannot connect to PV '%s'." % pv_name)

    def read(self):
        """
        Read PVs one by one.
        :return: List of results.
        """
        result = []
        for pv in self.pvs:
            if self.n_measurements == 1:
                result.append(pv.get())
            else:
                pv_result = []
                for i in range(self.n_measurements):
                    pv_result.append(pv.get())
                result.append(pv_result)

        return result

    def set_and_match(self, values, tolerance=0.00001, timeout=5):
        """
        Write values and wait for PVs to reach set value.
        :param values: Values to set.
        :param tolerance: Tolerance that needs to be reached.
        :param timeout: Timeout to reach the desired position.
        :raise ValueError if position cannot be reached in time
        """
        values = convert_to_list(values)

        for pv, value in zip(self.pvs, values):
            pv.put(value)

        # Boolean array to represent which PVs have reached their target value.s
        within_tolerance = [False] * len(self.pvs)
        initial_timestamp = time.time()

        # Read values until all PVs have reached the desired value or time has run out.
        while not all(within_tolerance) and time.time() - initial_timestamp < timeout:
            for index, pv in ((index, pv) for index, reached, pv
                              in zip(count(), within_tolerance, self.pvs) if not reached):
                # The get method might return a None. In this case we do not care about the method.
                current_value = pv.get()
                if not current_value:
                    continue

                if abs(pv.get() - values[index]) < tolerance:
                    within_tolerance[index] = True

        if not all(within_tolerance):
            raise ValueError("Cannot achieve position in specified time.")

    def close(self):
        for pv in self.pvs:
            pv.disconnect()
