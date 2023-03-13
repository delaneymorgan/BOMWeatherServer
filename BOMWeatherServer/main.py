#!/usr/bin/env python3
# coding=utf-8

from functools import partial
from http.server import HTTPServer
import argparse

import BOMWeatherServer
from BOMWeatherServer.version import __version__, __description__
from bom_weather_monitor import BOMWeatherMonitor
from bom_weather_server import MyServerHandler

# =============================================================================


OBSERVATION_INTERVAL = 10  # 10 seconds
FORECAST_INTERVAL = 15  # 15 seconds


# =============================================================================


class Globals(object):
    def __init__(self):
        self.running = True
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
    parser.add_argument("-v", "--verbose", help="verbose mode", action="store_true")
    parser.add_argument("--version", action="version", version=f"{BOMWeatherServer.__name__} {__version__}")
    parser.add_argument("-?", "--help", help="show help message and quit", action="help")
    args = parser.parse_args()
    return args


# =============================================================================


def main():
    my_args = arg_parser()
    my_globals = Globals()
    monitor = BOMWeatherMonitor(my_args, my_globals, OBSERVATION_INTERVAL, FORECAST_INTERVAL)
    handler = partial(MyServerHandler, my_args, monitor)
    server = HTTPServer(('', my_args.port), handler)
    print(f"{BOMWeatherServer.__name__} started http://{my_args.listener}:{my_args.port}")
    monitor.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        my_globals.running = False
    server.server_close()
    print(f"{BOMWeatherServer.__name__} stopped")
    return


if __name__ == '__main__':
    main()
