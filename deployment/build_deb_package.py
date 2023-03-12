#!/usr/bin/env python
# coding=utf-8

import argparse
import PackageBuilder
from VersionValidator import ValidateVersionNumber

# =============================================================================


BUILD_INFO_FILEPATH = "../BOMWeatherServer_file_list.json"


# =============================================================================


def arg_parser():
    """
    parse arguments

    :return: the parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="makes BOMWeatherServer a package for the specified target",
                                     add_help=False)
    parser.add_argument("-v", "--version", type=str, help="version#, i.e. x.y.z",
                        required=True, action=ValidateVersionNumber)
    parser.add_argument("-?", "--help", help="show help message and quit", action="help")
    args = parser.parse_args()
    return args


def main():
    args = arg_parser()
    try:
        builder = PackageBuilder.PackageBuilder("BOMWeatherServer", BUILD_INFO_FILEPATH, args.version)
        builder.build_debian()
    except Exception as ex:
        print(f"Error: {ex}")
    return


if __name__ == '__main__':
    main()
