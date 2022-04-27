#!/usr/bin/env bats
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT
#
# Additional tests to be added to the user accounts test suite, if running on
# a virtualization image

load "${TEST_COMMON_DIR}/integration-tests-common-virtual-funcs.sh"
load "${TEST_DIR}/user-accounts-virtualization-funcs.sh"

@test 'run user accounts integration tests on the Guest VM from the Control VM' {

    # Use the systemd-detect-virt utility to determine if running on the Guest
    # VM (utility returns 0) or the Control VM (utility returns non-zero)
    _run systemd-detect-virt
    if [ "${status}" -eq 0 ]; then

        log "SKIP" "This test should only run on the Control VM"
        skip

    else

        subtest="Xendomains and Guest VM is initialized"
        _run xendomains_and_guest_vm_is_initialized "${UA_TEST_GUEST_VM_NAME}"
        if [ "${status}" -ne 0 ]; then
            log "FAIL" "${subtest}"
            return 1
        else
            log "PASS" "${subtest}"
        fi
        log "PASS"

        subtest="Run tests on Guest VM"
        _run run_tests_on_guest_vm
        if [ "${status}" -ne 0 ]; then
            log "FAIL" "${subtest}"
            return 1
        else
            log "PASS" "${subtest}"
        fi
        log "PASS"

    fi
}
