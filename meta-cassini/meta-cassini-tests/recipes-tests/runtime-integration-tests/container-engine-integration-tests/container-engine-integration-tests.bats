#!/usr/bin/env bats
#
# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

# Run-time validation tests for the container engine running on a CASSINI system.

# Set generic configuration

if [ -z "${CE_TEST_LOG_DIR}" ]; then
    TEST_LOG_DIR="${HOME}/runtime-integration-tests-logs"
else
    TEST_LOG_DIR="${CE_TEST_LOG_DIR}"
fi

export TEST_LOG_FILE="${TEST_LOG_DIR}/container-engine-integration-tests.log"
export TEST_STDERR_FILE="${TEST_LOG_DIR}/ce-stderr.log"
export TEST_RUN_FILE="${TEST_RUNTIME_DIR}/container-engine-integration-tests.pgid"

# Set test-suite specific configuration

if [ -z "${CE_TEST_IMAGE}" ]; then
    CE_TEST_IMAGE="docker.io/library/alpine"
fi

export TEST_CLEAN_ENV="${CE_TEST_CLEAN_ENV:=1}"

load "${TEST_COMMON_DIR}/integration-tests-common-funcs.sh"
load "${TEST_DIR}/container-engine-funcs.sh"

# Ensure that the state of the container environment is ready for the test
# suite
clean_test_environment() {

    # Use the BATS_TEST_NAME env var to categorise all logging messages relating
    # to the clean-up activities.
    export BATS_TEST_NAME="clean_test_environment"

    _run base_cleanup
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        return 1
    fi
}

# Runs once before the first test
setup_file() {

    _run test_suite_setup clean_test_environment
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
    _run check_container_is_running "${container_id}"
    if [ "${status}" -ne 0 ]; then
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

    subtest="Check the container is not running"
    _run check_container_is_not_running "${container_id}"
    if [ "${status}" -ne 0 ]; then
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
