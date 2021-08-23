#!/usr/bin/env python3
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

"""
This QA-check module runs on one or more git repositories (given by the
provided 'paths' list variable), in order to validate that commit messages
adhere to the project's expected commit message format.

The check currently validates the message of the currently checked out HEAD
only.

Validation of commit message:
    * Title (first line) is not blank
    * Number of characters in the title is fewer than than the "title_length"
      variable
    * The second line is blank to separate message title and body
    * Number of characters in each line of the message body is fewer than the
      "body_length" variable
    * A sign-off is included in the message, with the following format:
      "Signed-off-by: Name <valid@email.dom>"
      The specified email must also pass validation as provided by the
      "email_validator" Python package

Any failure will be logged along with the particular validation that failed.
"""

import email
import logging
import os
import subprocess

import common
import abstract_check


class CommitMsgCheck(abstract_check.AbstractCheck):
    """ Class to check the latest commit message of the git repositories. """

    name = "commit_msg"

    @staticmethod
    def get_vars():
        list_vars = {}
        plain_vars = {}

        list_vars["paths"] = "File paths to target Git repositories."
        plain_vars["title_length"] = "Maximum number of characters in title."
        plain_vars["body_length"] = ("Maximum number of characters in each"
                                     " line of message body.")

        return list_vars, plain_vars

    def __init__(self, logger, *args, **kwargs):
        self.logger = logger
        self.__dict__.update(kwargs)

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

        script = "git"
        script_path = common.find_executable(self.logger, script)

        if script_path is None:
            self.logger.error("FAIL")
            self.logger.error(f"Could not find {script}")
            return 1

        errors = []

        for path in self.paths:

            if not os.path.isdir(path):
                errors.append(f"Directory ${path} not found.")
                continue

            if not os.path.isabs(path):
                path = os.path.abspath(path)

            tests = {}
            tests["signed_off"] = ((f"{script} -C {path} log -1 | grep"
                                    " 'Signed-off-by:'"))

            tests["commit_msg"] = f"{script} -C {path} log -1 --pretty=%B"

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
                            elif len(line) > int(self.title_length):
                                errors.append((f"{test}: Title is too long"
                                               f" ({len(line)} >"
                                               f" {self.title_length}):"
                                               f" '{line}'"))

                        elif idx == 1 and line != "":
                            errors.append(f"{test}: Line {idx} is not empty")

                        elif idx > 1 and len(line) > int(self.body_length):
                            errors.append((f"{test}: Line {idx} is too long"
                                           f" ({len(line)} >"
                                           f" {self.body_length}):"
                                           f" '{line}'"))

        if errors:
            self.logger.error("FAIL")
            for error in errors:
                self.logger.error(error)
            return 1
        else:
            self.logger.info("PASS")
            return 0
