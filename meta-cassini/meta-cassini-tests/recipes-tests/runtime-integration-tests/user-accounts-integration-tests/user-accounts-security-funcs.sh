#!/usr/bin/env bash
#
# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

# run ${1} command as ${2} user
check_user_local_access() {
    expect "${TEST_COMMON_DIR}/run-command.expect" \
        -user "${1}" \
        -command "echo OK" \
        -console "local" \
        2>"${TEST_STDERR_FILE}"
}

# run ${1} command as ${2} user at ${3} remote via ssh
check_user_remote_access() {
    expect "${TEST_COMMON_DIR}/run-command.expect" \
        -hostname "${2}" \
        -user "${1}" \
        -command "echo OK" \
        -console "ssh" \
        2>"${TEST_STDERR_FILE}"
}

CASSINI_UMASK="${CASSINI_SECURITY_UMASK}"

check_umask() {
    umask_val="$(umask 2>"${TEST_STDERR_FILE}")"
    if [ "${umask_val}" = "${CASSINI_UMASK}" ]; then
        return 0
    else
        echo "Wrong umask setting! current: '${umask_val}'," \
             "expected: '${CASSINI_UMASK}'."
        return 1
    fi
}
