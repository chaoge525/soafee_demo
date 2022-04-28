#!/usr/bin/env bash
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

run_tests_on_guest_vm() {
    expect "${TEST_COMMON_DIR}/run-command.expect" \
        -hostname "${TEST_GUEST_VM_NAME}" \
        -command "ptest-runner container-engine-integration-tests" \
        -timeout "120" \
        -console "guest_vm" \
        2>"${TEST_STDERR_FILE}"
}
