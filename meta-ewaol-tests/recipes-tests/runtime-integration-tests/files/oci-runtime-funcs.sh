#!/usr/bin/env bash

# Arg1: Image name
# Returns 0 if image exists
# Returns 1 if image does not exist
does_image_exist() {
    if [ "$(docker images 2>"${OCI_TEST_STDERR_FILE}" | grep -c "${1}")" -eq 1 ]; then
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
    docker image rm "${1}" --force 2>"${OCI_TEST_STDERR_FILE}"
}

# Arg1: Image name
# Arg2: Command to execute in container
# Returns exit code of the run command
# STDOUT is the container ID
container_run_persistent() {

    image_name="${1}"
    container_cmd="${*:2}"

    # shellcheck disable=SC2086
    docker run -it -d "${image_name}" ${container_cmd} 2>"${OCI_TEST_STDERR_FILE}"
}

# Arg1: Container ID
# Returns state.exitcode from the container inspect
# STDOUT is the state.status from the container inspect
check_container_state() {

    container_id="${1}"

    inspect_output=$(docker inspect -f '{{.State.Status}},{{.State.ExitCode}}' "${container_id}" 2>"${OCI_TEST_STDERR_FILE}" )
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
# Returns exit code of the container stop command
container_stop() {

    container_id="${1}"

    docker container stop "${container_id}" 2>"${OCI_TEST_STDERR_FILE}"
}

# Arg1: Container ID
# Returns exit code of the container rm command
container_remove() {

    container_id="$1"

    docker container rm "${container_id}" --force 2>"${OCI_TEST_STDERR_FILE}"
}

# Arg1: Image name
# STDOUT are the running container IDs for the image
get_running_containers() {

    image_name="${1}"

    docker ps -q --filter ancestor="${image_name}" 2>"${OCI_TEST_STDERR_FILE}"
}
