#!/usr/bin/env bats

# Run-time validation tests for OCI containers running on a EWAOL system.

load oci-runtime-funcs.sh
load integration-tests-common-funcs.sh

# Set configuration defaults

if [ -z "${OCI_TEST_IMAGE}" ]; then
    export OCI_TEST_IMAGE="docker.io/library/alpine"
fi

if [ -z "${OCI_TEST_LOG_DIR}" ]; then
    export OCI_TEST_LOG_DIR="$(pwd)/logs"
fi

if [ -z "${OCI_TEST_CLEAN_ENV}" ]; then
    export OCI_TEST_CLEAN_ENV=1
fi

# Ensure that the state of the OCI container environment is ready for the test
# suite
clean_test_environment() {

    # Remove any dangling containers based on the image
    run get_running_containers $(basename ${OCI_TEST_IMAGE})
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "Failed getting running containers of image \
'$(basename ${OCI_TEST_IMAGE})'" "${status}:${output}"
        log "INFO" "Unable to clean test environment"
    fi

    if [ -n "${output}" ]; then
        container_list=("${output}")
        for container_id in ${container_list}; do

            run container_stop ${container_id}
            if [ "${status}" -eq 0 ]; then
                log "INFO" "Cleaned test environment - stopped a running \
container '${container_id}' of image '$(basename ${OCI_TEST_IMAGE})'"
            else
                log "FAIL" "Unable to stop a running container \
'${container_id}' of image '$(basename ${OCI_TEST_IMAGE})'"
                log "INFO" "Unable to clean test environment"
            fi

        done
    fi

    # Remove the image if it exists
    run does_image_exist $(basename ${OCI_TEST_IMAGE})
    if [ "${status}" -eq 0 ]; then

        run image_remove $(basename ${OCI_TEST_IMAGE})
        if [ "${status}" -eq 0 ]; then
            log "INFO" "Cleaned test environment - removed image \
'$(basename ${OCI_TEST_IMAGE})'"
        else
            log "FAIL" "Unable to remove image '$(basename ${OCI_TEST_IMAGE})'"
            log "INFO" "Unable to clean test environment"
        fi

    fi
}

# Runs once before the first test
setup_file() {

    # Ensure log directory exists and clear any previous log if it exists
    mkdir -p "${OCI_TEST_LOG_DIR}"
    rm -f "${OCI_TEST_LOG_DIR}/oci-runtime-integration-tests.log"

    if [ "${OCI_TEST_CLEAN_ENV}" -eq 1 ]; then
        run clean_test_environment
    fi
}

# Runs after the final test
teardown_file() {

    if [ "${OCI_TEST_CLEAN_ENV}" -eq 1 ]; then
        run clean_test_environment
    fi
}

@test 'run OCI container' {

    # Run a container of the given image type pulled from an external image
    # hub, to execute an example workload simply consisting of an interactive
    # shell, then remove it afterwards.

    workload="/bin/sh"

    subtest="Run an OCI container with a persistent workload"
    run container_run_persistent ${OCI_TEST_IMAGE} ${workload}
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}" "${status}:${output}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    container_id="${output}"

    subtest="Check that the container is running"
    run check_container_state ${container_id}
    if [ "${status}" -ne 0 ] || [ "${output}" != "running" ]; then
        log "FAIL" "${subtest}" "${status}:${output}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Remove the running container"
    run container_remove ${container_id}
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}" "${status}:${output}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check the container status is no longer available"
    run check_container_state ${container_id}
    if [ "${status}" -eq 0 ] ; then
        log "FAIL" "${subtest}" "${status}:${output}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    log "PASS"
}
