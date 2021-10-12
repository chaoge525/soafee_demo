# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "K3S container orchestration integration tests."
DESCRIPTION = "Integration tests for the K3S container orchestration system. \
               Tests may be run standalone via \
               run-k3s-integration-tests, or via the ptest \
               framework using ptest-runner."

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

TEST_SUITE_NAME = "k3s-integration-tests"
TEST_SUITE_PREFIX = "K3S"

TEST_FILES = "file://k3s-integration-tests.bats \
              file://k3s-funcs.sh \
              file://k3s-test-deployment.yaml \
              file://integration-tests-common-funcs.sh"

SRC_URI = "${TEST_FILES} \
           file://run-test-suite \
           file://run-ptest"

require runtime-integration-tests.inc
