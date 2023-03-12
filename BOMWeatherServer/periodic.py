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

    def check(self):
        time_now = time.time()
        elapsed_periods = math.floor((time_now - self.start_time) / self.period)
        remainder = (time_now - self.start_time) % self.period
        time_left = max(0, (self.period - remainder))
        if elapsed_periods > self.num_periods:
            self.num_periods += 1
            self.last_time = time_now
            self.task()
            return time_left
        return time_left
