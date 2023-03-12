#!/usr/bin/env python3
# coding=utf-8

from http.server import BaseHTTPRequestHandler, HTTPServer
import argparse
from functools import partial
import json
from threading import Thread, Lock
import time
import untangle

import BOMWeatherServer
from BOMWeatherServer.version import __version__, __description__
from BOMWeatherServer.periodic import Periodic

# =============================================================================


OBSERVATION_INTERVAL = 10     # 10 seconds
FORECAST_INTERVAL = 15        # 15 seconds

gRunning = True


# =============================================================================


class BOMWeatherMonitor(Thread):
    def __init__(self, observation_place, forecast_place):
        super(BOMWeatherMonitor, self).__init__()
        self.observation_place = observation_place
        self.forecast_place = forecast_place
        self.weather_lock = Lock()
        self.observation = None
        self.forecast = None
        self.observation_periodic = Periodic(OBSERVATION_INTERVAL, self.get_observation, "observation")
        self.forecast_periodic = Periodic(FORECAST_INTERVAL, self.get_forecast, "forecast")
        return

    def get_observation(self):
        # TODO: get observation
        print("observing")
        with self.weather_lock:
            self.observation = dict(temp_now=22, temp_min=12, temp_max=25, icon_name="sunny")
        return

    def get_forecast(self):
        # TODO: get forecast
        print("forecasting")
        with self.weather_lock:
            self.forecast = [
                dict(dow="Mon", temp_max="25", icon_name="sunny"),
                dict(dow="Tue", temp_max="20", icon_name="clear"),
                dict(dow="Wed", temp_max="22", icon_name="partly-cloudy"),
                dict(dow="Thu", temp_max="23", icon_name="rain"),
                dict(dow="Fri", temp_max="24", icon_name="storm")
            ]
        return

    def run(self):
        while gRunning:
            self.observation_periodic.check()
            self.forecast_periodic.check()
            time.sleep(1)
        return

    def get_weather(self):
        with self.weather_lock:
            results = dict(observation=self.observation, forecast=self.forecast)
            return results


# =============================================================================


class MyServerHandler(BaseHTTPRequestHandler):
    def __init__(self, monitor, *args, **kwargs):
        self.monitor = monitor
        super(MyServerHandler, self).__init__(*args, **kwargs)
        return

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        return

    # noinspection PyPep8Naming
    def do_GET(self):
        self.do_HEAD()
        weather = self.monitor.get_weather()
        json_text = json.dumps(weather)
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
    parser.add_argument("-o", "--observation", help="observation place code.", required=True)
    parser.add_argument("-f", "--forecast", help="forecast place code.", required=True)
    parser.add_argument("--version", action="version", version=f"{BOMWeatherServer.__name__} {__version__}")
    parser.add_argument("-?", "--help", help="show help message and quit", action="help")
    args = parser.parse_args()
    return args


# =============================================================================


def main():
    args = arg_parser()
    monitor = BOMWeatherMonitor(args.observation, args.forecast)
    handler = partial(MyServerHandler, monitor)
    server = HTTPServer(('', args.port), handler)
    print(f"{BOMWeatherServer.__name__} started http://{args.listener}:{args.port} "
          f"for {args.observation}/{args.forecast}")
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
