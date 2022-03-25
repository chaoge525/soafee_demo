#!/usr/bin/env bats
#
# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Run-time validation tests for the Xen hypervisor implementing virtualization
# on an EWAOL system.

# Set generic configuration

if [ -z "${VIRT_TEST_LOG_DIR}" ]; then
    TEST_LOG_DIR="${HOME}/runtime-integration-tests-logs"
else
    TEST_LOG_DIR="${VIRT_TEST_LOG_DIR}"
fi

export TEST_LOG_FILE="${TEST_LOG_DIR}/virtualization-integration-tests.log"
export TEST_STDERR_FILE="${TEST_LOG_DIR}/virt-stderr.log"
export TEST_RUN_FILE="${TEST_LOG_DIR}/virt-test-pgid"

# Set test-suite specific configuration

if [ -z "${VIRT_TEST_GUEST_VM_NAME}" ]; then
    VIRT_TEST_GUEST_VM_NAME="%GUESTNAME%1"
fi

load integration-tests-common-funcs.sh
load integration-tests-common-virtual-funcs.sh
load virtualization-funcs.sh

# Runs once before the first test
setup_file() {
    _run test_suite_setup

    _run xendomains_and_guest_vm_is_initialized "${VIRT_TEST_GUEST_VM_NAME}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        exit 1
    fi

}

# Runs after the final test
teardown_file() {
    _run test_suite_teardown
}

@test 'validate Guest VM is running' {

    subtest="Guest VM is running"
    _run guest_vm_is_running "${VIRT_TEST_GUEST_VM_NAME}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Log-in to Guest VM and check external network is accessible"
    _run test_guest_vm_login_and_network_access "${VIRT_TEST_GUEST_VM_NAME}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    log "PASS"
}

@test 'validate Guest VM management' {

    subtest="Guest VM is running"
    _run guest_vm_is_running "${VIRT_TEST_GUEST_VM_NAME}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Shutdown Guest VM"
    _run shutdown_guest_vm
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Guest VM is not running after shutdown"
    _run wait_for_success 300 10 guest_vm_is_not_running "${VIRT_TEST_GUEST_VM_NAME}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Start Guest VM"
    _run start_guest_vm
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Guest VM is running after being restarted"
    _run wait_for_success 300 10 guest_vm_is_running "${VIRT_TEST_GUEST_VM_NAME}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    log "PASS"
}
