#!/usr/bin/env python3
#
# Copyright (c) 2021-2022, Arm Limited.
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


class CheckSetting():
    """ Class for storing information about a parameter for a qa-check module.
        """

    def __init__(self, name, is_list=False, is_pattern=False, required=False,
                 default=None, message=""):
        """ * name sets the name of the parameter in the config file and
              command line when combined with the check module name.
            * if is_list is true this parameter will be treated as a list and
              can be set as a comma separated value on command line or a list
              in the YAML config. If false then only one value is expected on
              the command line and the YAML config.
            * if is_pattern is true this parameter will be converted to a regex
              from a gitignore style pattern.
            * if required is true an error will be raised if the parameter is
              not set.
            * default sets the default value if the param is not required and
              not set.
            * message sets the help message to be printed by --help. """
        self.name = name
        self.is_list = is_list
        self.is_pattern = is_pattern
        self.required = required
        self.default = default
        self.message = message


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
        """ Return a list of CheckSetting objects that define the variables
            that are required to run the check module. """
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
