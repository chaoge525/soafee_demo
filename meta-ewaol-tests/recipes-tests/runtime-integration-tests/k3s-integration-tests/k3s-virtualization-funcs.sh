#!/usr/bin/env bash
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

load integration-tests-common-virtual-funcs.sh

if [ -z "${K3S_TEST_GUEST_VM_NAME}" ]; then
    K3S_TEST_GUEST_VM_NAME="%GUESTNAME%1"
fi

K3S_AGENT_OVERRIDE_FILENAME="/lib/systemd/system/k3s-agent.service.d/01-test-connect.conf"

# Override this test to validate that the pods are executed on the correct node
# (i.e. the agent on the Guest VM)
wait_for_deployment_to_be_running() {

    status=1

    # Check if the deployment is Available (may take some time, so kubectl wait)
    _run kubectl_wait "deployment" "${1}" "Available"
    if [ "${status}" -ne 0 ]; then
        return 1
    fi

    # Get the names of the pods corresponding to the test deployment
    _run query_kubectl "pod" \
        "--selector=app=k3s-test" "{range .items[*]}{@.metadata.name}:{end}"
    if [ -n "${output}" ]; then
        mapfile -t pod_names < <(echo "${output}" | tr ':' '\n')

        # The below ensures all the pods are running on the Guest VM (and not on
        # the Control VM)
        for pod_name in "${pod_names[@]}"; do
            if [ -z "${pod_name}" ]; then
                continue
            fi

            _run query_kubectl "pod" "${pod_name}" "{.spec.nodeName}"
            if [ "${status}" -ne 0 ]; then
                echo "Could not find the node running pod '${pod_name}'"
                return 1
            elif [ "${output}" != "${K3S_TEST_GUEST_VM_NAME}" ]; then
                echo "Node running pod '${pod_name}' was '${output}'"
                return 1
            fi

        done
    fi

    return 0
}

get_target_node_ip() {
    sudo -n kubectl get node "${K3S_TEST_GUEST_VM_NAME}" \
        -o jsonpath="{.status.addresses[?(@.type=='InternalIP')].address}"
}

# Revert the environment to a state where the Guest VM is idle (its agent is not
# connected to the server)
cleanup_k3s_agent_on_guest_vm() {

    # Stop the agent
    expect run-command.expect \
        -hostname "${K3S_TEST_GUEST_VM_NAME}" \
        -command "sudo -n systemctl stop k3s-agent" \
        -console "guest_vm" \
        2>"${TEST_STDERR_FILE}"

    # Remove the systemd override if it exists
    expect run-command.expect \
        -hostname "${K3S_TEST_GUEST_VM_NAME}" \
        -command "sudo -n rm -f ${K3S_AGENT_OVERRIDE_FILENAME} && \
             sudo -n systemctl daemon-reload" \
        -console "guest_vm" \
        2>"${TEST_STDERR_FILE}"

    kubectl_delete "node" "${K3S_TEST_GUEST_VM_NAME}"

    return 0
}

get_server_token() {
    sudo -n cat /var/lib/rancher/k3s/server/node-token 2>"${TEST_STDERR_FILE}"
}

get_server_ip() {
    ifconfig xenbr0 | awk '/inet addr/{print substr($2,6)}' 2>"${TEST_STDERR_FILE}"
}

configure_k3s_agent_on_guest_vm() {

    ip="${1}"
    token="${2}"
    override_dir=$(dirname "${K3S_AGENT_OVERRIDE_FILENAME}")

    cmd="\
sudo -n mkdir -p ${override_dir} && echo -e '\
[Service]\n\
ExecStart=\n\
ExecStart=/usr/local/bin/k3s agent --server=https://${ip}:6443 --token=${token} --node-label=ewaol.node-type=guest-vm' \
| sudo -n tee ${K3S_AGENT_OVERRIDE_FILENAME} > /dev/null \
&& sudo -n systemctl daemon-reload"

    expect run-command.expect \
        -hostname "${K3S_TEST_GUEST_VM_NAME}" \
        -command "${cmd}" \
        -console "guest_vm" \
        2>"${TEST_STDERR_FILE}"

}

start_k3s_agent_on_guest_vm() {

    expect run-command.expect \
        -hostname "${K3S_TEST_GUEST_VM_NAME}" \
        -command "sudo -n systemctl start k3s-agent" \
        -console "guest_vm" \
        2>"${TEST_STDERR_FILE}"

}

# Additional activities are required to run the k3s integration tests on a
# virtualized k3s cluster (Control VM server + Guest VM agent). Those functions
# are implemented by overriding those function calls here.
wait_for_k3s_to_be_running() {

    # The overridden function also ensures that xendomains and the target Guest
    # VM is running
    _run xendomains_and_guest_vm_is_initialized "${K3S_TEST_GUEST_VM_NAME}"
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

# Stop the agent (if it is running)
extra_cleanup() {
    cleanup_k3s_agent_on_guest_vm
}

# Start the agent (if it is not running)
extra_setup() {

    # Check if the agent is already running
    _run expect run-command.expect \
        -hostname "${K3S_TEST_GUEST_VM_NAME}" \
        -command "systemctl is-active k3s-agent" \
        -console "guest_vm" \
        2>"${TEST_STDERR_FILE}"

    if [ "${status}" -eq 0 ]; then
        # The agent is already running
        return 0
    fi

    # 1. Get the token
    # 2. Get the IP
    # 3. Add an override on the Guest VM
    # 4. Reload the daemon on the Guest VM
    # 5. Start the k3s-agent service on the Guest VM

    _run get_server_token
    if [ "${status}" -ne 0 ]; then
        echo "Could not get the k3s cluster token."
        return 1
    fi
    token="${output}"

    _run get_server_ip
    if [ "${status}" -ne 0 ]; then
        echo "Could not get the k3s Control VM IP address."
        return 1
    fi
    ip="${output}"

    _run configure_k3s_agent_on_guest_vm "${ip}" "${token}"
    if [ "${status}" -ne 0 ]; then
        echo "Failed to configure the k3s agent systemd override on the Guest VM."
        return 1
    fi

    _run start_k3s_agent_on_guest_vm
    if [ "${status}" -ne 0 ]; then
        echo "Failed to start the k3s agent on the Guest VM."
        return 1
    fi

    return 0
}
