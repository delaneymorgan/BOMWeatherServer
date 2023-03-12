import time
import math


class Periodic(object):
    def __init__(self, period, task, name=None):
        self.period = period
        self.task = task
        self.name = name
        self.start_time = time.time()
        self.num_periods = -1
        self.last_time = 0
        return

    def check(self, arg=None):
        """
        check the periodic action
        :param arg: optional argument for managed task
        :return: True => performed task, False => otherwise, time left to next task performance
        """
        time_now = time.time()
        elapsed_periods = math.floor((time_now - self.start_time) / self.period)
        remainder = (time_now - self.start_time) % self.period
        time_left = max(0, (self.period - remainder))
        if elapsed_periods > self.num_periods:
            self.num_periods += 1
            self.last_time = time_now
            self.task(arg)
            return True, time_left
        return False, time_left
