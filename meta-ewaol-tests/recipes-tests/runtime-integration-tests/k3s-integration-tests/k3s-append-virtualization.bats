#!/usr/bin/env bats
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT
#
# Additional BATS code to be appended to the k3s test suite, if running on a
# virtualization image

if [ -z "${K3S_TEST_GUEST_VM_BASENAME}" ]; then
    K3S_TEST_GUEST_VM_BASENAME="${EWAOL_GUEST_VM_HOSTNAME}"
fi

export TEST_GUEST_VM_BASENAME="${K3S_TEST_GUEST_VM_BASENAME}"

export K3S_AGENT_OVERRIDE_FILENAME="/lib/systemd/system/k3s-agent.service.d/01-test-connect.conf"

load "${TEST_COMMON_DIR}/integration-tests-common-virtual-funcs.sh"
load "${TEST_DIR}/k3s-virtualization-funcs.sh"

# Override the clean_test_environment call for the virtualization case to
# include an optional extra clean-up in addition to the normal base clean-up
clean_test_environment() {

    export BATS_TEST_NAME="clean_test_environment"
    status=0

    _run base_cleanup
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        return 1
    fi

    _run cleanup_k3s_agent_on_guest_vm
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        return 1
    fi

    _run extra_cleanup
    if [ "${status}" -ne 0 ]; then
        log "FAIL"
        return 1
    fi
}

# Start the agent (if it is not running)
extra_setup() {

    load_guest_vm_vars

    # The test descriptions output to the log should be informative, so let the
    # user know how many VMs are being orchestrated
    export K3S_TEST_TARGET="on ${TEST_GUEST_VM_COUNT} Guest VMs"

    output=""

    # 1. Get the token
    # 2. Get the IP

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

    # Connect each Guest VM to the K3s cluster

    guest_vm_idx=0
    for guest_vm in ${TEST_GUEST_VM_NAMES}; do
        guest_vm_idx=$((guest_vm_idx+1))

        vm_description="Guest VM ${guest_vm_idx}/${TEST_GUEST_VM_COUNT} (${guest_vm})"

        # Ensure the VM is running
        _run guest_vm_is_initialized "${guest_vm}"
        if [ "${status}" -ne 0 ]; then
            echo "${output}"
            return "${status}"
        fi

        # Check if the agent is already running
        _run expect "${TEST_COMMON_DIR}/run-command.expect" \
            -hostname "${guest_vm}" \
            -command "systemctl is-active k3s-agent" \
            -console "guest_vm" \
            2>"${TEST_STDERR_FILE}"

        if [ "${status}" -eq 0 ]; then
            # The agent is already running
            continue
        fi

        # 3. Add an override on the Guest VM
        # 4. Reload the daemon on the Guest VM
        # 5. Start the k3s-agent service on the Guest VM

        _run configure_k3s_agent_on_guest_vm "${guest_vm}" "${ip}" "${token}"
        if [ "${status}" -ne 0 ]; then
            echo "Failed to configure the K3s agent systemd override on ${vm_description}"
            return "${status}"
        fi

        _run start_k3s_agent_on_guest_vm "${guest_vm}"
        if [ "${status}" -ne 0 ]; then
            echo "Failed to start the K3s agent on ${vm_description}"
            return "${status}"
        fi

    done
}
