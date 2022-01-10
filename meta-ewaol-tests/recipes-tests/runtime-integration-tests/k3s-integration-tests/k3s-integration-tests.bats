#!/usr/bin/env bats
#
# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Run-time validation tests for the K3S container orchestration platform.

# Set generic configuration

if [ -z "${K3S_TEST_LOG_DIR}" ]; then
    TEST_LOG_DIR="$(pwd)/logs"
else
    TEST_LOG_DIR="${K3S_TEST_LOG_DIR}"
fi

export TEST_LOG_FILE="${TEST_LOG_DIR}/k3s-integration-tests.log"
export TEST_STDERR_FILE="${TEST_LOG_DIR}/k3s-stderr.log"
export TEST_RUN_FILE="${TEST_LOG_DIR}/k3s-test-pgid"

# Set test-suite specific configuration

export TEST_CLEAN_ENV="${K3S_TEST_CLEAN_ENV:=1}"

load integration-tests-common-funcs.sh
load k3s-funcs.sh

# Ensure that the state of the orchestration service is reset to its
# out-of-the-box state, not polluted by a previous test suite execution
clean_test_environment() {

    # Use the BATS_TEST_NAME env var to categorise all logging messages relating
    # to the clean-up activities.
    export BATS_TEST_NAME="clean_test_environment"

    _run wait_for_k3s_to_be_running
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        exit 1
    fi

    _run remove_k3s_test_service
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        exit 1
    fi

    _run remove_k3s_test_deployment
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        exit 1
    fi

}

# Runs once before the first test
setup_file() {
    _run test_suite_setup clean_test_environment

    # If the environment clean option is disabled, we should still wait for k3s
    # to be fully initialized (e.g. after booting) before running the tests
    _run wait_for_k3s_to_be_running
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        exit 1
    fi
}

# Runs after the final test
teardown_file() {
    _run test_suite_teardown clean_test_environment
}

@test 'K3S orchestration of containerized web service' {

    subtest="Deploy workload"
    _run apply_workload "k3s-test-deployment.yaml"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check deployment is ready with pod replicas"
    _run wait_for_deployment_to_be_running "k3s-test-deployment"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Expose deployed workload as a service"
    _run kubectl_expose_deployment "k3s-test-deployment" "k3s-test-service"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Get IP of service"
    _run get_service_ip "k3s-test-service"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi
    ip="${output}"

    subtest="Check service is accessible on network"
    _run check_service_is_accessible "${ip}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Get name of a running pod"
    _run get_random_pod_name_from_application "k3s-test"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi
    pod_name="${output}"

    subtest="Delete running pod"
    _run kubectl_delete "pod" "${pod_name}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check service remains accessible with failed pod"
    _run check_service_is_accessible "${ip}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Get image version of a running pod"
    _run confirm_image_of_application_pods "k3s-test" "nginx:1.20"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Upgrade deployed container images"
    _run upgrade_image_of_deployment "k3s-test-deployment" "nginx=nginx:1.21"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check service remains accessible after image upgrade"
    _run check_service_is_accessible "${ip}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check upgraded image version of a running pod"
    _run confirm_image_of_application_pods "k3s-test" "nginx:1.21"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Stop K3S server"
    _run stop_k3s_service
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check service remains accessible with failed K3S server"
    _run check_service_is_accessible "${ip}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Restart K3S server after simulated failure"
    _run start_k3s_service
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check K3S server is responsive to kubectl"
    _run get_random_pod_name_from_application "k3s-test"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi
}
