# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "Virtualization integration tests."
DESCRIPTION = "Integration tests for the Xen hypervisor. \
               Tests may be run standalone via \
               run-virtualization-integration-tests, or via the ptest \
               framework using ptest-runner."

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

inherit features_check
REQUIRED_DISTRO_FEATURES += "ewaol-virtualization"

OVERRIDES:append = "${EWAOL_OVERRIDES}"

TEST_FILES = "file://virtualization-integration-tests.bats \
              file://virtualization-funcs.sh \
              "

TEST_FILES:append:ewaol-security = " \
    file://virtualization-append-security.bats \
    "

inherit runtime-integration-tests
require runtime-integration-tests.inc
