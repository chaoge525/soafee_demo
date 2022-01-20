#!/usr/bin/env bash
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

load integration-tests-common-virtual-funcs.sh

if [ -z "${K3S_TEST_GUEST_NAME}" ]; then
    K3S_TEST_GUEST_NAME="ewaol-vm1"
fi

K3S_AGENT_OVERRIDE_FILENAME="/lib/systemd/system/k3s-agent.service.d/01-test-connect.conf"

# Override this test to validate that the pods are executed on the correct node
# (i.e. the agent on the VM)
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

        # The below ensures all the pods are running on the Guest (and not on
        # the Host)
        for pod_name in "${pod_names[@]}"; do
            if [ -z "${pod_name}" ]; then
                continue
            fi

            _run query_kubectl "pod" "${pod_name}" "{.spec.nodeName}"
            if [ "${status}" -ne 0 ]; then
                echo "Could not find the node running pod '${pod_name}'"
                return 1
            elif [ "${output}" != "${K3S_TEST_GUEST_NAME}" ]; then
                echo "Node running pod '${pod_name}' was '${output}'"
                return 1
            fi

        done
    fi

    return 0
}

get_target_node_ip() {
    kubectl get node "${K3S_TEST_GUEST_NAME}" \
        -o jsonpath="{.status.addresses[?(@.type=='InternalIP')].address}"
}

# Revert the environment to a state where the VM is idle (its agent is not
# connected to the Host server)
cleanup_k3s_agent_on_guest() {

    # Stop the agent
    expect guest-run-command.expect \
        "${K3S_TEST_GUEST_NAME}" \
        "systemctl stop k3s-agent" \
        2>"${TEST_STDERR_FILE}"

    # Remove the systemd override if it exists
    expect guest-run-command.expect \
        "${K3S_TEST_GUEST_NAME}" \
        "rm -f ${K3S_AGENT_OVERRIDE_FILENAME} && systemctl daemon-reload" \
        2>"${TEST_STDERR_FILE}"

    kubectl_delete "node" "${K3S_TEST_GUEST_NAME}"

    return 0
}

get_host_server_token() {
    cat /var/lib/rancher/k3s/server/node-token 2>"${TEST_STDERR_FILE}"
}

get_host_server_ip() {
    ifconfig xenbr0 | awk '/inet addr/{print substr($2,6)}' 2>"${TEST_STDERR_FILE}"
}

configure_k3s_agent_on_vm() {

    ip="${1}"
    token="${2}"
    override_dir=$(dirname "${K3S_AGENT_OVERRIDE_FILENAME}")

    cmd="\
mkdir -p ${override_dir} && echo -e '\
[Service]\n\
ExecStart=\n\
ExecStart=/usr/local/bin/k3s agent --server=https://${ip}:6443 --token=${token} --node-label=ewaol.node-type=vm' \
> ${K3S_AGENT_OVERRIDE_FILENAME} \
&& systemctl daemon-reload"

    expect guest-run-command.expect \
        "${K3S_TEST_GUEST_NAME}" \
        "${cmd}" \
        2>"${TEST_STDERR_FILE}"

}

start_k3s_agent_on_vm() {

    expect guest-run-command.expect \
        "${K3S_TEST_GUEST_NAME}" \
        "systemctl start k3s-agent" \
        2>"${TEST_STDERR_FILE}"

}

# Additional activities are required to run the k3s integration tests on a
# virtualized k3s cluster (Host server + VM agent). Those functions are
# implemented by overriding those function calls here.

wait_for_k3s_to_be_running() {

    # The overridden function also ensures that xendomains and the target Guest
    # is running
    _run xendomains_and_guest_is_initialized "${K3S_TEST_GUEST_NAME}"
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
    cleanup_k3s_agent_on_guest
}

# Start the agent (if it is not running)
extra_setup() {

    # Check if the agent is already running
    _run expect guest-run-command.expect \
        "${K3S_TEST_GUEST_NAME}" \
        "systemctl is-active k3s-agent" \
        2>"${TEST_STDERR_FILE}"

    if [ "${status}" -eq 0 ]; then
        # The agent is already running
        return 0
    fi

    # 1. Get the token
    # 2. Get the IP
    # 3. Add an override on the VM
    # 4. Reload the daemon on the VM
    # 5. Start the k3s-agent service on the VM

    _run get_host_server_token
    if [ "${status}" -ne 0 ]; then
        echo "Could not get the k3s cluster token."
        return 1
    fi
    token="${output}"

    _run get_host_server_ip
    if [ "${status}" -ne 0 ]; then
        echo "Could not get the k3s host IP address."
        return 1
    fi
    ip="${output}"

    _run configure_k3s_agent_on_vm "${ip}" "${token}"
    if [ "${status}" -ne 0 ]; then
        echo "Failed to configure the k3s agent systemd override on the VM."
        return 1
    fi

    _run start_k3s_agent_on_vm
    if [ "${status}" -ne 0 ]; then
        echo "Failed to start the k3s agent on the VM."
        return 1
    fi

    return 0
}
