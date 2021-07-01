#!/usr/bin/env bash
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Arg1: Type of message (INFO, DEBUG, PASS, FAIL, SKIP)
# Arg2: Message to log
log() {
    if [ -z "${1}" ] ; then
        echo "ERROR:Incorrect arguments to log()"
        exit 1
    fi

    local log_msg
    local debug_msg
    local stderr

    log_msg="${1}:${BATS_TEST_NAME}"
    if [ -n "${2}" ]; then
        log_msg="${log_msg}:${2}"
    fi

    echo "${log_msg}" >> "${CE_TEST_LOG_FILE}"
    echo "${log_msg}"

    if [ "${1}" == "FAIL" ]; then
        # If the test failed, add additional debugging information

        stderr="$(cat "${CE_TEST_STDERR_FILE}")"

        debug_msg="DEBUG:${BATS_TEST_NAME}:${status:-}:${output:-}:${stderr}"

        echo "${debug_msg}" >> "${CE_TEST_LOG_FILE}"
        echo "${debug_msg}"
    fi
}
