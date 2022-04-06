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

TEST_SUITE_NAME = "user-accounts-integration-tests"
TEST_SUITE_PREFIX = "USR_ACC"

TEST_FILES = "file://user-accounts-integration-tests.bats \
              file://user-accounts-funcs.sh \
              file://integration-tests-common-funcs.sh \
              "

TEST_FILES:append:ewaol-virtualization = " \
    file://user-accounts-additional-virtualization-tests.bats \
    file://user-accounts-virtualization-funcs.sh \
    file://integration-tests-common-virtual-funcs.sh \
    file://run-command.expect \
    file://login-console-funcs.expect \
    "

TEST_FILES:append:ewaol-security = " \
    file://user-accounts-additional-security-tests.bats \
    file://user-accounts-security-funcs.sh \
    file://run-command.expect \
    file://login-console-funcs.expect \
    "

SRC_URI = "${TEST_FILES} \
           file://run-test-suite \
           file://run-ptest"

require runtime-integration-tests.inc

RDEPENDS:${PN}:ewaol-virtualization += "expect"
RDEPENDS:${PN}:ewaol-security += "expect"

do_install:append:ewaol-security() {

    # Append the security tests to the deployed test suite
    # Skip the first 2 lines to omit the shebang
    tail -n +3 \
        "${D}/${TEST_DIR}/user-accounts-additional-security-tests.bats" \
        >> "${D}/${TEST_DIR}/user-accounts-integration-tests.bats"

    rm "${D}/${TEST_DIR}/user-accounts-additional-security-tests.bats"
}

do_install:append:ewaol-virtualization() {

    # Append the virtualization tests to the deployed test suite
    # Skip the first 2 lines to omit the shebang
    tail -n +3 \
        "${D}/${TEST_DIR}/user-accounts-additional-virtualization-tests.bats" \
        >> "${D}/${TEST_DIR}/user-accounts-integration-tests.bats"

    sed -i "s#%GUESTNAME%#${EWAOL_GUEST_VM_HOSTNAME}#g" \
        "${D}/${TEST_DIR}/user-accounts-virtualization-funcs.sh"

    rm "${D}/${TEST_DIR}/user-accounts-additional-virtualization-tests.bats"
}
