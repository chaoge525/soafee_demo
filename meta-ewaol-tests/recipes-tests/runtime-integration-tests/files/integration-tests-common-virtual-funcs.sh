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

xendomains_is_initialized() {

    _run wait_for_success 300 10 xendomains_is_running
    if [ "${status}" -ne 0 ]; then
        echo "Timeout reached before xendomains service is active"
        return "${status}"
    fi

    return 0
}

guest_vm_is_initialized() {

    _run wait_for_success 300 10 guest_vm_is_running "${1}"
    if [ "${status}" -ne 0 ]; then
        echo "Timeout reached before Guest VM '${1}' is running"
        return "${status}"
    fi

    return 0
}

guest_vm_reset_password() {

    # Use the systemd-detect-virt utility to determine if running on the Guest
    # VM (utility returns 0) or the Control VM (utility returns non-zero)
    _run systemd-detect-virt
    if [ "${status}" -ne 0 ]; then

        _run xendomains_is_initialized
        if [ "${status}" -ne 0 ]; then
            echo "${output}"
            return "${status}"
        fi

        _run guest_vm_is_initialized "${1}"
        if [ "${status}" -ne 0 ]; then
            echo "${output}"
            return "${status}"
        fi

        _run expect "${TEST_COMMON_DIR}/run-command.expect" \
            -hostname "${1}" \
            -command "sudo usermod -p '' ${USER} && \
                sudo passwd -e ${USER}" \
            -console "guest_vm" \
            2>"${TEST_STDERR_FILE}"

        if [ "${status}" -ne 0 ]; then
            echo "Expect script to reset '${USER}' password on Guest VM failed."
            echo "${output}"
            return "${status}"
        fi
    fi

    return 0
}

# Output a filtered list of Guest VMs (given by `xl list`), with names that
# begin with the first argument to this function
# To output all Guest VMs, pass an empty string to this function
get_guest_vm_names() {

    vm_basename="${1}"

    # tail +3 removes the column headings
    # cut selects the first column (Name)
    sudo -n xl list |\
        tail +3 |\
        cut -d" " -f1 |\
        grep "^${vm_basename}" |\
        xargs \
        2>"${TEST_STDERR_FILE}"
}

# Populate the environment variables (TEST_GUEST_VM_NAMES, TEST_GUEST_VM_COUNT)
# needed to perform actions on the Guest VM(s)
# If the variables already exist, do nothing
load_guest_vm_vars() {

    if [ -z "${TEST_GUEST_VM_NAMES}" ]; then

      # Determine the list of Guest VMs that the test suite will target
      _run get_guest_vm_names "${TEST_GUEST_VM_BASENAME}"
      if [ "${status}" -ne 0 ]; then
          log "FAIL"
          echo "${output}"
          return "${status}"
      fi
      export TEST_GUEST_VM_NAMES="${output}"

    fi

    if [ -z "${TEST_GUEST_VM_COUNT}" ]; then
      count=$(echo "${TEST_GUEST_VM_NAMES}" | wc -w)
      export TEST_GUEST_VM_COUNT="${count}"
    fi
}
