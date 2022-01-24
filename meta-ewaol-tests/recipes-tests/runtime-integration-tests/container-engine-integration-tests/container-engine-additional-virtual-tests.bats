#!/usr/bin/env bats
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT
#
# Additional tests to be added to the container engine test suite, if running on
# a virtualization image

load integration-tests-common-virtual-funcs.sh
load container-engine-virtualization-funcs.sh

@test 'run container engine integration tests on the VM from the Host' {

    # Use the systemd-detect-virt utility to determine if running on the VM
    # (utility returns 0) or the Host (utility returns non-zero)
    _run systemd-detect-virt
    if [ "${status}" -eq 0 ]; then

        log "SKIP" "This test should only run on the Host"
        skip

    else

        subtest="Xendomains and VM is initialized"
        _run xendomains_and_guest_is_initialized "${CE_TEST_GUEST_NAME}"
        if [ "${status}" -ne 0 ]; then
            log "FAIL" "${subtest}"
            return 1
        else
            log "PASS" "${subtest}"
        fi
        log "PASS"

        subtest="Run tests on VM"
        _run run_tests_on_vm
        if [ "${status}" -ne 0 ]; then
            log "FAIL" "${subtest}"
            return 1
        else
            log "PASS" "${subtest}"
        fi
        log "PASS"

    fi
}
