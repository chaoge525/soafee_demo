#!/usr/bin/env python3
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

"""Ewaol shell-check

This script allows user to run code check on shell script files.
Code style is analyzed with shellcheck.

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


def shellcheck_file(path):
    """
    Run shellcheck for given file.
    """

    logger.debug('check file mimetype: %s', path)
    f_type = magic.from_file(path, mime=True)
    if f_type == 'text/x-shellscript' or path.endswith('.bats'):
        logger.info('Shellchecking file: %s', path)
        subprocess.run([f"{sys.exec_prefix}/bin/shellcheck", path])


def run_shellcheck(path, exclude):
    """
    Run shellcheck for given file or
    if path is a directory, filter out all shell scripts form given directory,
    include subdirectories and exclude directories form exclude list,
    and run shellcheck for all entries.
    """
    if os.path.isfile(path):
        shellcheck_file(path)
        return

    with os.scandir(path) as tree:
        for entry in sorted(tree, key=lambda entry: entry.path):
            if not entry.name.startswith('.'):
                relativepath = entry.path.replace(f"{os.getcwd()}/", '', 1)
                # check if directory or file is in exclude list
                if exclude and any(map(relativepath.__contains__, exclude)):
                    logger.info(f"Skipping excluded file: {relativepath} "
                                f"from list: {exclude}")
                    continue
                if entry.is_file():
                    shellcheck_file(entry.path)
                if entry.is_dir():
                    run_shellcheck(entry.path, exclude)


def main(args=None):
    if sys.version_info < (3, 6):
        raise ValueError('This script requires Python 3.6 or later')

    loglevels = {
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
    }

    desc = "Runs shellcheck on selected file or directory"
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

    exlist = list()
    if options.pathtoexclude:
        for ex in options.pathtoexclude:
            exlist += ex.split(',')
    logger.debug(exlist)
    run_shellcheck(options.pathtocheck, exlist)


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
