#!/usr/bin/env python3
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

"""Ewaol code check

This script allows user to run code check on shell and python files.
Code style is analyzed with:
 - shellcheck for shell scripts
 - pycodestyle for python scripts
It creates a Python venv under $TMP directory, installs all dependencies,
runs all checks and deletes it on exit.

This tool takes first argument as a path to check('.' is default)
It also allows to exlude files or directories with '--exclude' option.

There are three log levels available to set with '--log':
warning(default), info and debug.
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import venv


class CodeCheckEnvBuilder(venv.EnvBuilder):
    """
    This builder installs all packages required by Ewaol code check script,
    in temporary directory and runs code check.

    Attributes
    ----------
    pathtocheck: string
        Directory or file to check (default is '.')
    pathtoexclude: list
        Coma separated list of directories and files to exclude
        from shellcheck and pycodestyle (default is None)
    log: string
        Log level, it can be warning, info or debug (default is warning)

    Methods
    -------
    post_setup(context)
        Set up all packages which need to be pre-installed into the
        environment, to run shellcheck and pycodestyle.
    install_script(context, name, url)
        Install package from given url.
    pip_run_command(context, command, package=None)
        Run pip command.
    """

    def __init__(self, pathtocheck, pathtoexclude, logger):
        """
        Parameters
        ----------
        pathtocheck: str
            Directory or file to check (default is '.')
        pathtoexclude: list
            Coma separated list of directories and files to exclude
            from shellcheck and pycodestyle (default is None)
        log: string, optional
            Log level, it can be warning, info or debug (default is warning)
        """
        self.pathtocheck = pathtocheck
        self.pathtoexclude = pathtoexclude
        self.logger = logger
        super().__init__()

    def post_setup(self, context):
        """
        Set up all packages which need to be pre-installed into the
        environment, to run shellcheck and pycodestyle.

        Parameters
        ----------
        context: context object
            The information for the environment creation request
            being processed.
        """
        os.environ['VIRTUAL_ENV'] = context.env_dir

        self.pathtoexclude = (f"{context.env_name},"
                              f"{','.join(self.pathtoexclude)}")
        self.pathtoexclude = self.pathtoexclude.rstrip(',')

        url_setuptools = 'https://bootstrap.pypa.io/ez_setup.py'
        self.install_script(context, 'setuptools', url_setuptools)

        url_pip = 'https://bootstrap.pypa.io/get-pip.py'
        self.install_script(context, 'pip', url_pip)

        self.pip_run_command(context, 'install', 'pycodestyle')
        self.pip_run_command(context, 'install', 'shellcheck-py')
        self.pip_run_command(context, 'install', 'python-magic')

        # install and run scripts: shell_check and pycodestyle:
        for script in ['run_shellcheck.py', 'run_pycodestyle.py']:
            src = f"{os.path.dirname(os.path.abspath(__file__))}/{script}"
            self.logger.info(script.replace('_', ' ').rstrip('.py'))
            shutil.copy(src, context.bin_path)
            loglvl = f"{logging.getLevelName(self.logger.getEffectiveLevel())}"
            args = ([context.env_exe, os.path.join(context.bin_path, script),
                     os.path.abspath(self.pathtocheck), '--exclude',
                     self.pathtoexclude, '--log', loglvl])
            subprocess.check_call(args)

    def install_script(self, context, name, url):
        """
        Install package from given url.

        Parameters
        ----------
        context: context object
            The information for the environment creation request
            being processed.
        name: str
            Package name to install.
        url: str
            Link to python installation script.
        """
        script = os.path.basename(url)
        binpath = context.bin_path
        distpath = os.path.join(binpath, script)
        # Download script into the env's binaries folder
        urllib.request.urlretrieve(url, distpath)
        self.logger.info('Installing %s ...', name)
        sys.stderr.flush()
        # Install in the env
        args = [context.env_exe, script]
        process = subprocess.Popen(args, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, cwd=binpath)
        stdout, stderr = process.communicate()
        self.logger.debug(stdout.decode())
        self.logger.debug(stderr.decode())
        process.wait()
        self.logger.debug('done.')
        # Clean up - no longer needed
        os.unlink(distpath)

    def pip_run_command(self, context, command, package=None):
        """
        Run pip command

        Parameters
        ----------
        context: context object
            The information for the environment creation request
            being processed.

        command: str
            Pip command to be executed, e.g. install
        package: str, optional
            Argument for pip command, e.g. package (default is None)
        """
        loglvl = None
        args = [context.env_exe, "-m", "pip", command]
        if self.logger.getEffectiveLevel() > logging.INFO:
            loglvl = '-q'
        if self.logger.getEffectiveLevel() == logging.DEBUG:
            loglvl = '-v'
        if package:
            args.append(package)
        if loglvl:
            args.append(loglvl)
        subprocess.check_call(args)


def main(args=None):
    if sys.version_info < (3, 6):
        raise ValueError('This script requires Python 3.6 or later')
    loglevels = {
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
    }

    desc = ("Creates virtual Python environment and runs "
            "shellcheck and pycodestyle in target path.")
    parser = argparse.ArgumentParser(prog=__name__, description=desc)
    parser.add_argument('pathtocheck', nargs='?', default='.',
                        help='A path to run code check.')
    parser.add_argument('--exclude', action='append', default=[],
                        dest='pathtoexclude',
                        help='A path to exclude code check.')
    parser.add_argument('--log', default='warning',
                        help='Set log level to warning, info or debug.')

    options = parser.parse_args(args)
    mainlogger.setLevel(loglevels.get(options.log.lower()))
    mainlogger.debug(options)

    builder = CodeCheckEnvBuilder(pathtocheck=options.pathtocheck,
                                  pathtoexclude=options.pathtoexclude,
                                  logger=mainlogger)

    temp = tempfile.TemporaryDirectory()
    mainlogger.debug('Using temporary directory: %s', temp.name)
    builder.create(temp.name)


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)-6s:%(funcName)-20s:%(message)s')
    mainlogger = logging.getLogger(__name__)

    rc = 1
    try:
        main()
        rc = 0
    except Exception as e:
        mainlogger.error(e)
    sys.exit(rc)
