#!/usr/bin/env bash
#
# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

test_guest_vm_login_and_network_access() {
    expect guest-vm-run-command.expect \
        "${1}" \
        "ping -c 5 8.8.8.8" \
        2>"${TEST_STDERR_FILE}"
}

shutdown_guest_vm() {
    sudo -n systemctl stop xendomains 2>"${TEST_STDERR_FILE}"
}

start_guest_vm() {
    sudo -n systemctl start xendomains 2>"${TEST_STDERR_FILE}"
}

start_xendomains() {
    sudo -n systemctl start xendomains 2>"${TEST_STDERR_FILE}"
}
