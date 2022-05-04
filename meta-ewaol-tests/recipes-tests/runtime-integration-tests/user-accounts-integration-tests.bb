# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "User accounts integration tests."
DESCRIPTION = "Integration tests for user accounts settings validation. \
               Tests may be run standalone via \
               run-user-accounts-integration-tests, or via the ptest \
               framework using ptest-runner."

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

OVERRIDES:append = "${EWAOL_OVERRIDES}"

TEST_FILES = "file://user-accounts-integration-tests.bats \
              file://user-accounts-funcs.sh \
              "

TEST_FILES:append:ewaol-virtualization = " \
    file://user-accounts-append-virtualization.bats \
    file://user-accounts-virtualization-funcs.sh \
    "

TEST_FILES:append:ewaol-security = " \
    file://user-accounts-append-security.bats \
    file://user-accounts-security-funcs.sh \
    "

inherit runtime-integration-tests
require runtime-integration-tests.inc

export EWAOL_SECURITY_UMASK
ENVSUBST_VARS:append:ewaol-security = " \$EWAOL_SECURITY_UMASK"

do_install[vardeps] += "\
    EWAOL_SECURITY_UMASK \
    "
