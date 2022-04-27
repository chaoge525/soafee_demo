#!/usr/bin/env bash
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

if [ -z "${UA_TEST_GUEST_VM_NAME}" ]; then
    UA_TEST_GUEST_VM_NAME="${EWAOL_GUEST_VM_HOSTNAME}1"
fi

run_tests_on_guest_vm() {
    expect "${TEST_COMMON_DIR}/run-command.expect" \
        -hostname "${UA_TEST_GUEST_VM_NAME}" \
        -command "ptest-runner user-accounts-integration-tests" \
        -console "guest_vm" \
        2>"${TEST_STDERR_FILE}"
}
