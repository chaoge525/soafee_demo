#!/usr/bin/env bash
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Should only be called by virtualization-specific version of the environment
# clean-up
extra_cleanup() {

    # reset the password for '${TEST_SUDO_USER}' user
    sudo usermod -p '' "${TEST_SUDO_USER}"
    sudo passwd -e "${TEST_SUDO_USER}"

    # reset the password for '${NORMAL_USER}' user
    sudo usermod -p '' "${NORMAL_USER}"
    sudo passwd -e "${NORMAL_USER}"
}

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

EWAOL_UMASK="${EWAOL_SECURITY_UMASK}"

check_umask() {
    umask_val="$(umask 2>"${TEST_STDERR_FILE}")"
    if [ "${umask_val}" = "${EWAOL_UMASK}" ]; then
        return 0
    else
        echo "Wrong umask setting! current: '${umask_val}'," \
             "expected: '${EWAOL_UMASK}'."
        return 1
    fi
}
