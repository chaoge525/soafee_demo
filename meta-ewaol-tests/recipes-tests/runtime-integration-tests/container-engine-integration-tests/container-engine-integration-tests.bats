#!/usr/bin/env bats
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Run-time validation tests for the container engine running on a EWAOL system.

# Set generic configuration

if [ -z "${CE_TEST_LOG_DIR}" ]; then
    TEST_LOG_DIR="$(pwd)/logs"
else
    TEST_LOG_DIR="${CE_TEST_LOG_DIR}"
fi

export TEST_LOG_FILE="${TEST_LOG_DIR}/container-engine-integration-tests.log"
export TEST_STDERR_FILE="${TEST_LOG_DIR}/ce-stderr.log"
export TEST_RUN_FILE="${TEST_LOG_DIR}/ce-test-pgid"

# Set test-suite specific configuration

if [ -z "${CE_TEST_IMAGE}" ]; then
    CE_TEST_IMAGE="docker.io/library/alpine"
fi

if [ -z "${CE_TEST_CLEAN_ENV}" ]; then
    CE_TEST_CLEAN_ENV=1
fi

load container-engine-funcs.sh
load integration-tests-common-funcs.sh

# Ensure that the state of the container environment is ready for the test
# suite
clean_test_environment() {

    # The logging function uses the current test name to categorise any log
    # messages specific to the test. Here, define this variable manually in
    # order to similarly categorise all messages relating to the clean-up
    # activities.
    export BATS_TEST_NAME="clean_test_environment"

    # Remove any dangling containers based on the image
    _run get_running_containers "$(basename ${CE_TEST_IMAGE})"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "Cleaning test environment - failed getting running \
containers of image '$(basename ${CE_TEST_IMAGE})'"
    fi

    if [ -n "${output}" ]; then
        for container_id in ${output}; do

            _run container_stop "${container_id}"
            if [ "${status}" -eq 0 ]; then
                log "INFO" "Stopped a running \
container '${container_id}' of image '$(basename ${CE_TEST_IMAGE})'"
            else
                log "FAIL" "Unable to stop a running container \
'${container_id}' of image '$(basename ${CE_TEST_IMAGE})'"
            fi

        done
    fi

    # Remove the image if it exists
    _run does_image_exist "$(basename ${CE_TEST_IMAGE})"
    if [ "${status}" -eq 0 ]; then

        _run image_remove "$(basename ${CE_TEST_IMAGE})"
        if [ "${status}" -eq 0 ]; then
            log "INFO" "Cleaned test environment - removed image \
'$(basename ${CE_TEST_IMAGE})'"
        else
            log "FAIL" "Unable to rm image '$(basename ${CE_TEST_IMAGE})'"
        fi

    fi
}

# Runs once before the first test
setup_file() {

    # Clear and rebuild the logs
    rm -rf "${TEST_LOG_FILE}" "${TEST_STDERR_FILE}"
    mkdir -p "${TEST_LOG_DIR}"

    _run check_running_test_suite "${TEST_RUN_FILE}"
    if [ "${status}" -ne 0 ]; then
        exit 1
    fi

    _run begin_test_suite "${TEST_RUN_FILE}"

    if [ "${CE_TEST_CLEAN_ENV}" = "1" ]; then
        _run clean_test_environment
    fi
}

# Runs after the final test
teardown_file() {

    if [ "${CE_TEST_CLEAN_ENV}" = "1" ]; then
        _run clean_test_environment
    fi

    _run finish_test_suite "${TEST_RUN_FILE}"
}

@test 'run container' {

    # Run a container of the given image type pulled from an external image
    # hub, to execute an example workload simply consisting of an interactive
    # shell, then remove it afterwards.

    engine_args="-itd"
    workload="/bin/sh"

    subtest="Run a container with a persistent workload"
    _run container_run "${engine_args}" "${CE_TEST_IMAGE}" "${workload}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    container_id="${output}"

    subtest="Check that the container is running"
    _run check_container_state "${container_id}"
    if [ "${status}" -ne 0 ] || [ "${output}" != "running" ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Remove the running container"
    _run container_remove "${container_id}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check the container status is no longer available"
    _run check_container_state "${container_id}"
    if [ "${status}" -eq 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    log "PASS"
}

@test 'container network connectivity' {

    # Run a non-detached container that executes a workload that requires
    # network access. If the command does not return an error, then the
    # container has network connectivity.

    engine_args="-it"
    workload="apk update"

    subtest="Update apk package lists within container"
    _run container_run "${engine_args}" "${CE_TEST_IMAGE}" "${workload}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    log "PASS"
}
