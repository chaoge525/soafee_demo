#!/usr/bin/env python3
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

import email
import logging
import os
import shutil
import subprocess

import abstract_check


class CommitMsgCheck(abstract_check.AbstractCheck):
    """ Class to check the latest commit message of the git repositories given
        in the provided 'paths_to_check' list. The 'exclude_paths' list is
        unused, only present to conform to the standard check API. """

    def __init__(self, logger, paths_to_check, exclude_paths=None):
        self.name = "commit_msg"
        self.logger = logger
        self.paths_to_check = paths_to_check.split(",")
        self.exclude_paths = exclude_paths.split(",") if exclude_paths is not \
            None else []

        self.msg_title_length = 80
        self.msg_body_length = 80

        self.script = "git"
        self.script_path = None

    def get_pip_dependencies(self):
        """ For email validation, this checker requires the 'email_validator'
            package from pypi. """
        return ["email_validator"]

    def run(self):
        """ Run the git commit message check.
            If it is successful then report PASS.
            If it fails, then report FAIL and the list of errors. """

        self.logger.debug(f"Running {self.name} check.")

        import email_validator

        # Check if we can run git
        if self.script_path is None:
            self.script_path = shutil.which(self.script)

        if self.script_path is None:
            self.logger.error("FAIL")
            self.logger.error(f"Could not find {self.script}")
            return 1

        errors = []

        for path in self.paths_to_check:

            tests = {}
            tests["signed_off"] = ((f"{self.script} -C {path} log -1 | grep"
                                    " 'Signed-off-by:'"))

            tests["commit_msg"] = f"{self.script} -C {path} log -1 --pretty=%B"

            for test, cmd in tests.items():

                process = subprocess.Popen(cmd,
                                           stdout=subprocess.PIPE,
                                           shell=True)
                stdout, _ = process.communicate()
                stdout = stdout.decode().strip()

                if test == "signed_off":
                    # Check that all sign offs have a valid form:
                    # "Signed-off-by: Name <valid@email.dom>"

                    correct = "Signed-off-by: Name <valid@email.dom>"

                    if process.returncode != 0 or stdout == "":
                        errors.append(f"{test}: {correct} not found")

                    for idx, line in enumerate(stdout.split("\n")):
                        valid = True

                        try:
                            name, addr = email.utils.parseaddr(line)

                            # Check email address
                            email_validator.validate_email(addr)

                            # Check name is found
                            if name == "":
                                valid = False

                        except email_validator.EmailNotValidError:
                            valid = False

                        if not valid:
                            errors.append((f"{test}: '{line}' failed"
                                           " validation. Must be formed as"
                                           f" '{correct}'"))

                elif test == "commit_msg":

                    if process.returncode != 0 or stdout == "":
                        errors.append((f"{test}: no commit message found via"
                                       " '{cmd}'"))

                    # Iterate over the commit message and check its validity
                    for idx, line in enumerate(stdout.split("\n")):

                        if idx == 0:
                            if line == "":
                                errors.append(f"{test}: Title is empty")
                            elif len(line) > self.msg_title_length:
                                errors.append((f"{test}: Title is too long"
                                               f" ({len(line)} >"
                                               f" {self.msg_title_length}):"
                                               f" '{line}'"))

                        elif idx == 1 and line != "":
                            errors.append(f"{test}: Line {idx} is not empty")

                        elif idx > 1 and len(line) > self.msg_body_length:
                            errors.append((f"{test}: Line {idx} is too long"
                                           f" ({len(line)} >"
                                           f" {self.msg_body_length}):"
                                           f" '{line}'"))

        if errors:
            self.logger.error("FAIL")
            for error in errors:
                self.logger.error(error)
            return 1
        else:
            self.logger.info("PASS")
            return 0
