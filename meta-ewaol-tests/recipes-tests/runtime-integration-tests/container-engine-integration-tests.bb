# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "Container engine integration tests."
DESCRIPTION = "Integration tests for the Docker container engine. \
               Tests may be run standalone via \
               run-container-engine-integration-tests, or via the ptest \
               framework using ptest-runner."

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

OVERRIDES:append = "${EWAOL_OVERRIDES}"

TEST_SUITE_NAME = "container-engine-integration-tests"
TEST_SUITE_PREFIX = "CE"

TEST_FILES = "file://container-engine-integration-tests.bats \
              file://container-engine-funcs.sh \
              file://integration-tests-common-funcs.sh"

TEST_FILES:append:ewaol-virtualization = " \
    file://integration-tests-common-virtual-funcs.sh \
    file://login-console-funcs.expect \
    file://run-command.expect \
    file://container-engine-additional-virtual-tests.bats \
    file://container-engine-virtualization-funcs.sh \
    "

SRC_URI = "${TEST_FILES} \
           file://run-test-suite \
           file://run-ptest"

RDEPENDS:${PN}:ewaol-virtualization += "expect"

require runtime-integration-tests.inc

do_install:append:ewaol-virtualization() {

    # Append the virtualization tests to the deployed test suite
    # Skip the first 2 lines to omit the shebang
    tail -n +3 \
        "${D}/${TEST_DIR}/container-engine-additional-virtual-tests.bats" \
        >> "${D}/${TEST_DIR}/container-engine-integration-tests.bats"

    sed -i "s#%GUESTNAME%#${EWAOL_GUEST_VM_HOSTNAME}#g" \
        "${D}/${TEST_DIR}/container-engine-virtualization-funcs.sh"

    rm "${D}/${TEST_DIR}/container-engine-additional-virtual-tests.bats"

}
