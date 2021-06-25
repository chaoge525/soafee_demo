#!/usr/bin/env python3
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

"""
This file describes the Python class-interface that check modules must
implement in order to be compatible with the run-checks.py wrapper script.
The interface is enforced through inheritance, where checks must form a
subclass of AbstractCheck, and thus must implement concrete versions of its
abstract functions or fail with a Python TypeError.

Attempting to plug-in a check module that does not inherit this class will
result in a validation error.
"""

from abc import ABC, abstractmethod


class AbstractCheck(ABC):
    """ Abstract class to enforce the necessary functions that check modules
        must implement. """

    @abstractmethod
    def __init__(self, logger, *args, **kwargs):
        """ In addition to a logging object, the check constructor will receive
            keyword arguments that provide all of its required parameters as
            specified by get_vars().
            The resulting object's parameters may therefore be populated by
            updating the object's internal dictionary via:
                self.__dict__.update(kwargs)
            """
        pass

    @abstractmethod
    def get_vars(self):
        """ Return two dicts that define the variables that are required to run
            the check module, where each dict maps a variable name to a
            description of the variable for usage instructions.

            The first dict must correspond to list variables, each populated by
            the user via either a YAML list in a YAML configuration file, or
            via a comma-separated list within the command-line arguments.
            The second dict must correspond to plain variables, each mapping to
            a single value. """
        pass

    @abstractmethod
    def get_pip_dependencies(self):
        """ Return a list of strings corresponding to the Python package names
            required to execute the check module. The caller may then ensure
            the check is run from an environment where these dependencies are
            fulfilled in order to run the check successfully. """
        pass

    @abstractmethod
    def run(self):
        """ Execute the logic of the check module and return 0 (success) or 1
            (failure). """
        pass
