#!/usr/bin/env bash
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Ensure that the state of the container environment is ready for the test
# suite
clean_test_environment() {

    # Use the BATS_TEST_NAME env var to categorise all logging messages relating
    # to the clean-up activities.
    export BATS_TEST_NAME="clean_test_environment"

    # reset the password for '${TEST_SUDO_USER}' user
    sudo usermod -p '' "${TEST_SUDO_USER}"
    sudo passwd -e "${TEST_SUDO_USER}"

    # reset the password for '${NORMAL_USER}' user
    sudo usermod -p '' "${NORMAL_USER}"
    sudo passwd -e "${NORMAL_USER}"
}

# Runs once before the first test
setup_file() {
    _run test_suite_setup clean_test_environment
}

# Runs after the final test
teardown_file() {
    _run test_suite_teardown clean_test_environment
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
