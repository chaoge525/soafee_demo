#!/usr/bin/env bash
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

if [ -z "${CE_TEST_GUEST_VM_NAME}" ]; then
    CE_TEST_GUEST_VM_NAME="%GUESTNAME%1"
fi

run_tests_on_guest_vm() {
    expect guest-vm-run-command.expect \
        "${CE_TEST_GUEST_VM_NAME}" \
        "ptest-runner container-engine-integration-tests" "120" \
        2>"${TEST_STDERR_FILE}"
}
