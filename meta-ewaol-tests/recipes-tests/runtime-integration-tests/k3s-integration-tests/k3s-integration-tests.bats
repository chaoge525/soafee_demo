#!/usr/bin/env bats
#
# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Run-time validation tests for the K3s container orchestration platform.

# Set generic configuration

if [ -z "${K3S_TEST_LOG_DIR}" ]; then
    TEST_LOG_DIR="${HOME}/runtime-integration-tests-logs"
else
    TEST_LOG_DIR="${K3S_TEST_LOG_DIR}"
fi

export TEST_LOG_FILE="${TEST_LOG_DIR}/k3s-integration-tests.log"
export TEST_STDERR_FILE="${TEST_LOG_DIR}/k3s-stderr.log"
export TEST_RUN_FILE="${TEST_RUNTIME_DIR}/k3s-integration-tests.pgid"

# Set test-suite specific configuration

export TEST_CLEAN_ENV="${K3S_TEST_CLEAN_ENV:=1}"

load "${TEST_COMMON_DIR}/integration-tests-common-funcs.sh"
load "${TEST_DIR}/k3s-funcs.sh"

# Ensure that the state of the orchestration service is reset to its
# out-of-the-box state, not polluted by a previous test suite execution
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

    # If the environment clean option is disabled, we should still wait for K3s
    # to be fully initialized (e.g. after booting) before running the tests
    _run wait_for_k3s_to_be_running
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        return 1
    fi

    export K3S_TEST_TARGET="locally"

    # Call without run as we might export environment variables
    extra_setup
    status="${?}"
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

# shellcheck disable=SC2016
@test 'K3s container orchestration for ${K3S_TEST_TYPE}' {

    subtest="Deploy workload ${K3S_TEST_TARGET}"
    _run apply_workload "${TEST_DIR}/k3s-test-deployment.yaml"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check deployment is ready ${K3S_TEST_TARGET} with pod replicas"
    _run wait_for_deployment_to_be_running "k3s-test"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Expose workload deployed ${K3S_TEST_TARGET} as a service"
    _run kubectl_expose_deployment "k3s-test" "30000"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Get the IP address of nodes running workload deployed ${K3S_TEST_TARGET}"
    _run get_target_node_ips
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi
    ips="${output}"

    subtest="Check deployment exposed ${K3S_TEST_TARGET} is accessible on network"
    _run check_service_is_accessible "${ips}" "30000"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check old image version of a pod running ${K3S_TEST_TARGET}"
    _run confirm_image_of_application_pods "k3s-test" "nginx:1.20"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Upgrade container images of workload deployed ${K3S_TEST_TARGET}"
    _run upgrade_image_of_deployment "k3s-test" "nginx=nginx:1.21"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check all upgraded pods are running ${K3S_TEST_TARGET}"
    _run wait_for_deployment_to_be_running "k3s-test"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check upgraded image version of a pod running ${K3S_TEST_TARGET}"
    _run confirm_image_of_application_pods "k3s-test" "nginx:1.21"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check deployment exposed ${K3S_TEST_TARGET} remains accessible after image upgrade"
    _run check_service_is_accessible "${ips}" "30000"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Stop K3s server"
    _run stop_k3s_service
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check deployment exposed ${K3S_TEST_TARGET} remains accessible with failed K3s server"
    _run check_service_is_accessible "${ips}" "30000"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Restart K3s server after simulated failure"
    _run start_k3s_service
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check K3s server is responsive to kubectl"
    _run get_random_pod_name_from_application "k3s-test"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

}
