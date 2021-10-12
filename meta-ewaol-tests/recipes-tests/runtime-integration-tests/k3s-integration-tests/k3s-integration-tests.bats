#!/usr/bin/env bats
#
# Copyright (c) 2021, Arm Limited.
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

if [ -z "${K3S_TEST_CLEAN_ENV}" ]; then
    K3S_TEST_CLEAN_ENV=1
fi

load k3s-funcs.sh
load integration-tests-common-funcs.sh

# Ensure that the state of the orchestration service is reset to its
# out-of-the-box state, not polluted by a previous test suite execution
clean_test_environment() {

    # The logging function uses the current test name to categorise any log
    # messages specific to the test. Here, define this variable manually in
    # order to similarly categorise all messages relating to the clean-up
    # activities.
    export BATS_TEST_NAME="clean_test_environment"

    # Start the server if it was stopped
    _run systemd_service "is-active"
    if [ "${status}" -ne 0 ]; then
        log "DEBUG" "Starting K3S systemd service..."
        _run systemd_service "start"
    fi

    # Delete the service that wraps the test deployment if it exists
    _run query_kubectl "service" "k3s-test-service" "{.spec}"
    if [ "${status}" -eq 0 ]; then
        log "DEBUG" "Deleting service..."
        _run kubectl_delete "service" "k3s-test-service"
        if [ "${status}" -ne 0 ]; then
            log "FAIL" "Failed to delete the k3s-test-service Service"
            return 1
        fi
    fi

    # Get the names of the pods corresponding to the test deployment
    _run query_kubectl "pod" \
        "--selector=app=k3s-test" "{range .items[*]}{@.metadata.name}:{end}"
    if [ -n "${output}" ]; then
        mapfile -t pod_names < <(echo "${output}" | tr ':' '\n')
        # Delete the deployment
        log "DEBUG" "Deleting deployment..."
        _run kubectl_delete "deployment" "k3s-test-deployment"
        if [ "${status}" -ne 0 ]; then
            log "FAIL" "Failed to delete the k3s-test-deployment Deployment"
            return 1
        fi
        # Query the pods until they have been terminated (kubectl returns
        # failure)
        for pod_name in "${pod_names[@]}"; do
            if [ -z "${pod_name}" ]; then
                continue
            fi
            # shellcheck disable=SC2034
            for i in {1..60..10}; do
                log "DEBUG" "Checking ${pod_name} was stopped..."
                _run kubectl_query "pod" "${pod_name}" "{.status.phase}"
                if [ "${status}" -eq 0 ]; then
                    sleep 10
                else
                    break
                fi
            done
        done
    fi

    # Return the k3s service to its original state, if we created an override
    if [ -f "/lib/systemd/system/k3s.service.d/test-override.conf" ]; then
        log "DEBUG" "Deleting systemd override..."
        rm -rf /lib/systemd/system/k3s.service.d/test-override.conf
        systemctl daemon-reload
        systemctl restart k3s
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

    if [ "${K3S_TEST_CLEAN_ENV}" = "1" ]; then
        _run clean_test_environment
    fi
}

# Runs after the final test
teardown_file() {

    if [ "${K3S_TEST_CLEAN_ENV}" = "1" ]; then
        _run clean_test_environment
    fi

    _run finish_test_suite "${TEST_RUN_FILE}"
}

@test 'K3S orchestration of containerized web service' {

    subtest="Check or wait for server to be running"
    # shellcheck disable=SC2034
    for i in {1..300..10}; do
        log "DEBUG" "${subtest}..."

        # Check the server is running
        _run systemd_service "is-active"
        if [ "${status}" -ne 0 ]; then
            sleep 10
            continue
        fi
        # Check the system-pods have been created
        _run query_kubectl "pods" "--namespace=kube-system" \
            "{range .items[*]}{@.status.phase}:{end}"
        if [ "${status}" -ne 0 ]; then
            break
        elif [ -z "${output}" ]; then
            status=1
            sleep 10
        else
            # Check the system-pods are either Running or Succeeded
            mapfile -t pod_phases < <(echo "${output}" | tr ':' '\n')
            for phase in "${pod_phases[@]}"; do
                if [ -z "${phase}" ]; then
                    continue
                fi
                if [ "${phase}" != "Running" ] && \
                   [ "${phase}" != "Succeeded" ]; then
                    status=1
                    sleep 10
                    break
                fi
            done
            if [ "${status}" -eq 0 ]; then
                # All system-pods have been initialized
                break
            fi
        fi
    done
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Deploy workload"
    _run apply_workload "k3s-test-deployment.yaml"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check deployment is ready with pod replicas"
    _run kubectl_wait "deployment" "k3s-test-deployment" "Available"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Expose deployed workload as a service"
    _run kubectl_expose_deployment "k3s-test-deployment" \
        "k3s-test-service"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Get IP of service"
    _run query_kubectl "service" "k3s-test-service" "{.spec.clusterIP}"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi
    ip="${output}"

    subtest="Check service is accessible on network"
    # shellcheck disable=SC2034
    for i in {1..60..10}; do
        _run get_from_url "http://${ip}" "80"
        if [ "${status}" -eq 0 ]; then
            break
        else
            sleep 10
        fi
    done
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Get name of a running pod"
    pod_index="$((RANDOM % 3))"
    _run query_kubectl "pod" "--selector=app=k3s-test" \
        "{.items[${pod_index}].metadata.name}"
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
    # shellcheck disable=SC2034
    for i in {1..60..10}; do
        _run get_from_url "http://${ip}" "80"
        if [ "${status}" -eq 0 ]; then
            break
        else
            sleep 10
        fi
    done
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Get image version of a running pod"
    _run query_kubectl "pod" "--selector=app=k3s-test" \
        "{.items[${pod_index}].spec.containers[0].image}"
    if [ "${status}" -ne 0 ] || [ "${output}" != "nginx:1.20" ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Upgrade deployed container images"
    _run kubectl_set "image" "deployment/k3s-test-deployment" \
        "nginx=nginx:1.21"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi
    pod_name="${output}"

    subtest="Check service remains accessible after image upgrade"
    # shellcheck disable=SC2034
    for i in {1..60..10}; do
        _run get_from_url "http://${ip}" "80"
        if [ "${status}" -eq 0 ]; then
            break
        else
            sleep 10
        fi
    done
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check upgraded image version of a running pod"
    # shellcheck disable=SC2034
    for i in {1..60..10}; do
        _run query_kubectl "pod" "--selector=app=k3s-test" \
            "{.items[${pod_index}].spec.containers[0].image}"
        if [ "${status}" -ne 0 ]; then
            break
        elif [ "${output}" != "nginx:1.21" ]; then
            sleep 10
        else
            break
        fi
    done
    if [ "${status}" -ne 0 ] || [ "${output}" != "nginx:1.21" ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Stop K3S server"
    _run systemd_service "stop"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check service remains accessible with failed K3S server"
    # shellcheck disable=SC2034
    for i in {1..60..10}; do
        _run get_from_url "http://${ip}" "80"
        if [ "${status}" -eq 0 ]; then
            break
        else
            sleep 10
        fi
    done
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Restart K3S server after simulated failure"
    _run systemd_service "start"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check service is running"
    # shellcheck disable=SC2034
    for i in {1..60..10}; do
        _run systemd_service "is-active"
        if [ "${status}" -eq 0 ]; then
            break
        else
            sleep 10
        fi
    done
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check K3S server is responsive to kubectl"
    # shellcheck disable=SC2034
    for i in {1..60..10}; do
        _run query_kubectl "pod" "--selector=app=k3s-test" \
            "{.items[${pod_index}].metadata.name}"
        if [ "${status}" -eq 0 ]; then
            break
        else
            sleep 10
        fi
    done
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Change server configuration"
    _run update_server_arguments_and_restart "--disable-agent"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check K3S server is running after configuration change"
    # shellcheck disable=SC2034
    for i in {1..60..10}; do
        _run systemd_service "is-active"
        if [ "${status}" -eq 0 ]; then
            break
        else
            sleep 10
        fi
    done
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Delete test workload deployment"
    _run kubectl_delete "deployment" "k3s-test-deployment"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Deploy new workload to agent-less server"
    _run apply_workload "k3s-test-deployment.yaml"
    if [ "${status}" -ne 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    subtest="Check deployment has no running replicas"
    _run kubectl_wait "deployment" "k3s-test-deployment" "Available"
    if [ "${status}" -eq 0 ]; then
        log "FAIL" "${subtest}"
        return 1
    else
        log "PASS" "${subtest}"
    fi

    log "PASS"
}
