#!/usr/bin/python3

import argparse
import json
import logging
import os

import util


file_abspath = os.path.abspath(__file__)
parent_directory = os.path.split(os.path.split(file_abspath)[0])[0]

example_settings = {
  "mode": {
    "auto": False,
    "program": 0,
    "manual": False,
    "desired_temp": 19.5
  },
  "temperatures": {
    "room": 20.0
  },
  "log": {
    "loglevel": "INFO",
    "session": "",
    "last_day_on": "1970-01-01",
    "time_elapsed": "0:00:00",
  },
  "paths": {
    "daily_log": os.path.join(parent_directory, "logs/log.json"),
    "relay_stat": os.path.join(parent_directory, "settings/stats.json"),
    "program": os.path.join(parent_directory, "programs/program.json"),
    "examples": os.path.join(parent_directory, "examples")
  },
  "configs": {
    "UDP_IP": "127.0.0.1",
    "UDP_port": 2222
  },
  "poll_intervals": {
    "settings": 1,
    "temperature": 5
  },
  "relay": {
    "channel": 36,
    "direction": 0,
    "initial": 1
  }
}

logger_name = 'thermostat.settings'
logger = logging.getLogger(logger_name)


def create_parser():
    '''
    Defines script's arguments.
    '''

    parser = argparse.ArgumentParser(
        description=(
            'Edits the settings.json file ruling the heater behavior.'
        )
    )

    parser.add_argument(
        '-a', '--auto',
        help='Set auto to ON. Turns ON heater according to program.'
    )

    parser.add_argument(
        '-l', '--loglevel',
        help='Defines the log level for logger in scripts.',
        type=str
    )

    parser.add_argument(
        '-m', '--manual',
        help='Set manual to ON. Turns ON heater.'
    )

    parser.add_argument(
        '-p', '--program',
        help='Insert the program number you wish to load.',
        type=int
    )

    parser.add_argument(
        '-t', '--temperature',
        help='Insert the desired temperature when in manual mode.',
        type=float
    )

    args = parser.parse_args()
    logger.debug(
        f'manual: {args.manual}; auto: {args.auto}; program: {args.program};'
    )

    def string_to_bool(arg):

        if arg is not None and isinstance(arg, str):
            if arg.lower() in {'true', 't', 'yes', 'y', 'on', '1'}:
                return True
            elif arg.lower() in {'false', 'f', 'no', 'n', 'off', '0'}:
                return False
            else:
                raise parser.error(
                    'Please enter a boolean-like value for this argument.'
                )
        else:
            pass

    def int_to_string(arg):

        if arg is not None:
            if isinstance(arg, int):
                return str(arg)
            else:
                raise parser.error(
                    'Please enter an integer.'
                )

    args.manual = string_to_bool(args.manual)
    args.auto = string_to_bool(args.auto)

    logger.debug(
        f'manual: {args.manual}; auto: {args.auto}; program: {args.program};'
    )

    if (
        args.auto is None and
        args.loglevel is None and
        args.manual is None and
        args.program is None and
        args.temperature is None
    ):
        raise parser.error(
            'Please enter at least one argument.'
            " Type '--help' for more information."
        )

    return args


def main(time_elapsed=None):
    '''
    Function called when script is called directly.
    Takes argument from argparse defined in create_parser function.
    '''

    args = create_parser()

    settings_path = os.path.join(parent_directory, 'settings/settings.json')
    settings_file = load_settings(settings_path)
    # define all fields that can be changed using this module
    settings_changes = {
        'mode': {
            'auto': (
                args.auto if args.auto is not None
                else settings_file['mode']['auto']
            ),
            'program': (
                args.program if args.program is not None
                else settings_file['mode']['program']
            ),
            'manual': (
                args.manual if args.manual is not None
                else settings_file['mode']['manual']
            ),
            'desired_temp': (
                args.temperature if args.temperature is not None
                else settings_file['mode']['desired_temp']
            )
        },
        'log': {
            'loglevel': (
                args.loglevel if args.loglevel is not None
                else settings_file['log']['loglevel']
            )
        }
    }

    return handler(
        settings_path=settings_path,
        settings_changes=settings_changes
    )


def load_settings(settings_path):
    '''
    Return setting in 'setting.json' file in a python dictionary.
    '''

    if not os.path.isfile(settings_path) or not os.stat(settings_path).st_size:
        logger.info('{} not found, creating.'.format(settings_path))
        settings_parent = os.path.split(settings_path)[0]
        if not os.path.isdir(settings_parent):
            os.mkdir(settings_parent)
        with open(settings_path, 'w') as f:
            json.dump(example_settings, f, indent=2)
        logger.debug('Created new settings.json file from example.')

    with open(settings_path) as f:
        settings_file = json.load(f)

    return settings_file


def update_settings(settings_changes, settings_file, settings_path):
    '''
    Write settings_changes to 'setting.json' file.
    Returns contents of the file in a python dictionary.
    '''

    if settings_changes != settings_file:
        settings_changes = json.dumps(settings_changes, indent=2)
        logger.debug('\n' + settings_changes)
        logger.debug('Settings changed!')
        with open(settings_path, 'w') as f:
            f.write(settings_changes)
            f.write('\n')
    else:
        logger.debug('Settings not changed.')

    return load_settings(settings_path)


def handler(settings_path, settings_changes={}):
    '''
    Sends updates to update_settings function.
    Returns contents of 'settings.json' after updates in a python dictionary.
    '''

    settings_file = load_settings(settings_path)

    logger.debug('Settings file read: {}'.format(settings_file))
    logger.debug('Settings before update: {}'.format(settings_changes))

    # nested dict update of settings_changes
    settings_changes = {
        k:( # take outer from settings_file if not in settings_changes
            {kk:v for kk, v in settings_file[k].items()}
            if k not in settings_changes
            else { # if exists in both go deeper
                kk:( # if key not in settings_changes take v from settings_file
                    v if kk not in settings_changes[k]
                    else settings_changes[k][kk] # from settings_changes else
                ) for kk, v in settings_file[k].items()
            }
        ) for k in settings_file
    }

    logger.debug('Settings after update: {}'.format(settings_changes))

    return update_settings(settings_changes, settings_file, settings_path)


if __name__ == '__main__':

    main()
