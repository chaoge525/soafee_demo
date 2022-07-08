#!/usr/bin/env bash
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# First argument is the Guest VM name
run_tests_on_guest_vm() {
    expect "${TEST_COMMON_DIR}/run-command.expect" \
        -hostname "${1}" \
        -command "ptest-runner container-engine-integration-tests" \
        -console "guest_vm" \
        2>"${TEST_STDERR_FILE}"
}
