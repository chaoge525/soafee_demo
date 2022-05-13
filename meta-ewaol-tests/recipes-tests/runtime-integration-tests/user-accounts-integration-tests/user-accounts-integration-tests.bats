#!/usr/bin/env bats
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Run-time validation tests for the EWAOL system user accounts.

# Set generic configuration

if [ -z "${UA_TEST_LOG_DIR}" ]; then
    TEST_LOG_DIR="${HOME}/runtime-integration-tests-logs"
else
    TEST_LOG_DIR="${UA_TEST_LOG_DIR}"
fi

export TEST_LOG_FILE="${TEST_LOG_DIR}/user-accounts-integration-tests.log"
export TEST_STDERR_FILE="${TEST_LOG_DIR}/ua-stderr.log"
export TEST_RUN_FILE="${TEST_RUNTIME_DIR}/user-accounts-integration-tests.pgid"

export TEST_SUDO_USER="test"
export SUDO_USER="ewaol"
export NORMAL_USER="user"

export TEST_CLEAN_ENV="${UA_TEST_CLEAN_ENV:=1}"

load "${TEST_COMMON_DIR}/integration-tests-common-funcs.sh"
load "${TEST_DIR}/user-accounts-funcs.sh"

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

    # Call without run as we might export environment variables
    extra_setup
    status="${?}"
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

@test 'user accounts management tests' {

    subtest="Check '${NORMAL_USER}' user HOME directory mode"
    _run check_user_home_dir_mode "${NORMAL_USER}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check if '${SUDO_USER}' user does have sudo access"
    _run check_user_sudo_privileges "${SUDO_USER}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check if '${NORMAL_USER}' user does not have sudo access"
    _run check_user_sudo_privileges "${NORMAL_USER}"
    if [ "${status}" -ne 1 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    log "PASS"
}
