#!/usr/bin/env bash
#
# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Arg1: Image name
# Returns 0 if image exists
# Returns 1 if image does not exist
does_image_exist() {
    if [ "$(sudo -n docker images 2>"${TEST_STDERR_FILE}" \
        | grep -c "${1}")" -eq 1 ]; then
            return 0
    else
            return 1
    fi
}

# Arg1: Image name
# Returns exit code of the image rm command
image_remove() {

    # use --force to avoid having to remove any dependent containers that we
    # have created
    sudo -n docker image rm "${1}" --force 2>"${TEST_STDERR_FILE}"
}

# Arg1: Arguments passed to the engine for running the container
# Arg2: Image name
# Arg3: Command to execute in container
#
# If detached (with '-d'), returns exit code of the container creation (exit
# code of command is available by subsequently inspecting the container
# status), and STDOUT is the container ID.
#
# If not detached, returns exit code for the command, and STDOUT is the output
# of the command
container_run() {

    engine_args="${1}"
    image_name="${2}"
    container_cmd="${*:3}"

    # shellcheck disable=SC2086
    sudo -n docker run "${engine_args}" "${image_name}" ${container_cmd} \
        2>"${TEST_STDERR_FILE}"
}

# Arg1: Container ID
# Returns state.exitcode from the container inspect
# STDOUT is the state.status from the container inspect
check_container_state() {

    container_id="${1}"

    inspect_output=$(sudo -n docker inspect \
        -f '{{.State.Status}},{{.State.ExitCode}}' "${container_id}" \
        2>"${TEST_STDERR_FILE}" )
    if [ -z "${inspect_output}" ]; then
        echo "Inspect failed"
        return 1
    fi

    status=$(echo "${inspect_output}" | cut -d, -f1)
    exitcode=$(echo "${inspect_output}" | cut -d, -f2)

    echo "${status}"
    return "${exitcode}"
}

# Arg1: Container ID
# Returns 0 if running, 1 if not running
check_container_is_running() {

    _run check_container_state "${1}"
    if [ "${status}" -ne 0 ] || [ "${output}" != "running" ]; then
        return 1
    else
        return 0
    fi

}

# Arg1: Container ID
# Returns 1 if running, 0 if not running
check_container_is_not_running() {
    ! check_container_is_running "${1}"
}


# Arg1: Container ID
# Returns exit code of the container stop command
container_stop() {

    container_id="${1}"

    sudo -n docker container stop "${container_id}" 2>"${TEST_STDERR_FILE}"
}

# Arg1: Container ID
# Returns exit code of the container rm command
container_remove() {

    container_id="$1"

    sudo -n docker container rm "${container_id}" --force \
        2>"${TEST_STDERR_FILE}"
}

# Arg1: Image name
# STDOUT are the running container IDs for the image
get_running_containers() {

    image_name="${1}"

    sudo -n docker ps -q --filter ancestor="${image_name}" \
        2>"${TEST_STDERR_FILE}"
}

# Arg1: Image name
clean_and_remove_image() {

    image=$(basename "${1}")
    rc=0

    _run get_running_containers "${image}"
    if [ "${status}" -ne 0 ]; then
        echo "Failed getting running containers of image '${image}'"
        rc="${status}"
    fi

    if [ -n "${output}" ]; then
        for container_id in ${output}; do

            _run container_stop "${container_id}"
            if [ "${status}" -ne 0 ]; then
                echo "Failed to stop a running container '${container_id}' of" \
                    "image '${image}'"
                rc="${status}"
            fi

        done
    fi

    # Remove the image if it exists
    _run does_image_exist "${image}"
    if [ "${status}" ]; then

        _run image_remove "${image}"
        if [ "${status}" -ne 0 ]; then
            echo "Failed to remove image '${image}'"
            rc="${status}"
        fi

    fi

    return "${rc}"
}

base_cleanup() {

    # Remove any dangling containers based on the image
    _run clean_and_remove_image "${CE_TEST_IMAGE}"
    if [ "${status}" -ne 0 ]; then
        echo "Failed to remove test image and dangling containers"
    fi

    return "${status}"
}
