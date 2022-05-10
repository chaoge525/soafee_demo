#!/usr/bin/env bash
#
# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

# Arg1: Type of message (INFO, DEBUG, PASS, FAIL, SKIP)
# Arg2: Message to log
#
# If message type is FAIL, then an additional DEBUG message will be produced
# that contains the ${status} and ${output} variable (these are normally
# defined by BATS) as well as the contents of ${TEST_STDERR_FILE}
log() {
    if [ -z "${1}" ] ; then
        echo "ERROR:Incorrect arguments to log()"
        exit 1
    fi

    local log_msg
    local debug_msg
    local stderr
    local timestamp

    timestamp=$(date "+%Y-%m-%d %H:%M:%S")

    log_msg="${timestamp} ${1}:${BATS_TEST_NAME}"
    if [ -n "${2}" ]; then
        log_msg="${log_msg}:${*:2}"
    fi

    echo "${log_msg}" >> "${TEST_LOG_FILE}"
    echo "${log_msg}"

    if [ "${1}" == "FAIL" ]; then
        # If the test failed, add additional debugging information

        stderr="$(cat "${TEST_STDERR_FILE}")"

        debug_msg="${timestamp} DEBUG:${BATS_TEST_NAME}:${status:-}:${output:-}:${stderr}"

        echo "${debug_msg}" >> "${TEST_LOG_FILE}"
        echo "${debug_msg}"
        echo "DEBUG:Test log can be found at ${TEST_LOG_FILE}"
    fi
}

# Wrapper around BATS run to redirect FD3 and avoid hanging execution if
# subprocess fails or is long-running (e.g. a daemon process).
# See the following for details:
#   https://bats-core.readthedocs.io/en/stable/writing-tests.html
_run() {
    run "$@" 3>/dev/null
}

# This function handles the case where a previous test suite may fail in a
# hanging state, be user-interrupted and suspended, or orphaned during its
# execution, in order to avoid the possibility of running multiple interleaving
# test suites on the system which may interfere.
#
# To do this, when a test suite execution begins it writes its PGID to a
# run-file, and removes this run-file when it ends. Before any execution
# begins, the existance of a run-file is checked in order to determine if a
# previous execution is running. If it is running, a SIGINT to sent to the
# previous execution's PGID, before continuing.
#
# This function checks for the existance of the run-file, and sends the SIGINT
# if it is found.
#
# Arg1: Path to the run-file, if it exists
# Returns 1 if a previous execution was found but could not be terminated
# Returns 0 otherwise
check_running_test_suite() {

    # Provide a high-level test name so that the log messages are categorised
    # appropriately
    BATS_TEST_NAME="check_prior_execution"

    if pgid=$(cat "$1"); then
        # A run file currently exists, therefore a previous execution didn't
        # complete
        log "DEBUG" "Found a run-file from an existing test execution: ${pgid}"

        # Send an interrupt to the previously running process group
        log "DEBUG" "Sending an SIGINT to ${pgid}"
        kill -INT -- "-${pgid}"

        # Wait for the process to terminate

        # shellcheck disable=SC2034
        for i in {1..60..5}; do
            if [ -d "/proc/${pgid}" ]; then
                sleep 5
            else
                break
            fi
        done

        if [ -d "/proc/${pgid}" ]; then
            log "DEBUG" "Existing test execution with pgid ${pgid} could not"
                " be interrupted - please stop this running test before"
                " running another"

            unset BATS_TEST_NAME
            return 1
        else
            log "DEBUG" "Existing test suite execution was terminated"
        fi
    fi

    unset BATS_TEST_NAME
    return 0
}

# Create the run-file with the appropriate PGID
#
# Arg1: Path to the run-file
begin_test_suite() {
    # shellcheck disable=SC2009
    pgid="$(ps -o pid,pgid | grep -w "$$" | xargs | cut -d" " -f 2)"
    sudo sh -c "echo ${pgid} > ${1}"
}

# Remove the run-file if it contains the appropriate PGID
#
# Arg1: Path to the run-file
finish_test_suite() {

    # shellcheck disable=SC2009
    pgid=$(ps -o pid,pgid | grep -w "$$" | xargs | cut -d" " -f 2)
    file_pgid=$(cat "$1")

    if [ "${pgid}" -ne "${file_pgid}" ]; then
        log "DEBUG" "When finishing test-suite execution, the PGID ${pgid}"
            " did not match the PGID within the run-file ${file_pgid}"
    else
        sudo rm "${1}"
    fi

}

# The test_suite_setup and test_suite_teardown functions carry out the standard
# pre- and post-test-suite activities common across suites.
#
# The functions make use of expected environment variables:
#   TEST_LOG_FILE
#   TEST_STDERR_FILE
#   TEST_RUN_FILE
#   TEST_CLEAN_ENV
#
# If TEST_CLEAN_ENV is set to 1, the functions will call a test-suite-specific
# function, if one is provided as the first argument

test_suite_setup() {

    # Clear and rebuild the logs
    rm -f "${TEST_LOG_FILE}" "${TEST_STDERR_FILE}"
    mkdir -p "${TEST_LOG_DIR}"

    # Create volatile runtime directory.
    sudo mkdir -p "${TEST_RUNTIME_DIR}"

    _run check_running_test_suite "${TEST_RUN_FILE}"
    if [ "${status}" -ne 0 ]; then
        echo "${output}"
        return "${status}"
    fi

    _run begin_test_suite "${TEST_RUN_FILE}"
    if [ "${status}" -ne 0 ]; then
        echo "${output}"
        return "${status}"
    fi

    if [ "${TEST_CLEAN_ENV}" = "1" ] && [ -n "${1}" ]; then
        _run "${1}"
        if [ "${status}" -ne 0 ]; then
            echo "${output}"
            return "${status}"
        fi
    fi

}

test_suite_teardown() {

    status=0

    if [ "${TEST_CLEAN_ENV}" = "1" ] && [ -n "${1}" ]; then
        _run "${1}"
    fi

    # Always finish, even if the clean-up operations failed
    finish_test_suite "${TEST_RUN_FILE}"

    echo "${output}"
    return "${status}"
}

# Helper function to wait for some condition until a given timeout, probing the
# condition according to a given interval
# Accuracy of the timeout (in seconds) assumes a zero-cost condition evaluation
#
# Arg1: Timeout in seconds
# Arg2: Re-evaluation interval in seconds
# Arg3-*: Function with arguments that evaluates success (it returns 0) or
# continue to wait (it returns 1) or stop waiting and abort (it returns 2).
wait_for_success() {

    cmd="${*:3}"

    log "DEBUG" "Waiting for '${cmd}' to return success (timeout=${1}s)"

    num_iters=$(("(${1}/${2})"))
    if [ $((${1}%${2})) -gt 0 ]; then
        num_iters=$((num_iters + 1))
    fi

    i=1
    while ((i<num_iters)); do

        ${cmd}
        result=${?}

        if [ ${result} -eq 2 ]; then
            return 1
        elif [ ${result} -ne 0 ]; then
            sleep "${2}"
        else
            return 0
        fi
        i=$((i + 1))

    done

    ${cmd}
    result=${?}
    if [ ${result} -ne 0 ]; then
        log "DEBUG" "Timeout for '${cmd}' reached"
        return 1
    else
        return 0
    fi

}

# By default, the extra_* functions are not implemented
# Conditionally included files may define implementations by overriding them

extra_cleanup() {
  return 0
}

extra_setup() {
  return 0
}
