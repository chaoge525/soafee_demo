#!/usr/bin/env python3
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

"""
This QA-check module ensures that all Python files within the project are
compliant with the code-style conventions in PEP8 as validated by the
pycodestyle utility.

The check runs recursively and independently on the file and directory paths
given by the 'paths' variable. Files within these paths will be validated only
if they are not excluded by any match to the regex strings given within
'exclude_patterns', and have a non-MIME file type (as output by the `file`
utility) that contains at least one substring in 'file_types', which should
identify Python files.

On failure, the check will log any files that failed validation along with the
reason for the error as given by pycodestyle.
"""

import logging
import os
import re
import shutil
import subprocess

import abstract_check


class PythonCheck(abstract_check.AbstractCheck):
    """ Class to run the pycodestyle utility on Python scripts, to validate
        compliance with some of the style conventions in PEP 8. """

    name = "python"

    @staticmethod
    def get_vars():
        list_vars = {}
        plain_vars = {}

        list_vars["paths"] = ("File paths to check, or directories to recurse."
                              " Relative paths will be considered relative to"
                              " the root directory.")

        list_vars["exclude_patterns"] = ("Patterns where if any is matched"
                                         " with the file/directory name, the"
                                         " check will not be applied to it or"
                                         " continue into its subpaths.")

        list_vars["file_types"] = ("String list where only files with non-MIME"
                                   " files-types (as output by the `file`"
                                   " utility) that contain at least one as a"
                                   " substring will be checked.")

        return list_vars, plain_vars

    def __init__(self, logger, *args, **kwargs):
        self.logger = logger
        self.__dict__.update(kwargs)

        checker_path = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(f"{checker_path}/../../")

        self.script = "pycodestyle"
        self.script_path = None

        self.num_files_checked = 0

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

        self.num_files_checked += 1

    def check_path(self, path, file_errors):
        """ Recursive function to descend into all non-excluded directories and
            find all non-excluded files, relative to the given path. Run the
            pycodestyle script on each Python file that we encounter. """

        import magic

        # Don't descend into any excluded directories or check any excluded
        # files
        if any([re.fullmatch(pat, path) for pat in self.exclude_patterns]):
            return

        if os.path.isfile(path):
            if any([ftype.lower() in magic.from_file(path, mime=False).lower()
                    for ftype in self.file_types]):
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

            for path in self.paths:

                if not os.path.isabs(path):
                    path = os.path.join(self.project_root, path)

                if not os.path.exists(path):
                    file_errors[path] = ["File or directory not found."]
                    continue

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
            self.logger.info(f"PASS ({self.num_files_checked} files checked)")
            return 0
