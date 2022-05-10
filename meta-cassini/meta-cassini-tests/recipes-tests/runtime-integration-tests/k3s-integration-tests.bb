# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

SUMMARY = "K3s container orchestration integration tests."
DESCRIPTION = "Integration tests for the K3s container orchestration system. \
               Tests may be run standalone via \
               run-k3s-integration-tests, or via the ptest \
               framework using ptest-runner."

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

OVERRIDES:append = "${CASSINI_OVERRIDES}"

TEST_FILES = "file://k3s-integration-tests.bats \
              file://k3s-funcs.sh \
              file://k3s-test-deployment.yaml"

inherit runtime-integration-tests
require runtime-integration-tests.inc

K3S_TEST_DESC = "local deployment of K3s pods"
export K3S_TEST_DESC

ENVSUBST_VARS:append = " \$K3S_TEST_DESC"

do_install[vardeps] += "\
    K3S_TEST_DESC \
    "
