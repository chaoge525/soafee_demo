#!/usr/bin/env bash
#
# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

apply_workload() {
    kubectl apply -f "${1}"  2>"${TEST_STDERR_FILE}"
}

query_kubectl() {
    kubectl --request-timeout=60s get "${1}" "${2}" -o jsonpath="${3}" 2>"${TEST_STDERR_FILE}"
}

kubectl_wait() {
    kubectl wait --timeout=60s --for=condition="${3}" "${1}" "${2}" 2>"${TEST_STDERR_FILE}"
}

kubectl_delete() {
    kubectl delete "${1}" "${2}" 2>"${TEST_STDERR_FILE}"
}

kubectl_set() {
    kubectl set "${1}" "${2}" "${3}" 2>"${TEST_STDERR_FILE}"
}

kubectl_expose_deployment() {
    kubectl expose deployment "${1}" --name="${2}" 2>"${TEST_STDERR_FILE}"
}

systemd_service() {
    systemctl "${1}" k3s 2>"${TEST_STDERR_FILE}"
}

get_from_url() {
    timeout 10 wget -O - "${1}:${2}" 2>"${TEST_STDERR_FILE}"
}

pod_does_not_exist() {

    status=""

    _run kubectl_query "pod" "${1}" "{.status.phase}"
    if [ "${status}" -eq 0 ]; then
        # The pod still exists
        return 1
    else
        # The pod could not be found
        return 0
    fi

}

get_service_ip() {
    query_kubectl "service" "${1}" "{.spec.clusterIP}"
}

wait_for_deployment_to_be_running() {
    kubectl_wait "deployment" "${1}" "Available"
}

check_service_is_accessible() {
    wait_for_success 60 10 get_from_url "http://${1}" "80"
}

get_random_pod_name_from_application() {
    pod_index="$((RANDOM % 3))"
    query_kubectl "pod" "--selector=app=${1}" \
        "{.items[${pod_index}].metadata.name}"
}

test_application_pod_image() {

    _run query_kubectl "pod" "--selector=app=${1}" \
        "{.items[${3}].spec.containers[0].image}"
    if [ "${status}" -ne 0 ] || [ "${output}" != "${2}" ]; then
        return 1
    else
        return 0
    fi

}

confirm_image_of_application_pods() {

    pod_index="$((RANDOM % 3))"
    wait_for_success 60 10 test_application_pod_image "${1}" "${2}" \
        "${pod_index}"

}

upgrade_image_of_deployment() {
    kubectl_set "image" "deployment/${1}" "${2}"
}

start_k3s_service() {
    systemd_service "start"
}

stop_k3s_service() {
    systemd_service "stop"
}

k3s_service_is_running() {

    systemd_service "is-active"
    if [ ${?} ]; then
        return 0
    else
        return 1
    fi
}

k3s_system_pods_are_running() {

    _run query_kubectl "pods" "--namespace=kube-system" \
        "{range .items[*]}{@.status.phase}:{end}"
    if [ "${status}" -ne 0 ]; then
        return 2
    elif [ -z "${output}" ]; then
        return 1
    else
        # Check the system-pods are either Running or Succeeded
        mapfile -t pod_phases < <(echo "${output}" | tr ':' '\n')
        for phase in "${pod_phases[@]}"; do
            if [ -z "${phase}" ]; then
                continue
            fi
            if [ "${phase}" != "Running" ] && \
               [ "${phase}" != "Succeeded" ]; then
                return 1
            fi
        done
        return 0
    fi

}

wait_for_k3s_to_be_running() {

    _run wait_for_success 300 10 k3s_service_is_running
    if [ "${status}" -ne 0 ]; then
        echo "Timeout reached before k3s service is active"
        return "${status}"
    fi

    _run wait_for_success 300 10 k3s_system_pods_are_running
    if [ "${status}" -ne 0 ]; then
        echo "Timeout reached before k3s system pods were initialized"
    fi
    return "${status}"

}

remove_k3s_test_service() {

    # Delete the service that wraps the test deployment if it exists
    _run query_kubectl "service" "k3s-test-service" "{.spec}"
    if [ "${status}" -eq 0 ]; then
        _run kubectl_delete "service" "k3s-test-service"
        if [ "${status}" -ne 0 ]; then
            echo "Failed to delete the k3s-test-service Service"
            return 1
        fi
    fi

    # If we get here, we either couldn't find the service or it was successfully
    # deleted
    return 0
}

remove_k3s_test_deployment() {

    # Get the names of the pods corresponding to the test deployment
    _run query_kubectl "pod" \
        "--selector=app=k3s-test" "{range .items[*]}{@.metadata.name}:{end}"
    if [ -n "${output}" ]; then
        mapfile -t pod_names < <(echo "${output}" | tr ':' '\n')

        # Delete the deployment
        _run kubectl_delete "deployment" "k3s-test-deployment"
        if [ "${status}" -ne 0 ]; then
            echo "Failed to delete the k3s-test-deployment Deployment"
            return 1
        fi

        # Ensure all the pods have been terminated
        for pod_name in "${pod_names[@]}"; do
            if [ -z "${pod_name}" ]; then
                continue
            fi

            run_ wait_for_success 60 10 pod_does_not_exist "${pod_name}"
            if [ "${status}" -ne 0 ]; then
                echo "Failed to delete the k3s-test-deployment Deployment"
                return 1
            fi
        done
    fi

    return 0
}
