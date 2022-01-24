#!/usr/bin/env bash
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

if [ -z "${CE_TEST_GUEST_NAME}" ]; then
    CE_TEST_GUEST_NAME="ewaol-vm"
fi

run_tests_on_vm() {
    expect guest-run-command.expect \
        "${CE_TEST_GUEST_NAME}" \
        "ptest-runner container-engine-integration-tests" \
        2>"${TEST_STDERR_FILE}"
}

