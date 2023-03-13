#!/usr/bin/env python3
# coding=utf-8

from http.server import BaseHTTPRequestHandler
from urllib import parse
import json
import re

from BOMWeatherServer.weather_pending import WeatherPending

# =============================================================================


PLACE_CODE_REGEX = r"^[A-Z]{3}\d{5}$"


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


class MyServerHandler(BaseHTTPRequestHandler):
    def __init__(self, my_args, monitor, *args, **kwargs):
        self.my_args = my_args
        self.monitor = monitor
        self.place_code_re = re.compile(PLACE_CODE_REGEX)
        super(MyServerHandler, self).__init__(*args, **kwargs)
        return

    # noinspection PyPep8Naming
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
        except WeatherPending as ex:
            self.do_HEAD(451)
            msg = dict(reason=f"weather pending for location {ex.observation_place}/{ex.forecast_place}")
            json_text = json.dumps(msg)
            self.wfile.write(json_text.encode("utf8"))
        except InvalidParameters:
            self.do_HEAD(400)
            msg = dict(reason=f"place codes for observation and forecast required: "
                              f"http://<host>:<port>?observation=<place>&forecast=<place>")
            json_text = json.dumps(msg)
            self.wfile.write(json_text.encode("utf8"))
        except InvalidPlaceCode as ex:
            self.do_HEAD(400)
            msg = dict(reason=f"place code {ex.place_code} is not valid")
            json_text = json.dumps(msg)
            self.wfile.write(json_text.encode("utf8"))
        return

    # noinspection PyShadowingBuiltins
    def log_message(self, format: str, *args: any) -> None:
        # DO NOTHING - NO NEED TO SPAM LOGS
        return
