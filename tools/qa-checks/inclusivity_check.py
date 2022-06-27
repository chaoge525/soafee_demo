#!/usr/bin/env python3
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

"""
This QA-check module checks for any potential non-inclusive terminology used in
the project. As non-inclusive terminology is highly nuanced and
context-dependent, the check simply highlights potential terminology to the
user so that consideration can be made if alternative language would be more
appropriate.

The check runs recursively and independently on the file and directory paths
given by the 'paths' variable. Files within these paths will be validated only
if they are not excluded by any match to the regex strings given within
'exclude_patterns'.

Where appropriate alternatives cannot be found, the usage can be tagged as an
acknowledged exception that will then be excluded from the check. To do this,
add "inclusivity-exception" before the usage, either on the same line or on the
immediately preceeding line. So that the tag is not considered as part of
the file's normal contents, it should be commented or otherwise excluded from
the file's expected usage.

Any non-excepted usages of potentially non-inclusive terminology will be
reported as an error from the QA-check, along with the file path and the line
numbers where the terminology was found.
"""

import bisect
import collections
import os
import re

import common
import abstract_check


class InclusivityCheck(abstract_check.AbstractCheck):

    name = "inclusivity"

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
                "non_inclusive_language_file",
                default="tools/qa-checks/non-inclusive-language.txt",
                message=("Path to a file containing non inclusive terminology"
                         " for the check to find.")
            )
        ]

    def __init__(self, logger, *args, **kwargs):
        self.logger = logger
        self.__dict__.update(kwargs)

        self.num_files_checked = 0
        self.non_inclusive_terms = list()

    def get_pip_dependencies(self):
        """ There are no additional Python package dependencies required. """
        return []

    def get_non_inclusive_language(self, non_inclusive_language_path):
        """ Parse the list of non-inclusive terms from file. """

        terms_list = list()

        with open(non_inclusive_language_path) as f:
            for line in f:
                terms_list.append(line.strip())

        return terms_list

    def run_inclusivitycheck(self, path, file_errors):
        """ Run the check, and return any non-inclusive terms as a dict mapping
            the filepath to a list of terms and their line numbers.
            """

        rel_path = os.path.relpath(path, self.project_root)

        errors_with_lines = collections.defaultdict(set)

        text = ""
        try:
            with open(path, 'r') as f:
                text = f.read()
        except UnicodeDecodeError as e:
            file_errors[rel_path] = [("Couldn't process file due to"
                                     " UnicodeDecodeError")]
            return

        # Get the positions of all the newlines in the text, so that we can
        # determine the line number of any matches
        newline_positions = [mat.start() for mat in re.finditer("\n", text)]

        for term in self.non_inclusive_terms:

            search = fr"\b{term}\b"
            if " " in term:
                multi_line_search = term.replace(" ", r"\b\s*\b")
                search = f"{term}|{multi_line_search}"

            for match in re.finditer(search, text, re.MULTILINE):

                # Find the nearest newline before the match
                line = bisect.bisect_left(newline_positions, match.start()) + 1

                # Check if it is tagged with an exception
                preceeding_text = text[newline_positions[line-3]:match.start()]
                if "inclusivity-exception" not in preceeding_text.lower():
                    errors_with_lines[term].add(str(line))

        errors = set()

        # Report any non-inclusive terminology with their line numbers
        for word, lines_set in errors_with_lines.items():
            error_msg = f"{','.join(lines_set)}:{word}"
            errors.add(error_msg)

        if errors_with_lines:
            file_errors[rel_path] = errors

        self.num_files_checked += 1

    def run(self):
        """ Run the inclusivity check.
            If no non-excepted non-inclusive terms are found, then report PASS.
            If non-inclusive terms are found and there is no in-file exception
            tag for it, then report FAIL and print the terms and their
            filepaths.
            """

        self.logger.debug(f"Running {self.name} check.")

        non_inclusive_language_path = self.non_inclusive_language_file.strip()
        if not os.path.isabs(self.non_inclusive_language_file):
            non_inclusive_language_path = os.path.join(
                self.project_root,
                self.non_inclusive_language_file.strip())

        if not os.path.isfile(non_inclusive_language_path):
            self.logger.error("FAIL")
            self.logger.error("Could not find the non-inclusive language file"
                              f" at {non_inclusive_language_path}.")
            return 1

        self.non_inclusive_terms = self.get_non_inclusive_language(
                                       non_inclusive_language_path)

        if len(self.non_inclusive_terms) == 0:
            self.logger.error("FAIL")
            self.logger.error("Failed to parse any non-inclusive terms,"
                              " so check cannot be performed.")
            return 1

        file_errors = dict()

        for path in self.paths:

            if not os.path.isabs(path):
                path = os.path.join(self.project_root, path)

            if not os.path.exists(path):
                file_errors[path] = ["File or directory not found."]
                continue

            self.logger.debug(f"Running {self.name} check on {path}")

            common.recursively_apply_check(
                path,
                self.run_inclusivitycheck,
                file_errors,
                self.exclude_patterns)

        if file_errors:
            self.logger.error("FAIL")
            self.logger.warning("Found potential non-inclusive terminology.")
            for filename, errors in file_errors.items():
                for error in errors:
                    self.logger.error(f"{filename}:{error}")
            return 1
        else:
            self.logger.info(f"PASS ({self.num_files_checked} files checked)")
            return 0
