#!/usr/bin/env python3
#
# Copyright (c) 2021-2022, Arm Limited.
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

import collections
import itertools
import os
import re
import subprocess
import tempfile

import common
import abstract_check


class SpellCheck(abstract_check.AbstractCheck):
    """ Class to check the spelling of words in the project.

        SpellCheck uses the 'pyspellchecker' Python package.

        As the repository contains many non-standard technical words, extend
        the default built-in dictionary "en" with a custom dictionary of valid
        words (provided by the 'dict_path' parameter). """

    name = "spell"

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
                message=("Path to a custom dictionary file that"
                         " provides additional valid words when"
                         " validating the spelling of files within"
                         " the project.")
            ),
            abstract_check.CheckSetting(
                "dict_path",
                message=("Path to a custom dictionary file that"
                         " provides additional valid words when"
                         " validating the spelling of files within"
                         " the project.")
            )
        ]

    def __init__(self, logger, *args, **kwargs):
        self.logger = logger
        self.__dict__.update(kwargs)

        self.num_files_checked = 0

    def get_pip_dependencies(self):
        """ The pyspellchecker package is required to run the checker. """
        return ["pyspellchecker"]

    def run_spellcheck(self, path, file_errors):
        """ Run the spellchecker, and return any misspellings as a dict mapping
            the filepath to a list of misspelt words and their line numbers.
            """

        rel_path = os.path.relpath(path, self.project_root)

        import spellchecker
        word_freq = spellchecker.WordFrequency()
        hash_regex = re.compile(r"\b([a-f\d]{40}|[A-F\d]{40})\b")

        errors = set()

        # Pass each line of the file through the spell checker
        # For any detected errors, check if it is excluded from the check
        # (for example, we don't check the contents of documentation code
        # blocks)

        try:
            with open(path, 'r', encoding="utf-8") as f:
                text = f.read()  # for matching
                f.seek(0)  # to iterate over lines later

                exclusions = list()

                # Currently the project has ReStructuredText formatted links
                # within the Markdown readme
                if path.endswith(".rst") or path.endswith(".md"):
                    # Exclude the following:
                    code = r"(\.\. code-block::.*$)((\n +.*|\s)+)"
                    link_defs = r"(\.\.\s+_.*$)((\n +.*|\s)+)"
                    links_in = r"`([^\s]*?)`_"
                    links_ex = r":ref:`([^\s]*?)`"

                    matches_code = re.finditer(code, text, re.M)
                    matches_linkdefs = re.finditer(link_defs, text, re.M)
                    matches_links_in = re.finditer(links_in, text, re.M)
                    matches_links_ex = re.finditer(links_ex, text, re.M)

                    matches = itertools.chain(matches_code,
                                              matches_linkdefs,
                                              matches_links_in,
                                              matches_links_ex)

                    for _, match in enumerate(matches):
                        for _, group_text in enumerate(match.groups()):
                            if not group_text.strip():
                                continue
                            exclusions.append(group_text.strip().lower())

                for line in f:
                    if line.strip() == "":
                        continue

                    # Test the line for spelling mistakes
                    word_freq.load_text(line.strip())
                    words = list(self.spellcheck.unknown(word_freq.words()))

                    for word in words:

                        if any([word in ex for ex in exclusions]):
                            continue

                        if hash_regex.match(word):
                            continue

                        errors.add(word)

        except UnicodeDecodeError as e:
            file_errors[rel_path] = [("Couldn't process file due to"
                                     " UnicodeDecodeError")]
            return

        # Map words to a set of lines
        errors_with_lines = collections.defaultdict(set)

        # Get the full word from the token that was parsed from the line, if
        # necessary. This is to make the custom dictionary more understandable.
        # For example, "killall" should not be a valid word, unless it is part
        # of a reference to the "k3s-killall" script. So the latter is the only
        # word that should be considered valid.
        # In addition, get the line number(s) for the word
        for word in errors:

            inc_chars = r"][[:alnum:]\+\-_|\.\'"
            search = fr"[{inc_chars}]*{word}[{inc_chars}]*"
            cmd = ["grep", "-inoP", search, path]
            process = subprocess.run(cmd,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            stdout = process.stdout.decode().strip()

            if process.returncode == 0 and stdout != "":

                full_words = [(line.split(":")[0], line.split(":")[1].strip())
                              for line in stdout.split("\n")]

                full_errors = list()
                for line_number, full_word in full_words:

                    # Remove any trailing special characters
                    full_word = full_word.strip().strip("_+-|][.'").lower()

                    if any([full_word in ex for ex in exclusions]):
                        continue

                    # Check if the proper word is an actual spelling mistake /
                    # is contained in the custom dictionary
                    if (full_word in errors_with_lines or
                            self.spellcheck.unknown([full_word])):

                        # Merge the line numbers where it is found
                        errors_with_lines[full_word].add(line_number)

            else:
                # Couldn't find the string (this shouldn't happen)
                # Don't discard the error
                errors_with_lines[word].add("unknown")

        errors = list()

        # Report all full word errors and their line numbers
        for word, lines_set in errors_with_lines.items():
            error_msg = f"{','.join(lines_set)}:{word}"
            errors.append(error_msg)

        if errors_with_lines:
            file_errors[rel_path] = errors

        self.num_files_checked += 1

    def run(self):
        """ Run the spell check.
            If no misspellings are found, then report PASS.
            If any misspellings are found, then report FAIL and print the list
            of misspelt words and their filepaths. """

        self.logger.debug(f"Running {self.name} check.")

        file_errors = dict()

        try:
            import spellchecker

            self.spellcheck = spellchecker.SpellChecker()

            dict_path = self.dict_path
            if dict_path is not None:
                if not os.path.isabs(dict_path):
                    dict_path = os.path.join(self.project_root, dict_path)

                if not os.path.isfile(dict_path):
                    self.logger.warning(("Could not find the dictionary file"
                                         f" at {dict_path}."))
                else:
                    try:

                        def simple_split(text):
                            return text.split()

                        self.spellcheck.word_frequency.load_text_file(
                            dict_path,
                            tokenizer=simple_split)

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
                common.recursively_apply_check(
                    path,
                    self.run_spellcheck,
                    file_errors,
                    self.exclude_patterns)

        except ImportError as e:
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
