#!/usr/bin/env bats
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT
#
# Additional tests to be added to the user accounts test suite, if running on
# a virtualization image

if [ -z "${UA_TEST_GUEST_VM_BASENAME}" ]; then
    UA_TEST_GUEST_VM_BASENAME="${EWAOL_GUEST_VM_HOSTNAME}"
fi

export TEST_GUEST_VM_BASENAME="${UA_TEST_GUEST_VM_BASENAME}"

load "${TEST_COMMON_DIR}/integration-tests-common-virtual-funcs.sh"
load "${TEST_DIR}/user-accounts-virtualization-funcs.sh"

clean_test_environment() {

    export BATS_TEST_NAME="clean_test_environment"

    # There are no virtualization-only clean-up activities required
    # Call the extra_cleanup conditional implementation
    _run extra_cleanup
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        return 1
    fi

}

extra_setup() {

    load_guest_vm_vars
}


@test 'run user accounts integration tests on Guest VMs from the Control VM' {

    # Use the systemd-detect-virt utility to determine if running on the Guest
    # VM (utility returns 0) or the Control VM (utility returns non-zero)
    _run systemd-detect-virt
    if [ "${status}" -eq 0 ]; then

        log "SKIP" "This test should only run on the Control VM"
        skip

    else

        subtest="Xendomains is initialized"
        _run xendomains_is_initialized
        if [ "${status}" -ne 0 ]; then
            log "FAIL" "${subtest}"
            return 1
        else
            log "PASS" "${subtest}"
        fi

        guest_vm_idx=0
        for guest_vm in ${TEST_GUEST_VM_NAMES}; do
            guest_vm_idx=$((guest_vm_idx+1))

            vm_description="Guest VM ${guest_vm_idx}/${TEST_GUEST_VM_COUNT} (${guest_vm})"

            subtest="${vm_description} is initialized"
            _run guest_vm_is_initialized "${guest_vm}"
            if [ "${status}" -ne 0 ]; then
                log "FAIL" "${subtest}"
                return 1
            else
                log "PASS" "${subtest}"
            fi

            subtest="Run tests on ${vm_description}"
            _run run_tests_on_guest_vm "${guest_vm}"
            if [ "${status}" -ne 0 ]; then
                log "FAIL" "${subtest}"
                return 1
            else
                log "PASS" "${subtest}"
            fi
        done

        log "PASS"

    fi
}
