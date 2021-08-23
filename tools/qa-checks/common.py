#!/usr/bin/env python3
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

"""
This file provides common functionality that may be used by multiple QA-checks.
"""

import logging
import os
import re
import shutil


def find_executable(logger, name):
    """ Function that returns the correct executable for a given name, based on
        whether or not the calling context is within a Python virtual
        environment.

        Returns None if the executable cannot be found. """

    if "VENV_BIN" in os.environ:

        script_path = shutil.which(name, path=os.environ["VENV_BIN"])
        if script_path is None:
            script_path = shutil.which(name)
            if script_path:
                logger.debug((f"Could not find the '{name}' executable in the"
                              " virtual environment, using the host system's"
                              " version."))

    else:
        script_path = shutil.which(name)

    return script_path


def recursively_apply_check(
        path,
        check_fn,
        file_errors,
        exclude_patterns=None,
        file_types=None):
    """ Recursive function to descend into all non-excluded directories and
        find all non-excluded files, relative to the given path. Run the
        check function on each file that we encounter that matches the
        optionally-defined file types. """

    if not os.path.isabs(path):
        file_errors[path] = [("Internal error: invalid path for the"
                              "recursive_run_check function (path must be"
                              " absolute).")]
        return

    try:
        if file_types:
            import magic

        # Don't descend into any excluded directories or check any excluded
        # files
        if exclude_patterns and any([re.fullmatch(pat, path)
                                    for pat in exclude_patterns]):
            return

        if os.path.isfile(path):
            if (not file_types or
                any([ft.lower() in magic.from_file(path, mime=False).lower()
                    for ft in file_types])):

                check_fn(path, file_errors)

        else:
            for sub_path in os.listdir(path):
                next_path = os.path.join(path, sub_path)

                recursively_apply_check(
                    next_path,
                    check_fn,
                    file_errors,
                    exclude_patterns,
                    file_types)

    except ImportError:
        file_errors[path] = ["Failed to load the Python 'magic' module."]
