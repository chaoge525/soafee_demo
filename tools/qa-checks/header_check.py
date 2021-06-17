#!/usr/bin/python3
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Script to check headers for the meta-ewaol repository.
# This script should be in meta-ewaol/meta-ewaol-config/tools/.


import re
import os
import time
import subprocess

import abstract_check


class HeaderCheck(abstract_check.AbstractCheck):
    """ Class to check the headers in the provided directories or files within
        the 'paths_to_check' list, excluding paths (and subpaths) of those
        found in 'exclude_paths'. """

    def __init__(self, logger, paths_to_check, exclude_paths=None):
        self.logger = logger
        self.paths_to_check = paths_to_check.split(",")
        self.exclude_paths = exclude_paths.split(",") if exclude_paths is not \
            None else []

        self.checker_path = os.path.dirname(os.path.abspath(__file__))
        self.project_root = f"{self.checker_path}/../../"

        self.name = "header"
        self.arm_contributor = True

        self.IGNORED_FILE_EXTENSIONS = [
            '.gitignore',
            '.md',
            '.rst',
            '.pyc',
            '.png',
            '.cfg',
            '.css'
        ]

        # Supported comment types
        self.SUPPORTED_COMMENT_TYPES = '#|*|;|//'

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

    def get_pip_dependencies(self):
        """ There are no non-standard Python package dependencies required to
            run the executable """
        return []

    def check_header(self, path, file_errors):
        """ This function checks the header in a file. it returns any errors
            as a dict mapping the filepath to the error """

        # Checking file extension.
        if os.path.splitext(path)[1] in self.IGNORED_FILE_EXTENSIONS:
            return

        rel_path = os.path.relpath(path, self.project_root)

        # Read beggining of file and match to header.
        cmd = f"sed -n -e '/[{self.SUPPORTED_COMMENT_TYPES}].*Copyright/,\
            /[^{self.SUPPORTED_COMMENT_TYPES}]/p' {path}"

        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   shell=True,
                                   universal_newlines=True)

        try:
            head_line = process.stdout.read()
        except UnicodeDecodeError as e:
            file_errors[rel_path] = f"Couldn't process file : {e}"
            return

        match = re.compile(self.HEADER_MATCH, re.MULTILINE).search(head_line)

        correct = "Copyright (c) YYYY(-YYYY), <Contributor>. \n \n"\
                  "SPDX-License-Identifier: <License name>"

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
                        error = "copyright date does not match file's last" \
                                " modification"
                elif len(dates) == 1:
                    if dates[0] != last_change_year:
                        valid_dates = False
                        error = "copyright date does not match file's last" \
                                " modification"
                else:
                    valid_dates = False
                    error = "expected YYYY or YYYY-YYYY"
                if not valid_dates:
                    file_errors[rel_path] = f"incorrect date format : {error}"
            else:
                file_errors[rel_path] = "Copyright header found but format is"\
                                        f" incorrect, expected : \n{correct}"

        else:
            # Header didn't match the pattern.
            file_errors[rel_path] = f"missing header, expected : \n{correct}"

        return

    def check_path(self, path, file_errors):
        """ Recursive function to descend into all non-excluded directories and
            find all non-excluded files, relative to the given path. Run the
            spellchecker script on each file that we encounter. """

        rel_path = os.path.relpath(path, self.project_root)

        # We don't descend into any excluded directories or check any
        # explicitly excluded files
        if any(exclude in path for exclude in self.exclude_paths):
            return

        if os.path.isfile(path):
            self.check_header(path, file_errors)
        else:
            for next_path in os.listdir(path):
                self.check_path(os.path.join(path, next_path), file_errors)
        return file_errors

    def run(self):

        file_errors = dict()

        self.logger.debug(f"Running {self.name} check.")
        for path in self.paths_to_check:
            path = path.replace("/.", "")
            self.logger.debug(f"Running {self.name} check on {path}")
            self.check_path(path, file_errors)

        if file_errors:
            self.logger.error("FAIL")
            for filename, error in file_errors.items():
                self.logger.error(f"{filename}:{error}")
            return 1
        else:
            self.logger.info("PASS")
            return 0
