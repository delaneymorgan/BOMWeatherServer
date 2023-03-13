# BOMWeatherServer
A simple Australian Bureau of Meteorology weather server

## Usage:

    BOMWeatherServer -l <listener> -p <port> [--version] [-?]

The server will answer queries from the specified listener on the specified port with the current local time in JSON format.
Specify 127.0.0.1 for only listeners inside the same machine as the server.
Specify 0.0.0.0 for all listeners.

Enter the -? option to view command-line options.

### BoM Observation/Forecast Place Codes

You will need to know these codes for your location in order to drive the webservice.
The BoM location codes are somewhat cryptic.
i.e. an observation place code of IDV60901 refers to Melbourne.
A forecast place code of IDV10450 also refers to Melbourne.

For instance:

    BOMWeatherServer -l 0.0.0.0 -p 10124

... and in a browser, enter:

    http://<BOMWeatherServer Host>:10124/?observation=IDV60901&forecast=IDV10450

The first attempt should fail with a 451 response code and a "try again" reason.

Eventually, It should return something like this:

    {
      "observation": {
        "temp_now": 19.7,
        "icon_name": "partly-cloudy",
        "temp_max": 23.0
      },
      "forecast": [
        {
          "icon_name": "partly-cloudy",
          "temp_max": 23.0,
          "timestamp": 1678647600.0
        },
        {
          "icon_name": "partly-cloudy",
          "temp_min": 13.0,
          "temp_max": 29.0,
          "timestamp": 1678716000.0
        },
        {
          "icon_name": "cloudy",
          "temp_min": 16.0,
          "temp_max": 27.0,
          "timestamp": 1678802400.0
        },
        {
          "icon_name": "partly-cloudy",
          "temp_min": 18.0,
          "temp_max": 29.0,
          "timestamp": 1678888800.0
        },
        {
          "icon_name": "partly-cloudy",
          "temp_min": 15.0,
          "temp_max": 26.0,
          "timestamp": 1678975200.0
        },
        {
          "icon_name": "partly-cloudy",
          "temp_min": 15.0,
          "temp_max": 25.0,
          "timestamp": 1679061600.0
        },
        {
          "icon_name": "partly-cloudy",
          "temp_min": 14.0,
          "temp_max": 24.0,
          "timestamp": 1679148000.0
        }
      ]
    }

## Building Python Package:

You may need to install virtual environment support for your python version:

    sudo apt install python<X.X>-venv

...where X.X is the python version on your system.
i.e. python3.10 would be python3.10-venv.
Note that LocalTimeServer requires Python 3.6 or later.

From this directory:

    python3 build .

To install the built package:

    pip3 install ./dist/BOMWeatherServer-<VERSION>-py3-none-any.whl --force-reinstall

...where VERSION is the version of BOMWeatherServer you have just built (see version.py).
This will install BOMWeatherServer just for the current user in .local/bin.
To install system-wide, use sudo.

## Building Debian package

Firstly, install pre-requisites:

    sudo apt install build-essential binutils lintian debhelper dh-make devscripts

from the deployment folder, run:

    ./build_deb_package.py -v <version>

...where version is in a <major>.<minor>.<maintenance> format.
The produced package will have the form:

    BOMWeatherServer-<version>.deb

## Installing into OS

Ubuntu/Debian:

    sudo dpkg -i BOMWeatherServer-<version>.deb

Raspbian:

    sudo ./install_on_raspbian.py

## Updating Version#:

The version number is kept here:

    ./BOMWeatherServer/version.py
