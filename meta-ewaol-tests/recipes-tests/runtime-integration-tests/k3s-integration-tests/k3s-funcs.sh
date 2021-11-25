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
    kubectl wait --timeout=120s --for=condition="${3}" "${1}" "${2}" 2>"${TEST_STDERR_FILE}"
}

kubectl_delete() {
    kubectl delete "${1}" "${2}" 2>"${TEST_STDERR_FILE}"
}

kubectl_set() {
    kubectl set "${1}" "${2}" "${3}" 2>"${TEST_STDERR_FILE}"
}

kubectl_expose_deployment() {
    kubectl expose deployment "${1}" --name="${2}" 2>"${TEST_STDERR_FILE}"

    # Create a port forwarding service that allows the service to be accessed
    # via a particular port on localhost, even if that service is deployed
    # remotely (i.e., within a VM)
    cat << EOF > /lib/systemd/system/k3s-port-forward.service
[Unit]
Description=Run k3s port forwarding
Documentation=https://k3s.io
Requires=k3s.service
After=k3s.service

[Install]
WantedBy=multi-user.target
WantedBy=k3s.service

[Service]
Type=simple
KillMode=control-group
TimeoutStartSec=0
Restart=always
RestartSec=5s
# The port-forwarding process can enter an error state but remain running,
# requiring a restart (e.g. when the forwarded service is changed).
# To identify an error, check each line of output for the string 'error'. Only
# if one is found should the process exit with an error code for systemd to
# subsequently restart the service.
ExecStart=/bin/bash -c "\\
    awk '{if(tolower(\$\$0)~/error/){print \$\$0;exit(1)}} 1' \\
        < <(kubectl port-forward service/${2} ${3}:80 2>&1 || \\
            echo \"Command returned error code: \$\${?}\"); \\
    if [ \$\${?} -ne 0 ]; \\
    then \\
        exit 1; \\
    else \\
        exit 0; \\
    fi;"
EOF

    # Add an override to the k3s service that starts the new forwarding service
    # (if it exists) when the k3s service is started
    mkdir -p /lib/systemd/system/k3s.service.d
    cat << EOF > /lib/systemd/system/k3s.service.d/01-port-forward-dependency.conf
[Unit]
Wants=k3s-port-forward.service
EOF

    systemctl daemon-reload 2>"${TEST_STDERR_FILE}"
    systemctl restart k3s 2>>"${TEST_STDERR_FILE}"
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

check_service_is_accessible_via_server_routing_rules() {
    # Expect to access the service via requests to localhost with a particular
    # port (first argument) that has been routed to that service
    wait_for_success 60 10 get_from_url "http://localhost" "${1}"
}

check_service_is_accessible_directly() {
    # The service's ClusterIP (first argument) can be used to access it directly
    # on its listening port (second argument)
    wait_for_success 60 10 get_from_url "http://${1}" "${2}"
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

    # Remove the port-forwarding service if we created it
    if [ -f "/lib/systemd/system/k3s-port-forward.service" ]; then
        systemctl stop k3s-port-forward
        rm -f /lib/systemd/system/k3s-port-forward.service
    fi

    # Remove the dependency if we created it
    if [ -f "/lib/systemd/system/k3s.service.d/01-port-forward-dependency.conf" ];
    then
        rm -f /lib/systemd/system/k3s.service.d/01-port-forward-dependency.conf
    fi

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
# The standard k3s integration tests do not require extra activities on test
# suite start/end, so define empty functions here

extra_cleanup() {
    return 0
}

extra_setup() {
    return 0
}

extra_teardown() {
    return 0
}
