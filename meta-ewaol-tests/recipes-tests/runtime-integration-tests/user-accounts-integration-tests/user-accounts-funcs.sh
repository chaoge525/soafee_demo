#!/usr/bin/env bash
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

check_user_home_dir_mode() {
    dirmode="$(stat -c "%A" "/home/${1}" 2>"${TEST_STDERR_FILE}")"
    if [ "${dirmode:4}" = "------" ]; then
        return 0
    else
        echo "Directory '/home/${1}' current mode: '${dirmode}'," \
             "expected mode: 'drwx------'."
        return 1
    fi
}

check_user_sudo_privileges() {
    sudo su "${1}" -c 'sudo -nv' 2>"${TEST_STDERR_FILE}"
}
