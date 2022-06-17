#!/usr/bin/env python3
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

"""
This QA-check module ensures that all YAML files within the project are
compliant with the YAML standard as validated by the yamllint utility.

The check runs recursively and independently on the file and directory paths
given by the 'paths' variable. Files within these paths will be validated only
if they are not excluded by any match to the regex strings given within
'exclude_patterns', and are included by any match to one of the regex strings
given within 'include_patterns'.

On failure, the check will log any files that failed validation along with the
reason for the error as given by yamllint.
"""

import logging
import os
import re
import subprocess

import abstract_check
import common


class YamlCheck(abstract_check.AbstractCheck):
    """ Class to run the yamllint utility on YAML files, to validate
        compliance with the YAML standard. """

    name = "yaml"

    @staticmethod
    def get_vars():
        return [
            abstract_check.CheckSetting(
                "paths",
                is_list=True,
                default=["ROOT"],
                message=("File paths to check, or directories to recurse."
                         " Relative paths will be considered relative to"
                         " the root directory.")
            ),
            abstract_check.CheckSetting(
                "include_patterns",
                is_list=True,
                is_pattern=True,
                default=["*.yml", "*.yaml"],
                message=("Patterns where if none are matched"
                         " with the file/directory name, the"
                         " check will not be applied to it.")
            ),
            abstract_check.CheckSetting(
                "exclude_patterns",
                is_list=True,
                is_pattern=True,
                default=["GITIGNORE_CONTENTS", "*.git"],
                message=("Patterns where if any is matched"
                         " with the file/directory name, the"
                         " check will not be applied to it or"
                         " continue into its subpaths.")
            ),
            abstract_check.CheckSetting(
                "yamllint_args",
                default="",
                message=("Custom arguments to pass through to"
                         " the yamllint command. On"
                         " run-checks.py command line, set"
                         " this parameter using '=' to avoid"
                         " interpretation as arguments for"
                         " run-checks.py.")
            )
        ]

    def __init__(self, logger, *args, **kwargs):
        self.logger = logger
        self.__dict__.update(kwargs)

        self.script = "yamllint"
        self.script_path = None

        self.num_files_checked = 0

    def get_pip_dependencies(self):
        """ This class requires the 'yamllint' package from pip to run the
            validation. """
        return ["yamllint==1.26.3"]

    def run_yamllint(self, path, file_errors):
        """ Run the tool on the filepath, and return any code errors as a dict
            mapping the filepath to the list of errors. """

        command = [self.script_path, path]
        if self.yamllint_args != "":
            command += self.yamllint_args.split(" ")

        process = subprocess.run(command,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

        stdout = process.stdout.decode()
        stderr = process.stderr.decode()

        if process.returncode != 0:
            search_keyword = f"{path}"
            errors = []
            for line in stdout.strip().split("\n"):
                if search_keyword not in line:
                    # Line does not contain file name but should be
                    # reported anyway
                    errors.append(line.strip())

            if len(errors) == 0:
                # We failed but got no stdout, don't ignore this error!
                errors = [f"Unknown error (rc = {process.returncode})"]

            rel_path = os.path.relpath(path, self.project_root)
            file_errors[rel_path] = errors

        self.num_files_checked += 1

    def run(self):
        """ Run the YAML check.
            If no errors are found, then report PASS.
            If any errors are found, then report FAIL and print the list
            of code check errors and their filepaths. """

        self.logger.debug(f"Running {self.name} check.")

        # Check if we can run the tool
        self.script_path = common.find_executable(self.logger, self.script)
        if self.script_path is None:
            self.logger.error("FAIL")
            self.logger.error(f"Could not find {self.script} executable")
            return 1

        file_errors = dict()
        for path in self.paths:

            if not os.path.isabs(path):
                path = os.path.join(self.project_root, path)

            if not os.path.exists(path):
                file_errors[path] = ["File or directory not found."]
                continue

            self.logger.debug(f"Running {self.name} check on {path} using"
                              f" {self.script} {self.yamllint_args}")

            common.recursively_apply_check(
                path,
                self.run_yamllint,
                file_errors,
                self.exclude_patterns,
                include_patterns=self.include_patterns)

        if file_errors:
            self.logger.error("FAIL")
            for filename, errors in file_errors.items():
                for error in errors:
                    self.logger.error(f"{filename}:{error}")
            return 1
        else:
            self.logger.info(f"PASS ({self.num_files_checked} files checked)")
            return 0
