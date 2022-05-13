#!/usr/bin/env bash
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Should only be called by virtualization-specific version of the environment
# clean-up
extra_cleanup() {

    load_guest_vm_vars

    status=""
    output=""

    guest_vm_idx=0
    for guest_vm in ${TEST_GUEST_VM_NAMES}; do
        guest_vm_idx=$((guest_vm_idx+1))

        _run guest_vm_reset_password "${guest_vm}"
        if [ "${status}" -ne 0 ]; then
            echo "Failed to reset password for Guest VM ${guest_vm_idx}/${TEST_GUEST_VM_COUNT} (${guest_vm})"
            echo "${output}"
            return "${status}"
        fi
    done
}
