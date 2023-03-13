#!/usr/bin/env python3
# coding=utf-8

from periodic import Periodic
from threading import Thread, Lock
import json
import requests
import time
import untangle


from BOMWeatherServer.weather_pending import WeatherPending
from BOMWeatherServer.urls import OBSERVATION_URL


# =============================================================================


class BOMWeatherMonitor(Thread):
    def __init__(self, globals, observation_interval, forecast_interval):
        super(BOMWeatherMonitor, self).__init__()
        self.weather_lock = Lock()
        self.globals = globals
        self.observation_interval = observation_interval
        self.forecast_interval = forecast_interval
        self.observation = {}       # {observation_place:{observation={temp_now:<float>}, periodic=Periodic}}
        self.forecast = {}          # {forecast_place:{forecast={}, periodic=Periodic}}
        return

    def get_observation(self, observation_place):
        print(f"observing {observation_place}")
        url = OBSERVATION_URL.format(observation_place, observation_place)
        try:
            resp = requests.get(url)
            if resp:
                # observations typically contains many (hundreds, perhaps),
                # lets just grab the current observation.
                content_json = resp.content
                content = json.loads(content_json)
                observation = content["observations"]["data"][0]
                with self.weather_lock:
                    self.observation[observation_place]["observation"]["temp_now"] = observation["air_temp"]
        except Exception as ex:
            print(f"Error: {type(ex)}/{ex}")
        return

    def get_forecast(self, forecast_place):
        # TODO: get forecast
        print(f"forecasting {forecast_place}")
        forecast = [
            dict(dow="Mon", temp_max="25", icon_name="sunny"),
            dict(dow="Tue", temp_max="20", icon_name="clear"),
            dict(dow="Wed", temp_max="22", icon_name="partly-cloudy"),
            dict(dow="Thu", temp_max="23", icon_name="rain"),
            dict(dow="Fri", temp_max="24", icon_name="storm")
        ]
        with self.weather_lock:
            self.forecast[forecast_place]["forecast"] = forecast
        return

    def run(self):
        while self.globals.running:
            for place, info in self.observation.items():
                if info["periodic"].check(place):
                    # limit positive checks to one/loop for responsiveness
                    break
            for place, info in self.forecast.items():
                if info["periodic"].check(place):
                    # limit positive checks to one/loop for responsiveness
                    break
            time.sleep(1)
        return

    def get_weather(self, observation_place, forecast_place):
        with self.weather_lock:
            new_forecast = False
            new_observation = False
            if observation_place not in self.observation:
                new_observation = True
                self._add_observation(observation_place)
            if forecast_place not in self.forecast:
                new_forecast = True
                self._add_forecast(forecast_place)
            if new_observation or new_forecast:
                raise WeatherPending(observation_place, forecast_place)
            results = dict(observation=self.observation[observation_place]["observation"],
                           forecast=self.forecast[forecast_place]["forecast"])
            return results

    def _add_observation(self, observation_place):
        periodic = Periodic(self.observation_interval, self.get_observation, f"obsersation-{observation_place}")
        self.observation[observation_place] = dict(observation={}, periodic=periodic)
        return

    def _add_forecast(self, forecast_place):
        periodic = Periodic(self.forecast_interval, self.get_forecast, f"forecast-{forecast_place}")
        self.forecast[forecast_place] = dict(forecast={}, periodic=periodic)
        return

