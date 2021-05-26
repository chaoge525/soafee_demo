#!/usr/bin/env python3
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

"""Ewaol pycodestyle

This script allows user to run code check on python files.
Code style is analyzed with pycodestyle.

This tool takes first argument as a path to check.
It also allows to exlude files or directories with '--exclude' option.

There are three log levels available to set with '--log':
warning(default), info and debug.
"""

import argparse
import logging
import os
import subprocess
import sys

import magic


def run_pycodestyle(path, exclude):
    """
    Run pycodecheck on given file or directory.
    """
    if (os.path.isfile(path) and
            magic.from_file(path, mime=True) != 'text/x-python'):
        return

    pycodestylebin = sys.exec_prefix + '/bin/pycodestyle'
    if not os.path.isfile(pycodestylebin):
        pycodestylebin = 'pycodestyle'

    args = [pycodestylebin, path]
    if exclude:
        args.append(f"--exclude={','.join(exclude)}")
    subprocess.run(args)


def main(args=None):
    if sys.version_info < (3, 6):
        raise ValueError('This script requires Python 3.6 or later')

    loglevels = {
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
    }

    desc = "Runs pycodestyle on selected file or directory"
    parser = argparse.ArgumentParser(prog=__name__, description=desc)
    parser.add_argument('pathtocheck', nargs='?',
                        help='A file or directory to run code check.')
    parser.add_argument('--exclude', default=None,
                        dest='pathtoexclude', action='append',
                        help='A path to exclude code check.')
    parser.add_argument('--log', default='warning', dest='log',
                        help='Set log level to warning, info or debug.')

    options = parser.parse_args(args)
    logger.setLevel(loglevels.get(options.log.lower()))
    logger.debug(options)

    run_pycodestyle(options.pathtocheck, options.pathtoexclude)


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)-6s:%(funcName)-20s:%(message)s')
    logger = logging.getLogger(__name__)

    rc = 1
    try:
        main()
        rc = 0
    except Exception as e:
        logger.error(e)
    sys.exit(rc)
