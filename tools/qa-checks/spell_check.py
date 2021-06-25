#!/usr/bin/env python3
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

"""
This QA-check module aims to highlight English spelling errors within the
project.

The check runs recursively and independently on the file and directory paths
given by the 'paths' variable. Files within these paths will be validated only
if they are not excluded by any match to the regex strings given within
'exclude_patterns'. As many project files are technical in nature with
non-standard English words, a file location containing a list of additional
valid words may optionally be passed to the QA-check as the 'dict_path'
variable.

Any files with misspelt words found by the QA-check will be logged along with
the word itself and all of the line numbers where the invalid word was found
within the file.
"""

import os
import re
import shutil
import subprocess
import tempfile

import abstract_check


class SpellCheck(abstract_check.AbstractCheck):
    """ Class to check the spelling of words in the project.

        SpellCheck uses the 'pyspellchecker' Python package. The default
        package language "en" is extended with a custom dictionary found in the
        script path. """

    name = "spell"

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

        plain_vars["dict_path"] = ("Path to a custom dictionary file that"
                                   " provides additional valid words when"
                                   " validating the spelling of files within"
                                   " the project.")

        return list_vars, plain_vars

    def __init__(self, logger, *args, **kwargs):
        self.logger = logger
        self.__dict__.update(kwargs)

        self.script_path = None

        checker_path = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(f"{checker_path}/../../")

        self.num_files_checked = 0

    def get_pip_dependencies(self):
        """ The pyspellchecker package is required to run the checker. """
        return ["pyspellchecker"]

    def run_spellcheck(self, path, file_errors, spellcheck):
        """ Run the spellchecker, and return any misspellings as a dict mapping
            the filepath to a list of its misspelt words. """

        rel_path = os.path.relpath(path, self.project_root)

        # Create a word frequency dictionary from the file
        import spellchecker
        file_word_freq = spellchecker.WordFrequency(case_sensitive=True)

        # There may be many non-text/non-utf8 files in the directory, which
        # will fail to be loaded as a collection of words, so skip these
        try:
            file_word_freq.load_text_file(path)
        except UnicodeDecodeError:
            file_errors[rel_path] = [("Couldn't process file due to"
                                     " UnicodeDecodeError")]
            return

        # Compare with the spellcheck object's dictionary
        errors = list(spellcheck.unknown(file_word_freq.words()))

        # Report each error with line numbers
        errors_with_lines = list()
        for word in errors:
            search = fr"\b{word}\b"
            cmd = ["grep", "-in", search, path]
            process = subprocess.run(cmd,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            stdout = process.stdout.decode().strip()

            line_numbers = ["unknown"]
            if process.returncode == 0 and stdout != "":
                line_numbers = [line.split(":")[0] for line in
                                stdout.split("\n")]

            error_msg = f"{','.join(line_numbers)}:{word}"
            errors_with_lines.append(error_msg)

        if errors_with_lines:
            file_errors[rel_path] = errors_with_lines

        self.num_files_checked += 1

    def check_path(self, path, file_errors, spellcheck):
        """ Recursive function to descend into all non-excluded directories and
            find all non-excluded files, relative to the given path. Run the
            spellchecker script on each file that we encounter. """

        # Don't descend into any excluded directories or check any excluded
        # files
        if any([re.fullmatch(pat, path) for pat in self.exclude_patterns]):
            return

        if os.path.isfile(path):
            self.run_spellcheck(path, file_errors, spellcheck)
        else:
            for next_path in os.listdir(path):
                self.check_path(os.path.join(path, next_path),
                                file_errors,
                                spellcheck)

        return file_errors

    def run(self):
        """ Run the spell check.
            If no misspellings are found, then report PASS.
            If any misspellings are found, then report FAIL and print the list
            of misspelt words and their filepaths. """

        self.logger.debug(f"Running {self.name} check.")

        file_errors = dict()

        # Check if we have the script
        try:
            import spellchecker

            spellcheck = spellchecker.SpellChecker(case_sensitive=True)

            dict_path = self.dict_path
            if not os.path.isabs(dict_path):
                dict_path = os.path.join(self.project_root, dict_path)

            if not os.path.isfile(dict_path):
                self.logger.warning(("Could not find the dictionary file at"
                                     f"{dict_path}."))
            else:
                try:
                    spellcheck.word_frequency.load_text_file(dict_path)
                except UnicodeDecodeError:
                    self.logger.warning(("Could not UTF-8 decode the"
                                         " dictionary file at"
                                         f" {dict_path}."))

            for path in self.paths:

                if not os.path.isabs(path):
                    path = os.path.join(self.project_root, path)

                if not os.path.exists(path):
                    file_errors[path] = ["File or directory not found."]
                    continue

                self.logger.debug(f"Running {self.name} check on {path}")
                self.check_path(path, file_errors, spellcheck)

        except ImportError:
            self.logger.error("FAIL")
            self.logger.error("Failed to load the Python spellchecker module.")
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
