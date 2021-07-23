#!/usr/bin/env bash
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

apply_workload() {
    kubectl apply -f "${1}"  2>"${TEST_STDERR_FILE}"
}

query_kubectl() {
    kubectl get "${1}" "${2}" -o jsonpath="${3}" 2>"${TEST_STDERR_FILE}"
}

kubectl_wait() {
    kubectl wait --for=condition="${3}" "${1}" "${2}" 2>"${TEST_STDERR_FILE}"
}

kubectl_delete() {
    kubectl delete "${1}" "${2}" 2>"${TEST_STDERR_FILE}"
}

kubectl_set() {
    kubectl set "${1}" "${2}" "${3}" 2>"${TEST_STDERR_FILE}"
}

kubectl_expose_deployment() {
    kubectl expose deployment "${1}" --name="${2}" 2>"${TEST_STDERR_FILE}"
}

systemd_service() {
    systemctl "${1}" k3s 2>"${TEST_STDERR_FILE}"
}

update_server_arguments_and_restart() {
    mkdir -p /lib/systemd/system/k3s.service.d
    cat << EOF > /lib/systemd/system/k3s.service.d/test-override.conf
[Service]
ExecStart=
ExecStart=/usr/local/bin/k3s server ${1}
EOF
    systemctl daemon-reload 2>"${TEST_STDERR_FILE}"
    systemctl restart k3s 2>>"${TEST_STDERR_FILE}"
}

get_from_url() {
    timeout 10 wget -O - "${1}:${2}" 2>"${TEST_STDERR_FILE}"
}
