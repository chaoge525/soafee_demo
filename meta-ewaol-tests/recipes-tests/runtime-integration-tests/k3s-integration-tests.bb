# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "K3s container orchestration integration tests."
DESCRIPTION = "Integration tests for the K3s container orchestration system. \
               Tests may be run standalone via \
               run-k3s-integration-tests, or via the ptest \
               framework using ptest-runner."

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

OVERRIDES:append = "${EWAOL_OVERRIDES}"

TEST_FILES = "file://k3s-integration-tests.bats \
              file://k3s-funcs.sh \
              file://k3s-test-deployment.yaml"

TEST_FILES:append:ewaol-virtualization = " \
    file://k3s-append-virtualization.bats \
    file://k3s-virtualization-funcs.sh \
    "

TEST_FILES:append:ewaol-security = " \
    file://k3s-append-security.bats \
    file://k3s-security-funcs.sh \
    "

inherit runtime-integration-tests
require runtime-integration-tests.inc

K3S_TEST_TYPE = "local deployment"
K3S_TEST_TYPE:ewaol-virtualization = "remote deployment on Guest VMs"
export K3S_TEST_TYPE

ENVSUBST_VARS:append = " \$K3S_TEST_TYPE"

do_install[vardeps] += "\
    K3S_TEST_TYPE \
    "

do_install:append:ewaol-virtualization() {

    # Add a condition to the deployment to make it only schedulable on the Guest
    # VM
    cat << EOF >> ${D}/${TEST_DIR}/k3s-test-deployment.yaml
      nodeSelector:
        ewaol.node-type: guest-vm
EOF
}
