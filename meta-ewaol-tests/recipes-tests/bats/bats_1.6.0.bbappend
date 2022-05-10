# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

OVERRIDES:append = "${EWAOL_OVERRIDES}"

FILESEXTRAPATHS:prepend:ewaol-tests := "${THISDIR}/files:"

# Add backport patch to bug-fix BATS v1.6.0
SRC_URI:append:ewaol-tests = " \
    file://0001-Fix-status-in-teardown-overriding-exit-code.patch \
    "
