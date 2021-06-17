#!/usr/bin/env python3
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

import logging
import os
import shutil
import subprocess

import abstract_check


class PythonCheck(abstract_check.AbstractCheck):
    """ Class to run the pycodestyle utility on Python scripts, to validate
        compliance with some of the style conventions in PEP 8. """

    def __init__(self, logger, paths_to_check, exclude_paths=None):
        self.name = "python"
        self.logger = logger
        self.paths_to_check = paths_to_check.split(",")
        self.exclude_paths = exclude_paths.split(",") if exclude_paths is not \
            None else []

        checker_path = os.path.dirname(os.path.abspath(__file__))
        self.project_root = f"{checker_path}/../../"

        self.script = "pycodestyle"
        self.script_path = None

    def get_pip_dependencies(self):
        """ This class requires the 'magic' and 'pycodestyle' packages from pip
            to find files with Python code, and run the validation
            (respectively). """
        return ["python-magic", "pycodestyle"]

    def run_pycodestyle(self, path, file_errors):
        """ Run the tool on the filepath, and return any code errors as a dict
            mapping the filepath to the list of errors. """

        process = subprocess.run([self.script_path, path],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

        stdout = process.stdout.decode()
        stderr = process.stderr.decode()

        # As we report the error message with a relative path from the project
        # root, we remove the filename from the pycodestyle stdout
        filename = os.path.basename(path)

        if process.returncode != 0:
            errors = []
            for line in stdout.strip().split("\n"):
                if filename not in line:
                    # Not sure if this can happen, but if it can we should
                    # avoid an IndexError
                    errors.append(line)
                else:
                    errors.append(line.split(f"{filename}:")[1])

            if len(errors) == 0:
                # We failed but got no stdout, don't ignore this error!
                errors = [f"Unknown error (rc = {process.returncode})"]

            rel_path = os.path.relpath(path, self.project_root)
            file_errors[rel_path] = errors

    def check_path(self, path, file_errors):
        """ Recursive function to descend into all non-excluded directories and
            find all non-excluded files, relative to the given path. Run the
            pycodestyle script on each Python file that we encounter. """

        import magic

        # We don't descend into any excluded directories or check any
        # explicitly excluded files
        if path in self.exclude_paths:
            return

        if os.path.isfile(path):
            if magic.from_file(path, mime=True) == 'text/x-python':
                self.run_pycodestyle(path, file_errors)
        else:
            for next_path in os.listdir(path):
                self.check_path(os.path.join(path, next_path), file_errors)

        return file_errors

    def run(self):
        """ Run the python check.
            If no errors are found, then report PASS.
            If any errors are found, then report FAIL and print the list
            of code check errors and their filepaths. """

        self.logger.debug(f"Running {self.name} check.")

        # Check if we can run the tool
        if "VENV_BIN" in os.environ:
            self.script_path = shutil.which(self.script,
                                            path=os.environ["VENV_BIN"])
        else:
            self.script_path = shutil.which(self.script)

        if self.script_path is None:
            self.logger.error("FAIL")
            self.logger.error(f"Could not find {self.script} executable")
            return 1

        file_errors = dict()

        # Also check if we have the magic Python package
        try:

            import magic

            for path in self.paths_to_check:
                self.logger.debug(f"Running {self.name} check on {path}")
                self.check_path(path, file_errors)

        except ImportError:
            self.logger.error("FAIL")
            self.logger.error("Failed to load the Python 'magic' module.")
            return 1

        if file_errors:
            self.logger.error("FAIL")
            for filename, errors in file_errors.items():
                for error in errors:
                    self.logger.error(f"{filename}:{error}")
            return 1
        else:
            self.logger.info("PASS")
            return 0
