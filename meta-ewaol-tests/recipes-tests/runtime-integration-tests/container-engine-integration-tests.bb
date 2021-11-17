# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "Container engine integration tests."
DESCRIPTION = "Integration tests for the Docker container engine. \
               Tests may be run standalone via \
               run-container-engine-integration-tests, or via the ptest \
               framework using ptest-runner."

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

TEST_SUITE_NAME = "container-engine-integration-tests"
TEST_SUITE_PREFIX = "CE"

TEST_FILES = "file://container-engine-integration-tests.bats \
              file://container-engine-funcs.sh \
              file://integration-tests-common-funcs.sh"

SRC_URI = "${TEST_FILES} \
           file://run-test-suite \
           file://run-ptest"

require runtime-integration-tests.inc
