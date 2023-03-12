import argparse


class ValidateVersionNumber(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        parts = values.split(".")
        if len(parts) != 3:
            parser.error(f"Please enter a valid version number in <major>.<minor>.<maintenance> format")
        for part in parts:
            if not part.isdigit():
                parser.error(f"Please enter a valid version number in <major>.<minor>.<maintenance> format")
        setattr(namespace, self.dest, values)
        return
