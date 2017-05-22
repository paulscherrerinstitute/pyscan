from time import time, sleep

from pyscan.config import max_time_tolerance

smoothing_factor = 0.95


class TimePositioner(object):
    def __init__(self, time_interval, n_intervals, tolerance=None):
        """
        Time interval at which to read data.
        :param time_interval: Time interval in seconds.
        :param n_intervals: How many intervals to measure.
        """
        self.time_interval = time_interval
        # Tolerance cannot be less than the min set tolerance.
        if tolerance is None or tolerance < max_time_tolerance:
            tolerance = max_time_tolerance
        self.tolerance = tolerance

        # Minimum one measurement.
        if n_intervals < 1:
            n_intervals = 1
        self.n_intervals = n_intervals

    def get_generator(self):
        measurement_time_start = time()
        last_time_to_sleep = 0

        for _ in range(self.n_intervals):
            measurement_time_stop = time()
            # How much time did the measurement take.
            measurement_time = measurement_time_stop - measurement_time_start

            time_to_sleep = self.time_interval - measurement_time
            # Use the smoothing factor to attenuate variations in the measurement time.
            time_to_sleep = (smoothing_factor * time_to_sleep) + ((1-smoothing_factor) * last_time_to_sleep)

            # Time to sleep is negative (more time has elapsed, we cannot achieve the requested time interval.
            if time_to_sleep < (-1 * max_time_tolerance):
                raise ValueError("The requested time interval cannot be achieved. Last iteration took %.2f seconds, "
                                 "but a %.2f seconds time interval was set." % (measurement_time, self.time_interval))

            # Sleep only if time to sleep is positive.
            if time_to_sleep > 0:
                sleep(time_to_sleep)

            last_time_to_sleep = time_to_sleep
            measurement_time_start = time()

            yield None
