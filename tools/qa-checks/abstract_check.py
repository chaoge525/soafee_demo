#!/usr/bin/env python3
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod


class AbstractCheck(ABC):
    """ Abstract class to enforce the necessary functions that check modules
        must implement. """

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def get_pip_dependencies(self):
        """ Return a list of Python pip package names required to run the
            check module. If none are required, an empty list may be returned.
            """
        pass

    @abstractmethod
    def run(self):
        """ Execute the logic of the check module and return 0 (success) or 1
            (failure) """
        pass
