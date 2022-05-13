#!/usr/bin/env bats
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT
#
# Additional BATS code to be appended to the virtualization test suite, if
# running on a security-hardened image

# Define clean-up operations
clean_test_environment() {

    export BATS_TEST_NAME="clean_test_environment"
    status=0
    output=""

    load_guest_vm_vars

    guest_vm_idx=0
    for guest_vm in ${TEST_GUEST_VM_NAMES}; do
        guest_vm_idx=$((guest_vm_idx+1))

        vm_description="Guest VM ${guest_vm_idx}/${TEST_GUEST_VM_COUNT} (${guest_vm})"

        _run guest_vm_reset_password "${guest_vm}"
        if [ "${status}" -ne 0 ]; then
            echo "Failed to reset password for ${vm_description}"
            echo "${output}"
            return "${status}"
        fi
    done
}
