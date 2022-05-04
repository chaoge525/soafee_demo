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

    _run guest_vm_reset_password
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        return 1
    fi
}
