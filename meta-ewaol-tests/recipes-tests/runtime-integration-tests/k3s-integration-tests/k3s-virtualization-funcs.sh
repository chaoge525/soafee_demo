#!/usr/bin/env bash
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

get_random_pod_name_from_application() {
    pod_index="$((RANDOM % TEST_GUEST_VM_COUNT))"
    query_kubectl "pod" "--selector=app=${1}" \
        "{.items[${pod_index}].metadata.name}"
}

confirm_image_of_application_pods() {
    pod_index="$((RANDOM % TEST_GUEST_VM_COUNT))"
    wait_for_success 180 10 test_application_pod_image "${1}" "${2}" \
        "${pod_index}"
}

# Override this function to ensure that we deploy one Pod per Guest VM
apply_workload() {
  echo -e "  replicas: ${TEST_GUEST_VM_COUNT}" | sudo -n tee -a "${1}" \
    > /dev/null
  sudo -n kubectl apply -f "${1}"  2>"${TEST_STDERR_FILE}"
}

# Override this test to validate that the pods are executed on the correct node
# (i.e. the agent on the Guest VM)
# First argument is the application name
# Second argument is an optional list of pod names that will define the number
# of pods to expect to be running, and also the names that should be excluded
# from consideration. For example, the pod names as they were before an upgrade.
wait_for_deployment_to_be_running() {

    status=1

    # Check if the deployment is Available (may take some time, so kubectl wait)
    _run kubectl_wait "deployment" "${1}" "Available"
    if [ "${status}" -ne 0 ]; then
        return 1
    fi

    # If we have a list of pods in the second argument, then check we have the
    # correct number, none of which are in that list
    if [ -n "${2}" ]; then

        excluded_pods="${2}"
        expected_pod_count=$(wc -w <<< "${excluded_pods}")

        _run wait_for_success 180 10 check_running_pod_count_with_exclusions \
           "${1}" "${expected_pod_count}" "${excluded_pods}"
        if [ "${status}" -ne 0 ]; then
            echo -n "Timeout reached before ${expected_pod_count} new"
            echo " Pods were found to be running the application deployment."
            return "${status}"
        fi

    fi

    # Get the names of the current pods corresponding to the test deployment
    _run query_kubectl "pod" \
        "--selector=app=${1}" "{range .items[*]}{@.metadata.name}:{end}"
    if [ -n "${output}" ]; then
        mapfile -t pod_names < <(echo "${output}" | tr ':' '\n')

        # The below ensures all the pods are running on the Guest VMs (and not
        # on the Control VM)
        for pod_name in "${pod_names[@]}"; do
            if [ -z "${pod_name}" ]; then
                continue
            fi

            _run query_kubectl "pod" "${pod_name}" "{.spec.nodeName}"
            if [ "${status}" -ne 0 ]; then
                echo "Could not find the node running pod '${pod_name}'"
                return 1
            elif [ "$(echo "${TEST_GUEST_VM_NAMES}" \
                    | grep -w -q "${output}")" -ne 0 ]; then
                echo "Node running pod '${pod_name}' was '${output}'."
                echo "The target nodes were: ${TEST_GUEST_VM_NAMES}."
                return 1
            fi

        done
    fi

    return 0
}

get_target_node_ips() {

    ips=""

    echo "" > "${TEST_STDERR_FILE}"

    guest_vm_idx=0
    for guest_vm in ${TEST_GUEST_VM_NAMES}; do
        guest_vm_idx=$((guest_vm_idx+1))

        ip=$(sudo -n kubectl get node "${guest_vm}"\
             -o jsonpath="{.status.addresses[?(@.type=='InternalIP')].address}"\
             2>> "${TEST_STDERR_FILE}")

        ips="${ips} ${ip}"
    done

    echo "${ips}"
}

# Revert the environment to a state where the Guest VM is idle (its agent is not
# connected to the server)
cleanup_k3s_agent_on_guest_vm() {

    load_guest_vm_vars

    guest_vm_idx=0
    for guest_vm in ${TEST_GUEST_VM_NAMES}; do
        guest_vm_idx=$((guest_vm_idx+1))

        # Stop the agent
        expect "${TEST_COMMON_DIR}/run-command.expect" \
            -hostname "${guest_vm}" \
            -command "sudo -n systemctl stop k3s-agent" \
            -console "guest_vm" \
            2>"${TEST_STDERR_FILE}"

        # Remove the systemd override if it exists
        expect "${TEST_COMMON_DIR}/run-command.expect" \
            -hostname "${guest_vm}" \
            -command "sudo -n rm -f ${K3S_AGENT_OVERRIDE_FILENAME} && \
                 sudo -n systemctl daemon-reload" \
            -console "guest_vm" \
            2>"${TEST_STDERR_FILE}"

        kubectl_delete "node" "${guest_vm}"

    done

    return 0
}

get_server_token() {
    sudo -n cat /var/lib/rancher/k3s/server/node-token 2>"${TEST_STDERR_FILE}"
}

get_server_ip() {
    ifconfig xenbr0 | awk '/inet addr/{print substr($2,6)}' 2>"${TEST_STDERR_FILE}"
}

configure_k3s_agent_on_guest_vm() {

    guest_vm="${1}"
    ip="${2}"
    token="${3}"
    override_dir=$(dirname "${K3S_AGENT_OVERRIDE_FILENAME}")

    cmd="\
sudo -n mkdir -p ${override_dir} && echo -e '\
[Service]\n\
ExecStart=\n\
ExecStart=/usr/local/bin/k3s agent --server=https://${ip}:6443 --token=${token} --node-label=ewaol.node-type=guest-vm' \
| sudo -n tee ${K3S_AGENT_OVERRIDE_FILENAME} > /dev/null \
&& sudo -n systemctl daemon-reload"

    expect "${TEST_COMMON_DIR}/run-command.expect" \
        -hostname "${1}" \
        -command "${cmd}" \
        -console "guest_vm" \
        2>"${TEST_STDERR_FILE}"

}

start_k3s_agent_on_guest_vm() {

    expect "${TEST_COMMON_DIR}/run-command.expect" \
        -hostname "${1}" \
        -command "sudo -n systemctl start k3s-agent" \
        -console "guest_vm" \
        2>"${TEST_STDERR_FILE}"

}

# Override this function to ensure virtualization-specific Control VM
# initialization is complete
wait_for_k3s_to_be_running() {

    # Ensure the xendomains service is initialized
    _run xendomains_is_initialized
    if [ "${status}" -ne 0 ]; then
        echo "${output}"
        return "${status}"
    fi

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
