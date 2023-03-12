#!/usr/bin/env python3
# coding=utf-8

from http.server import BaseHTTPRequestHandler, HTTPServer
import argparse
from functools import partial
import json
import re
from threading import Thread, Lock
import time
import untangle
from urllib import parse

import BOMWeatherServer
from BOMWeatherServer.version import __version__, __description__
from BOMWeatherServer.periodic import Periodic

# =============================================================================


OBSERVATION_INTERVAL = 10     # 10 seconds
FORECAST_INTERVAL = 15        # 15 seconds
PLACE_CODE_REGEX = r"^[A-Z]{3}\d{5}$"

gRunning = True


# =============================================================================


class WeatherPending(Exception):
    def __init__(self, observation_place, forecast_place):
        super(WeatherPending, self).__init__()
        self.observation_place = observation_place
        self.forecast_place = forecast_place
        return


# =============================================================================


class InvalidPlaceCode(Exception):
    def __init__(self, place_code):
        super(InvalidPlaceCode, self).__init__()
        self.place_code = place_code
        return


# =============================================================================


class InvalidParameters(Exception):
    pass


# =============================================================================


class BOMWeatherMonitor(Thread):
    def __init__(self):
        super(BOMWeatherMonitor, self).__init__()
        self.weather_lock = Lock()
        self.observation = {}       # {observation_place:{observation={}, periodic=Periodic}}
        self.forecast = {}          # {forecast_place:{forecast={}, periodic=Periodic}}
        return

    def get_observation(self, observation_place):
        # TODO: get observation
        print(f"observing {observation_place}")
        observation = dict(temp_now=22, temp_min=12, temp_max=25, icon_name="sunny")
        with self.weather_lock:
            self.observation[observation_place]["observation"] = observation
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
        while gRunning:
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
        periodic = Periodic(OBSERVATION_INTERVAL, self.get_observation, f"obsersation-{observation_place}")
        self.observation[observation_place] = dict(observation={}, periodic=periodic)
        return

    def _add_forecast(self, forecast_place):
        periodic = Periodic(FORECAST_INTERVAL, self.get_forecast, f"forecast-{forecast_place}")
        self.forecast[forecast_place] = dict(forecast={}, periodic=periodic)
        return


# =============================================================================


class MyServerHandler(BaseHTTPRequestHandler):
    def __init__(self, monitor, *args, **kwargs):
        self.monitor = monitor
        self.place_code_re = re.compile(PLACE_CODE_REGEX)
        super(MyServerHandler, self).__init__(*args, **kwargs)
        return

    def do_HEAD(self, code):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        return

    def validate_parameters(self):
        try:
            query = parse.urlparse(self.path).query
            parameters = parse.parse_qs(query)
            observation_place = parameters["observation"][0].upper()
            if not self.place_code_re.match(observation_place):
                raise InvalidPlaceCode(observation_place)
            forecast_place = parameters["forecast"][0].upper()
            if not self.place_code_re.match(forecast_place):
                raise InvalidPlaceCode(forecast_place)
        except InvalidPlaceCode:
            raise
        except:
            raise InvalidParameters()
        return observation_place, forecast_place

    # noinspection PyPep8Naming
    def do_GET(self):
        try:
            observation_place, forecast_place = self.validate_parameters()
            weather = self.monitor.get_weather(observation_place, forecast_place)
            self.do_HEAD(200)
            json_text = json.dumps(weather)
            self.wfile.write(json_text.encode("utf8"))
        except InvalidParameters:
            self.do_HEAD(400)
            msg = dict(reason=f"place codes for observation and forecast required: "
                              f"http://<host>:<port>?observation=XXXXXXXX&forecast=XXXXXXXX")
            json_text = json.dumps(msg)
            self.wfile.write(json_text.encode("utf8"))
        except InvalidPlaceCode as ex:
            self.do_HEAD(400)
            msg = dict(reason=f"place code {ex.place_code} is not valid")
            json_text = json.dumps(msg)
            self.wfile.write(json_text.encode("utf8"))
        except WeatherPending as ex:
            self.do_HEAD(451)
            msg = dict(reason=f"weather pending for location {ex.observation_place}/{ex.forecast_place}")
            json_text = json.dumps(msg)
            self.wfile.write(json_text.encode("utf8"))
        return

    # noinspection PyShadowingBuiltins
    def log_message(self, format: str, *args: any) -> None:
        # DO NOTHING - NO NEED TO SPAM LOGS
        return


# =============================================================================


def arg_parser():
    """
    parse arguments

    :return: the parsed command line arguments
    """
    parser = argparse.ArgumentParser(prog=f"{BOMWeatherServer.__name__}",
                                     description=f"{BOMWeatherServer.__name__} - {__description__}", add_help=False)
    parser.add_argument("-l", "--listener", help="listener name/address. 0.0.0.0 for any listener.", required=True)
    parser.add_argument("-p", "--port", type=int, help="port#", required=True)
    parser.add_argument("--version", action="version", version=f"{BOMWeatherServer.__name__} {__version__}")
    parser.add_argument("-?", "--help", help="show help message and quit", action="help")
    args = parser.parse_args()
    return args


# =============================================================================


def main():
    args = arg_parser()
    monitor = BOMWeatherMonitor()
    handler = partial(MyServerHandler, monitor)
    server = HTTPServer(('', args.port), handler)
    print(f"{BOMWeatherServer.__name__} started http://{args.listener}:{args.port}")
    monitor.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        global gRunning
        gRunning = False
    server.server_close()
    print(f"{BOMWeatherServer.__name__} stopped")
    return


if __name__ == '__main__':
    main()
