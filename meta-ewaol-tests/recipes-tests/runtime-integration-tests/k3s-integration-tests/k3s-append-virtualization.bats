#!/usr/bin/env bats
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT
#
# Additional BATS code to be appended to the k3s test suite, if running on a
# virtualization image

if [ -z "${K3S_TEST_GUEST_VM_NAME}" ]; then
    K3S_TEST_GUEST_VM_NAME="${EWAOL_GUEST_VM_HOSTNAME}1"
fi

export TEST_GUEST_VM_NAME="${K3S_TEST_GUEST_VM_NAME}"

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
