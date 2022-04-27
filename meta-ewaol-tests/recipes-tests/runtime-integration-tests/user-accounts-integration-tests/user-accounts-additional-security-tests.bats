#!/usr/bin/env bats
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT
#
# Additional tests to be added to the user-accounts test suite, if running on
# a security-hardened image

export ROOT_USER="root"

load "${TEST_DIR}/user-accounts-security-funcs.sh"

@test 'user accounts management additional security tests' {

    subtest="Set password for '${NORMAL_USER}' account."
    _run check_user_local_access "${NORMAL_USER}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check if '${ROOT_USER}' account login is disabled."
    _run check_user_local_access "${ROOT_USER}"
    if [ "${status}" -ne 1 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check if SSH access for '${ROOT_USER}' account is disabled."
    _run check_user_remote_access "${ROOT_USER}" "localhost"
    if [ "${status}" -ne 1 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check umask setting for '${TEST_SUDO_USER}' account."
    _run check_umask
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    log "PASS"
}
