#!/usr/bin/env python3
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

"""
This QA-check module ensures that documentation builds without errors.

The check runs 'doc-build.py' once using the default arguments. The defaults
arguments can be overwritten using documentation_dir (source of documentation),
output_dir (location of build output, use "" to create a temp dir), and
requirements (location of pip requirements.txt).

On failure, the output from 'doc-build.py' will be logged.
"""

import logging
import pathlib
import subprocess
import sys
import tempfile

import abstract_check
import common


class DocBuildCheck(abstract_check.AbstractCheck):
    """ Class to run the documentation build. """

    name = "doc_build"

    @staticmethod
    def get_vars():
        list_vars = {}
        plain_vars = {}

        plain_vars["documentation_dir"] = ("Path to directory containing"
                                           " documentation source. A relative"
                                           " path will be considered relative"
                                           " to project_root.")
        plain_vars["output_dir"] = ("Path to directory where generated"
                                    " documentation will be placed. A relative"
                                    " path will be considered relative to"
                                    " project_root. If the directory does not"
                                    " exist, it will be created. If set to ''"
                                    " then a temporary directory will be used"
                                    " and deleted after the build.")
        plain_vars["requirements"] = ("Path to pip requirements file for"
                                      " building the documentation. A relative"
                                      " path will be considered relative to"
                                      " project_root.")

        optional_vars = ["documentation_dir", "output_dir", "requirements"]

        return list_vars, plain_vars, optional_vars

    def __init__(self, logger, *args, **kwargs):
        self.logger = logger
        self.__dict__.update(kwargs)

        file_dir = pathlib.Path(__file__).parent
        self.script = (file_dir.parent / "build/doc-build.py").resolve()

    def get_pip_dependencies(self):
        """ The doc build should install its own dependencies. """
        return []

    def run(self):
        """ Run the check.
            If no errors are found, then report PASS.
            If any errors are found, then report FAIL and print the list of
            errors. """

        tmp_dir = None

        if not self.script.is_file():
            self.logger.error(f"Could not find {self.script}")
            return 1

        self.logger.debug(f"Running {self.name} check")

        command = [sys.executable, str(self.script),
                   "--project_root", self.project_root]

        project_root_path = pathlib.Path(self.project_root)

        if self.documentation_dir is not None:
            self.documentation_dir = str(
                (project_root_path / self.documentation_dir).resolve())
            command += ["--documentation_dir", f"{self.documentation_dir}"]

        if self.output_dir == "":
            # TemporaryDirectory deletes directory on object garbage collection
            tmp_dir = tempfile.TemporaryDirectory()
            self.output_dir = tmp_dir.name
            self.logger.debug("Building documentation into temporary"
                              " directory")
        if self.output_dir is not None:
            self.output_dir = str(
                (project_root_path / self.output_dir).resolve())
            command += ["--output_dir", f"{self.output_dir}"]

        if self.requirements is not None:
            self.requirements = str(
                (project_root_path / self.requirements).resolve())
            command += ["--requirements", f"{self.requirements}"]

        self.logger.debug(f"Running command '{' '.join(command)}'")
        process = subprocess.run(command,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)

        stdout = process.stdout.decode()

        errors = []
        if process.returncode != 0:
            for line in stdout.strip().split("\n"):
                if line.strip() != "":
                    errors.append(line)
            if len(errors) == 0:
                # We failed but got no stdout, don't ignore this error!
                errors = [f"Unknown error (rc = {process.returncode})"]

        if errors:
            self.logger.error("FAIL")
            for error in errors:
                self.logger.error(f"{error}")
            return 1
        else:
            self.logger.info(f"PASS (documentation built)")
            return 0
