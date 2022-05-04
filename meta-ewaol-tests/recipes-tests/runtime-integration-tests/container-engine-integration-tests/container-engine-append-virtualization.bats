#!/usr/bin/env bats
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT
#
# Additional BATS code to be added to the container engine test suite, if
# running on a virtualization image

if [ -z "${CE_TEST_GUEST_VM_NAME}" ]; then
    CE_TEST_GUEST_VM_NAME="${EWAOL_GUEST_VM_HOSTNAME}1"
fi

TEST_GUEST_VM_NAME="${CE_TEST_GUEST_VM_NAME}"

load "${TEST_COMMON_DIR}/integration-tests-common-virtual-funcs.sh"
load "${TEST_DIR}/container-engine-virtualization-funcs.sh"

# Override the clean_test_environment call for the virtualization case to
# include an optional extra clean-up in addition to the normal base clean-up
clean_test_environment() {

    export BATS_TEST_NAME="clean_test_environment"

    _run base_cleanup
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        return 1
    fi

    _run extra_cleanup
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        return 1
    fi
}

@test 'run container engine integration tests on the Guest VM from the Control VM' {

    # Use the systemd-detect-virt utility to determine if running on the Guest
    # VM (utility returns 0) or the Control VM (utility returns non-zero)
    _run systemd-detect-virt
    if [ "${status}" -eq 0 ]; then

        log "SKIP" "This test should only run on the Control VM"
        skip

    else

        subtest="Xendomains and Guest VM is initialized"
        _run xendomains_and_guest_vm_is_initialized "${TEST_GUEST_VM_NAME}"
        if [ "${status}" -ne 0 ]; then
            log "FAIL" "${subtest}"
            return 1
        else
            log "PASS" "${subtest}"
        fi

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
