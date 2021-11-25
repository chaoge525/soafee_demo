#!/usr/bin/env bash
#
# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

get_guest_status() {

    xendomains_output=$(/usr/lib/xen/bin/xendomains status | grep "${1}" \
                        2>"${TEST_STDERR_FILE}")
    exitcode="${?}"

    if [ "${exitcode}" != 0 ]; then
        /usr/lib/xen/bin/xendomains status
        return "${exitcode}"
    fi

    guest_status=$(echo "${xendomains_output}" | \
                   awk '{print $NF}' | \
                   sed 's/[][]//g' \
                   2>>"${TEST_STDERR_FILE}")

    echo "${guest_status}"
    return "${exitcode}"

}

guest_is_running() {

    status=0
    output=""

    _run get_guest_status "${1}"
    if [ "${status}" -ne 0 ] && [ "${output}" != "running" ]; then
        return 1
    else
        return 0
    fi

}

guest_is_not_running() {

    # If the guest is not found then PASS
    # If the guest is found and it is dead: PASS
    # If the guest is found and it is not dead: FAIL

    guest_status=$(get_guest_status "${1}")
    if [ "${?}" -ne 1 ] && [ "${guest_status}" != "dead" ]; then
        return 1
    else
        return 0
    fi

}

test_guest_login_and_network_access() {
    expect guest-run-command.expect \
        "${1}" \
        "ping -c 5 8.8.8.8" \
        2>"${TEST_STDERR_FILE}"
}

shutdown_guest() {
    systemctl stop xendomains 2>"${TEST_STDERR_FILE}"
}

start_guest() {
    systemctl start xendomains 2>"${TEST_STDERR_FILE}"
}

start_xendomains() {
    systemctl start xendomains 2>"${TEST_STDERR_FILE}"
}

xendomains_is_running() {
    systemctl is-active xendomains 2>"${TEST_STDERR_FILE}"
}

wait_for_xendomains_to_be_running() {

    status=1
    _run wait_for_success 300 10 xendomains_is_running
    if [ "${status}" -ne 0 ]; then
        echo "Timeout reached before xendomains service is active"
        return "${status}"
    fi

    return "${status}"
}
