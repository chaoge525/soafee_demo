#!/usr/bin/env python3
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

import os
import shutil
import subprocess
import tempfile

import abstract_check


class SpellCheck(abstract_check.AbstractCheck):
    """ Class to check the spelling of words in the provided directories or
        files within the 'paths_to_check' list, excluding paths (and subpaths)
        of those found in 'exclude_paths'.

        SpellCheck uses the 'pyspellchecker' Python package. The default
        package language "en" is extended with a custom dictionary found in the
        script path. """

    def __init__(self, logger, paths_to_check, exclude_paths=None):
        self.name = "spell"
        self.logger = logger
        self.script_path = None
        self.paths_to_check = paths_to_check.split(",")
        self.exclude_paths = exclude_paths.split(",") if exclude_paths is not \
            None else []

        self.checker_path = os.path.dirname(os.path.abspath(__file__))
        self.project_root = f"{self.checker_path}/../../"

        dict_name = "ewaol-dictionary"
        self.dict_path = os.path.join(self.checker_path, dict_name)
        if not os.path.isfile(self.dict_path):
            self.logger.error((f"Dictionary {dict_name} not found in"
                               f" {self.checker_path}"))
            self.dict_path = None

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
            self.logger.debug(("Could not decode file as UTF-8, skipping"
                               f" (path: {path})"))
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

    def check_path(self, path, file_errors, spellcheck):
        """ Recursive function to descend into all non-excluded directories and
            find all non-excluded files, relative to the given path. Run the
            spellchecker script on each file that we encounter. """

        # We don't descend into any excluded directories or check any
        # explicitly excluded files
        if path in self.exclude_paths:
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

            if self.dict_path:
                try:
                    spellcheck.word_frequency.load_text_file(self.dict_path)
                except UnicodeDecodeError:
                    self.logger.warning(("Could not UTF-8 decode the"
                                         " dictionary file at"
                                         f" {self.dict_path}."))

            for path in self.paths_to_check:
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
            self.logger.info("PASS")
            return 0
