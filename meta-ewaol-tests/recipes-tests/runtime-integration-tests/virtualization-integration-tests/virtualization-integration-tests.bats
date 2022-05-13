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
export TEST_RUN_FILE="${TEST_RUNTIME_DIR}/virtualization-integration-tests.pgid"

# Set test-suite specific configuration

if [ -z "${VIRT_TEST_GUEST_VM_NAME}" ]; then
    VIRT_TEST_GUEST_VM_NAME="${EWAOL_GUEST_VM_HOSTNAME}1"
fi

export TEST_CLEAN_ENV="${VIRT_TEST_CLEAN_ENV:=1}"
TEST_GUEST_VM_NAME="${VIRT_TEST_GUEST_VM_NAME}"

load "${TEST_COMMON_DIR}/integration-tests-common-funcs.sh"
load "${TEST_COMMON_DIR}/integration-tests-common-virtual-funcs.sh"
load "${TEST_DIR}/virtualization-funcs.sh"

# There are no base clean-up activities required
# Function is defined and called so that it can be conditionally overridden
clean_test_environment() {
  :
}

# Runs once before the first test
setup_file() {

    _run test_suite_setup clean_test_environment
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        return 1
    fi

    _run xendomains_and_guest_vm_is_initialized "${TEST_GUEST_VM_NAME}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        return 1
    fi
}

# Runs after the final test
teardown_file() {

    _run test_suite_teardown clean_test_environment
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        return 1
    fi
}

@test 'validate Guest VM is running' {

    subtest="Guest VM is running"
    _run guest_vm_is_running "${TEST_GUEST_VM_NAME}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Log-in to Guest VM and check external network is accessible"
    _run test_guest_vm_login_and_network_access "${TEST_GUEST_VM_NAME}"
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
    _run guest_vm_is_running "${TEST_GUEST_VM_NAME}"
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
    _run wait_for_success 300 10 guest_vm_is_not_running "${TEST_GUEST_VM_NAME}"
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
    _run wait_for_success 300 10 guest_vm_is_running "${TEST_GUEST_VM_NAME}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    log "PASS"
}
