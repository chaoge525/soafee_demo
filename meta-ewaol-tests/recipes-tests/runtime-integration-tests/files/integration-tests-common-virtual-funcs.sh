#!/usr/bin/env bash
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

get_guest_vm_status() {

    sudo -v 2>"${TEST_STDERR_FILE}" || return 2

    xendomains_output=$(sudo -n /usr/lib/xen/bin/xendomains status \
                        | grep "${1}" 2>"${TEST_STDERR_FILE}")
    exitcode="${?}"

    if [ "${exitcode}" != 0 ]; then
        sudo -n /usr/lib/xen/bin/xendomains status
        return "${exitcode}"
    fi

    guest_vm_status=$(echo "${xendomains_output}" | \
                      awk '{print $NF}' | \
                      sed 's/[][]//g' \
                      2>>"${TEST_STDERR_FILE}")

    echo "${guest_vm_status}"
    return "${exitcode}"

}

guest_vm_is_running() {

    status=0
    output=""

    _run get_guest_vm_status "${1}"
    if [ "${status}" -eq 2 ]; then
        return 2
    elif [ "${status}" -ne 0 ] && [ "${output}" != "running" ]; then
        return 1
    else
        return 0
    fi

}

guest_vm_is_not_running() {

    # If the guest is not found then PASS
    # If the guest is found and it is dead: PASS
    # If the guest is found and it is not dead: FAIL

    guest_vm_status=$(get_guest_vm_status "${1}")
    if [ "${?}" -ne 1 ] && [ "${guest_vm_status}" != "dead" ]; then
        return 1
    else
        return 0
    fi

}

xendomains_is_running() {
    systemctl is-active xendomains 2>"${TEST_STDERR_FILE}"
}

xendomains_and_guest_vm_is_initialized() {

    _run wait_for_success 300 10 xendomains_is_running
    if [ "${status}" -ne 0 ]; then
        echo "Timeout reached before xendomains service is active"
        return "${status}"
    fi

    _run wait_for_success 300 10 guest_vm_is_running "${1}"
    if [ "${status}" -ne 0 ]; then
        echo "Timeout reached before Guest VM is running"
        return "${status}"
    fi

    return 0
}
