#!/usr/bin/env bash

# Arg1: Type of message (INFO, DEBUG, PASS, FAIL, SKIP)
# Arg2: Message to log
# Arg3: Debug message (will be output as separate DEBUG message)
log() {
    if [ -z "${1}" ] ; then
        echo "ERROR:Incorrect arguments to log()"
        exit 1
    fi

    local logfile="${OCI_TEST_LOG_DIR}/oci-runtime-integration-tests.log"

    local log_msg="${1}:${BATS_TEST_NAME}"
    if [ -n "${2}" ]; then
        log_msg="${log_msg}:${2}"
    fi

    echo "${log_msg}" >> "${logfile}"
    echo "${log_msg}"

    if [ "${3}" != "" ]; then
        local debug_msg="DEBUG:${BATS_TEST_NAME}:${@:3}"
        echo "${debug_msg}" >> "${logfile}"
        echo "${debug_msg}"
    fi
}
