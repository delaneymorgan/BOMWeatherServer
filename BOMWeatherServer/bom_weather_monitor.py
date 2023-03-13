#!/usr/bin/env python3
# coding=utf-8

from dateutil import parser as du_parser
from ftplib import FTP
from periodic import Periodic
from threading import Thread, Lock
import io
import json
import requests
import time
import untangle


from BOMWeatherServer.weather_pending import WeatherPending
from BOMWeatherServer.urls import OBSERVATION_URL, FORECAST_HOST, FORECAST_PATH


# =============================================================================


class BOMWeatherMonitor(Thread):
    BOM_ICONS = {
        '1': "sunny",
        '2': "clear",
        '3': "partly-cloudy",
        '3n': "partly-cloudy-night",
        '4': "cloudy",
        '6': "haze",
        '6n': "haze-night",
        '8': "light-rain",
        '9': "wind",
        '10': "fog",
        '10n': "fog-night",
        '11': "showers",
        '11n': "showers-night",
        '12': "rain",
        '13': "dust",
        '14': "frost",
        '15': "snow",
        '16': "storm",
        '17': "light-showers",
        '17n': "light-showers-night",
        '18': "heavy-showers",
        '19': "tropicalcyclone"
    }

    def __init__(self, my_args, my_globals, observation_interval, forecast_interval):
        super(BOMWeatherMonitor, self).__init__()
        self.weather_lock = Lock()
        self.my_args = my_args
        self.globals = my_globals
        self.observation_interval = observation_interval
        self.forecast_interval = forecast_interval
        self.forecast_to_observation = {}
        self.observation = {}       # {observation_place:{observation={temp_now:<float>}, periodic=Periodic}}
        self.forecast = {}          # {forecast_place:{forecast={}, periodic=Periodic}}
        return

    def get_observation(self, observation_place):
        # noinspection PyUnresolvedReferences
        if self.my_args.verbose:
            print(f"Getting observation for {observation_place}")
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

    @staticmethod
    def _decode_elements(forecast_elements, timestamp=None):
        info = {}
        # NOTE: sometimes this is a single dict, other times it's a list of dicts.
        if "type" in forecast_elements:
            # it's a single dict
            if forecast_elements["type"] == "forecast_icon_code":
                icon_code = forecast_elements.cdata
                info["icon_name"] = BOMWeatherMonitor.BOM_ICONS.get(icon_code, "blank")
            elif forecast_elements["type"] == "air_temperature_maximum":
                info["temp_max"] = float(forecast_elements.cdata)
            elif forecast_elements["type"] == "air_temperature_minimum":
                info["temp_min"] = float(forecast_elements.cdata)
        else:
            # it's an array of dicts
            for thisElement in forecast_elements:
                if thisElement["type"] == "forecast_icon_code":
                    icon_code = str(thisElement.cdata)
                    info["icon_name"] = BOMWeatherMonitor.BOM_ICONS.get(icon_code, "blank")
                elif thisElement["type"] == "air_temperature_maximum":
                    info["temp_max"] = float(thisElement.cdata)
                elif thisElement["type"] == "air_temperature_minimum":
                    info["temp_min"] = float(thisElement.cdata)
        if timestamp:
            d = du_parser.parse(timestamp)
            this_time = time.mktime(d.timetuple()) + d.microsecond / 1E6
            info["timestamp"] = this_time
        return info

    def get_forecast(self, forecast_place):
        # noinspection PyUnresolvedReferences
        if self.my_args.verbose:
            print(f"Getting forecast for {forecast_place}")
        ftp = FTP(FORECAST_HOST)
        ftp.login()
        fc_path = FORECAST_PATH.format(forecast_place)
        out_str = io.StringIO()
        ftp.retrlines("RETR " + fc_path, out_str.write)
        elements = untangle.parse(out_str.getvalue())
        out_str.close()
        area = elements.product.forecast.area[2]
        today_elements = area.forecast_period[0]
        tfc_elements = today_elements.element
        info = self._decode_elements(tfc_elements)
        periods_forecast = area.forecast_period
        observation_place = self.forecast_to_observation[forecast_place]
        # today's forecast is mixed in with the general forecast
        # we regard today's forecast as part of the observation
        forecast_today = {}
        for key in info:
            forecast_today[key] = info[key]
        forecast = []
        for day_forecast in periods_forecast:
            day_elements = day_forecast.element
            info = self._decode_elements(day_elements, day_forecast["start-time-local"])
            forecast.append(info)
        with self.weather_lock:
            self.forecast[forecast_place]["forecast"] = forecast
            self.observation[observation_place]["observation"].update(forecast_today)
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
            self.forecast_to_observation[forecast_place] = observation_place
            if new_observation or new_forecast:
                raise WeatherPending(observation_place, forecast_place)
            results = dict(observation=self.observation[observation_place]["observation"],
                           forecast=self.forecast[forecast_place]["forecast"])
            return results

    def _add_observation(self, observation_place):
        periodic = Periodic(self.observation_interval, self.get_observation, f"observation-{observation_place}")
        self.observation[observation_place] = dict(observation={}, periodic=periodic)
        return

    def _add_forecast(self, forecast_place):
        periodic = Periodic(self.forecast_interval, self.get_forecast, f"forecast-{forecast_place}")
        self.forecast[forecast_place] = dict(forecast={}, periodic=periodic)
        return

