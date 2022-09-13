# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Config specifc to the ewaol-security distro feature, enabled using
# DISTRO_FEATURES

EWAOL_OVERRIDES:append = ":ewaol-security"

DISTRO_FEATURES:append = " cassini-security"

EWAOL_SECURITY_UMASK = "${@ d.getVar('CASSINI_SECURITY_UMASK')}"
