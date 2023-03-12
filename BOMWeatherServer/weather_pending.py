#!/usr/bin/env python3
# coding=utf-8

class WeatherPending(Exception):
    def __init__(self, observation_place, forecast_place):
        super(WeatherPending, self).__init__()
        self.observation_place = observation_place
        self.forecast_place = forecast_place
        return
