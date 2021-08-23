#!/usr/bin/python3
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

"""
This QA-check module aims to validate the inclusion of copyright and license
headers within the relevant files of the project, according to an expected
format.

The check runs recursively and independently on the file and directory paths
given by the 'paths' variable, and ensures all non-excluded files have an
appropriate copyright and license header. Exclusions are specified in the regex
strings given within 'exclude_patterns', where any file that matches an exclude
pattern will not be checked (or recursed into).

License headers are validated to be of the format:
    Copyright (c) YYYY(-YYYY), <Contributor>
    SPDX-License-Identifier: <License name>

For each file with such a header, the final copyright year must match or be
later than the year of the last modification date of the file.

On failure, the check will log any files that failed validation along with the
reason for the error.
"""

import os
import re
import subprocess
import time

import common
import abstract_check


class HeaderCheck(abstract_check.AbstractCheck):
    """ Class to check the headers in the provided directories or files within
        the 'paths_to_check' list, excluding paths (and subpaths) of those
        found in 'exclude_paths'. """

    name = "header"

    @staticmethod
    def get_vars():
        list_vars = {}
        plain_vars = {}

        list_vars["paths"] = ("File paths to check, or directories to recurse."
                              " Relative paths will be considered relative to"
                              " the project's root directory.")
        list_vars["exclude_patterns"] = ("Patterns where if any is matched"
                                         " with the file/directory name, the"
                                         " check will not be applied to it or"
                                         " continue into its subpaths.")

        return list_vars, plain_vars

    def __init__(self, logger, *args, **kwargs):
        self.logger = logger
        self.__dict__.update(kwargs)

        checker_path = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(f"{checker_path}/../../")

        self.SUPPORTED_COMMENT_TYPES = '#|*|;|//'

        self.arm_contributor = True
        if self.arm_contributor:
            file_owner = "Arm Limited"
        else:
            file_owner = ""

        self.HEADER_MATCH = \
            '^([{0}]*) Copyright [(]c[)] (?P<years>[0-9]{{4}}(-[0-9]{{4}})?),'\
            f'.*{file_owner}.*$\n'\
            '(^([{0}]*)$\n)*'\
            '^([{0}]*) SPDX-License-Identifier:'\
            .format(self.SUPPORTED_COMMENT_TYPES)

        self.num_files_checked = 0

    def get_pip_dependencies(self):
        """ There are no non-standard Python package dependencies required to
            run the executable """
        return []

    def check_header(self, path, file_errors):
        """ This function checks the header in a file. it returns any errors
            as a dict mapping the filepath to the error """

        rel_path = os.path.relpath(path, self.project_root)

        # Read beggining of file and match to header.
        cmd = (f"sed -n -e '/[{self.SUPPORTED_COMMENT_TYPES}].*Copyright/,"
               f"/[^{self.SUPPORTED_COMMENT_TYPES}]/p' {path}")

        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   shell=True,
                                   universal_newlines=True)

        try:
            head_line = process.stdout.read()
        except UnicodeDecodeError as e:
            file_errors[rel_path] = ("Couldn't process file due to"
                                     " UnicodeDecodeError")
            return

        match = re.compile(self.HEADER_MATCH, re.MULTILINE).search(head_line)

        correct = ("Copyright (c) YYYY(-YYYY), <Contributor>\n"
                   "SPDX-License-Identifier: <License name>")

        if match:
            # Get the year of the last modification of the file.
            last_change = time.gmtime(os.path.getmtime(path))
            last_change_year = time.strftime("%Y", last_change)
            header_date = re.search(r"Copyright \(c\) (.+?),", head_line)

            if header_date:
                dates = header_date.group(1).split('-')
                # Check that the header date makes sense.
                valid_dates = True

                try:
                    int_dates = list(map(int, dates))
                except ValueError:
                    valid_dates = False

                if len(dates) == 2:
                    if int_dates[0] > int_dates[1]:
                        valid_dates = False
                        error = f"{int_dates[0]} > {int_dates[1]}"
                    elif int_dates[0] == int_dates[1]:
                        valid_dates = False
                        error = f"{int_dates[0]} = {int_dates[1]}"
                    elif dates[1] != last_change_year:
                        valid_dates = False
                        error = ("Copyright date does not match file's last"
                                 " modification")
                elif len(dates) == 1:
                    if dates[0] != last_change_year:
                        valid_dates = False
                        error = ("Copyright date does not match file's last"
                                 " modification")
                else:
                    valid_dates = False
                    error = "Expected: YYYY or YYYY-YYYY"
                if not valid_dates:
                    file_errors[rel_path] = f"Incorrect date format : {error}"
            else:
                file_errors[rel_path] = ("Copyright header found but format is"
                                         f" incorrect, expected: \n{correct}")

        else:
            # Header didn't match the pattern.
            file_errors[rel_path] = f"Missing header, expected: \n{correct}"

        self.num_files_checked += 1

    def run(self):

        self.logger.debug(f"Running {self.name} check.")

        file_errors = dict()
        for path in self.paths:

            if not os.path.isabs(path):
                path = os.path.join(self.project_root, path)

            if not os.path.exists(path):
                file_errors[path] = "File or directory not found."
                continue

            self.logger.debug(f"Running {self.name} check on {path}")
            common.recursively_apply_check(
                path,
                self.check_header,
                file_errors,
                self.exclude_patterns)

        if file_errors:
            self.logger.error("FAIL")
            for filename, error in file_errors.items():
                self.logger.error(f"{filename}:{error}")
            return 1
        else:
            self.logger.info(f"PASS ({self.num_files_checked} files checked)")
            return 0
