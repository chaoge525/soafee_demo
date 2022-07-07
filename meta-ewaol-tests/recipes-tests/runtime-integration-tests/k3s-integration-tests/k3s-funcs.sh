#!/usr/bin/env bash
#
# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

apply_workload() {
    sudo -n kubectl apply -f "${1}"  2>"${TEST_STDERR_FILE}"
}

query_kubectl() {
    sudo -n kubectl --request-timeout=60s get "${1}" "${2}" \
        -o jsonpath="${3}" 2>"${TEST_STDERR_FILE}"
}

kubectl_wait() {
    sudo -n kubectl wait --timeout=120s --for=condition="${3}" "${1}" "${2}" \
        2>"${TEST_STDERR_FILE}"
}

kubectl_delete() {
    sudo -n kubectl delete "${1}" "${2}" 2>"${TEST_STDERR_FILE}"
}

kubectl_set() {
    sudo -n kubectl set "${1}" "${2}" "${3}" 2>"${TEST_STDERR_FILE}"
}

kubectl_expose_deployment() {
    sudo -n kubectl create service nodeport "${1}" --tcp=80:80 \
        --node-port="${2}" 2>"${TEST_STDERR_FILE}"
}

systemd_service() {
    sudo -n systemctl "${1}" k3s 2>"${TEST_STDERR_FILE}"
}

get_from_url() {
    timeout 10 wget -o /dev/null -O - "${1}:${2}" 2>"${TEST_STDERR_FILE}"
}

pod_does_not_exist() {

    status=""

    _run query_kubectl "pod" "${1}" "{.status.phase}"
    if [ "${status}" -eq 0 ]; then
        # The pod still exists
        return 1
    else
        # The pod could not be found
        return 0
    fi

}

get_target_node_ips() {
    echo "localhost"
}

# First argument is the application name
# Second argument is an optional list of pod names that will define the number
# of pods to expect to be running, and also the names that should be excluded
# from consideration. For example, the pod names as they were before an upgrade.
wait_for_deployment_to_be_running() {
    _run kubectl_wait "deployment" "${1}" "Available"
    if [ "${status}" -ne 0 ]; then
        return "${status}"
    fi

    # If we have a list of pods in the second argument, then check we have the
    # correct number, none of which are in that list
    if [ -n "${2}" ]; then

        excluded_pods="${2}"
        expected_pod_count=$(wc -w <<< "${excluded_pods}")

        _run wait_for_success 60 10 check_running_pod_count_with_exclusions \
           "${1}" "${expected_pod_count}" "${excluded_pods}"
        if [ "${status}" -ne 0 ]; then
            echo -n "Timeout reached before ${expected_pod_count} new"
            echo " Pods were found to be running the application deployment."
            return "${status}"
        fi

    fi
}

# First argument is space-separated list of IP addresses
# Second argument is the port to use to query each IP
check_service_is_accessible() {
    for ip in ${1}; do
        _run wait_for_success 60 10 get_from_url "http://${ip}" "${2}"
        if [ "${status}" -ne 0 ]; then
            echo "${output}"
            echo "Timeout reached before http://${ip} responded on port ${2}"
            return "${status}"
        fi
    done
}

get_random_pod_name_from_application() {
    pod_index=0
    query_kubectl "pod" "--selector=app=${1}" \
        "{.items[${pod_index}].metadata.name}"
}

get_pod_names_from_application() {

    # Get the names of the pods corresponding to the test deployment
    _run query_kubectl "pod" \
        "--selector=app=${1}" "{range .items[*]}{@.metadata.name}:{end}"
    if [ -n "${output}" ]; then
        echo "${output}" | tr ':' ' '
    else
        echo "No pods found"
        return 1
    fi

}

# Checks that the provided number of pods exist for the provided application,
# and are in the 'Running' state
# Ignore any pod names which are provided in the second argument
check_running_pod_count_with_exclusions() {

    app_name="${1}"
    expected_pod_count="${2}"
    excluded_pod_names="${*:3}"

    non_excluded_pod_count=0

    # Get the names of the pods corresponding to the test deployment
    _run query_kubectl "pod" \
        "--selector=app=${app_name}" "{range .items[*]}{@.metadata.name}:{end}"
    if [ -n "${output}" ]; then
        mapfile -t pod_names < <(echo "${output}" | tr ':' '\n')

        for pod_name in "${pod_names[@]}"; do
            if [ -z "${pod_name}" ]; then
                continue
            fi

            # If the pod name is not found in the excluded list
            if ! echo "${excluded_pod_names}" | grep -w -q "${pod_name}"; then

                _run query_kubectl "pod" "${pod_name}" "{.status.phase}"
                if [ "${status}" -ne 0 ]; then
                    continue
                elif [ -z "${output}" ]; then
                    continue
                elif [ "${output}" != "Running" ]; then
                    continue
                fi

                non_excluded_pod_count=$((non_excluded_pod_count+1))
            fi

        done

        if [ "${non_excluded_pod_count}" -ne "${expected_pod_count}" ]; then
            return 1
        else
            return 0
        fi

    else
        return 1
    fi

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

    pod_index=0
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
    _run query_kubectl "service" "k3s-test" "{.spec}"
    if [ "${status}" -eq 0 ]; then
        _run kubectl_delete "service" "k3s-test"
        if [ "${status}" -ne 0 ]; then
            echo "Failed to delete the k3s-test Service"
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
        _run kubectl_delete "deployment" "k3s-test"
        if [ "${status}" -ne 0 ]; then
            echo "Failed to delete the k3s-test Deployment"
            return 1
        fi

        # Ensure all the pods have been terminated
        for pod_name in "${pod_names[@]}"; do
            if [ -z "${pod_name}" ]; then
                continue
            fi

            _run wait_for_success 60 10 pod_does_not_exist "${pod_name}"
            if [ "${status}" -ne 0 ]; then
                echo "Failed to delete the k3s-test Deployment"
                return 1
            fi
        done
    fi

    return 0
}

base_cleanup() {

    _run wait_for_k3s_to_be_running
    if [ "${status}" -ne 0 ]; then
        echo "${output}"
        return "${status}"
    fi

    _run remove_k3s_test_service
    if [ "${status}" -ne 0 ]; then
        echo "${output}"
        return "${status}"
    fi

    _run remove_k3s_test_deployment
    if [ "${status}" -ne 0 ]; then
        echo "${output}"
        return "${status}"
    fi

}
