# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

SUMMARY = "Container engine integration tests."
DESCRIPTION = "Integration tests for the Docker container engine. \
               Tests may be run standalone via \
               run-container-engine-integration-tests, or via the ptest \
               framework using ptest-runner."

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

OVERRIDES:append = "${CASSINI_OVERRIDES}"

TEST_FILES = "file://container-engine-integration-tests.bats \
              file://container-engine-funcs.sh"

inherit runtime-integration-tests
require runtime-integration-tests.inc
