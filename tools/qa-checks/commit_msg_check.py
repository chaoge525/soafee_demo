#!/usr/bin/env python3
#
# Copyright (c) 2021-2022, Arm Limited.
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
import re
import subprocess
import urllib

import common
import abstract_check


class CommitMsgCheck(abstract_check.AbstractCheck):
    """ Class to check the latest commit message of the git repositories. """

    name = "commit_msg"

    @staticmethod
    def get_vars():
        list_vars = {}
        plain_vars = {}
        optional_var_names = []

        list_vars["paths"] = "File paths to target Git repositories."
        plain_vars["title_length"] = "Maximum number of characters in title."
        plain_vars["body_length"] = ("Maximum number of characters in each"
                                     " line of message body.")
        plain_vars["commits"] = ("Defines the commit messages to check. Can be"
                                 " defined in one of two formats: '-N' to"
                                 " check the latest N commit messages, or"
                                 " 'commit1(,commit2,...)' as a string list of"
                                 " commits to check. The commits must be valid"
                                 " when passed to the 'git show' command, for"
                                 " example a commit SHA or a relative commit"
                                 " like HEAD~2.")

        return list_vars, plain_vars, optional_var_names

    def __init__(self, logger, *args, **kwargs):
        self.logger = logger
        self.__dict__.update(kwargs)

    def get_pip_dependencies(self):
        """ For email validation, this checker requires the 'email_validator'
            package from pypi. """
        return ["email_validator"]

    def parse_commits_str(self, commits_str):
        """ Convert the commits that the user requested into a list of commits
            that may be checked one at a time by being passed to the 'git show'
            command.
            Acceptable formats are:
              -N
              SHA1(,SHA2,...)
              HEAD~1(,HEAD~2,...)
        """

        try:

            commits = []
            if commits_str.startswith("-"):
                count = int(commits_str.split("-")[1])

                for i in range(count):
                    commits.append(f"HEAD~{i}")

            else:
                commits = commits_str.split(",")

                # Remove any blank commits
                commits = [commit for commit in commits if commit]

        except Exception as e:
            self.logger.error(("Invalid format for the desired commits to"
                               f" check: '{commits_str}'. Please see paramater"
                               " usage. Aborting the check."))
            self.logger.error(f"Exception was: {type(e)} {e}")
            exit(1)

        return commits

    def run(self):
        """ Run the git commit message check.
            If it is successful then report PASS.
            If it fails, then report FAIL and the list of errors. """

        self.logger.debug(f"Running {self.name} check.")

        try:
            import email_validator
        except ImportError:
            self.logger.error("FAIL")
            self.logger.error((f"Failed to import the Python email_validator"
                               " module."))
            return 1

        script = "git"
        script_path = common.find_executable(self.logger, script)

        if script_path is None:
            self.logger.error("FAIL")
            self.logger.error(f"Could not find {script}")
            return 1

        commits = self.parse_commits_str(self.commits)

        errors = []

        for path in self.paths:

            if not os.path.isdir(path):
                errors.append(f"Directory ${path} not found.")
                continue

            if not os.path.isabs(path):
                path = os.path.abspath(path)

            for commit in commits:

                # If printing an error message, attach this to identify which
                # commit had the error
                target = f"{os.path.basename(path)}:{commit}"

                cmd = f"{script} -C {path} show {commit} -q --format=%B"

                process = subprocess.Popen(cmd,
                                           stdout=subprocess.PIPE,
                                           shell=True)
                stdout, _ = process.communicate()
                stdout = stdout.decode().strip()

                if process.returncode != 0 or stdout == "":
                    errors.append(("Failed to get a commit message using:"
                                   f" {cmd}."))
                    continue

                # Check that all sign offs have a valid format

                correct_sign_off = "Signed-off-by: Name <valid@email.dom>"
                signed_off = "Signed-off-by:"
                matches = re.findall(fr"(^.*?{signed_off}.*?$)",
                                     stdout,
                                     re.MULTILINE)

                if not matches:
                    errors.append((f"{target}:Could not find a '{signed_off}'"
                                   f" line in the commit message."))
                    continue

                for line in matches:

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
                        errors.append((f"{target}:Failed sign-off validation:"
                                       " '{line}'. Must be formed as"
                                       f" '{correct_sign_off}'"))

                # Iterate over the full message and validate the other aspects

                for idx, line in enumerate(stdout.split("\n")):

                    if idx == 0:
                        if line == "":
                            errors.append(f"{target}:Message title is empty")
                        elif len(line) > int(self.title_length):
                            errors.append((f"{target}:Title is too long"
                                           f" ({len(line)} >"
                                           f" {self.title_length}):"
                                           f" '{line}'"))

                    elif idx == 1 and line != "":
                        errors.append((f"{target}:The message title must be"
                                       " followed by a blank line"))

                    elif idx > 1 and len(line) > int(self.body_length):

                        # Ignore lines that are URLs, which are allowed to
                        # break the maximum character length
                        try:
                            if urllib.parse.urlparse(line.strip()):
                                continue
                        except ValueError:
                            # Not a value URL
                            pass

                        errors.append((f"{target}:Line {idx} is too long"
                                       f" ({len(line)} > {self.body_length}):"
                                       f"'{line}'"))

        if errors:
            self.logger.error("FAIL")
            for error in errors:
                self.logger.error(error)
            return 1
        else:
            self.logger.info("PASS")
            return 0
