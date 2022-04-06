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

TEST_SUITE_NAME = "k3s-integration-tests"
TEST_SUITE_PREFIX = "K3S"

TEST_FILES = "file://k3s-integration-tests.bats \
              file://k3s-funcs.sh \
              file://k3s-test-deployment.yaml \
              file://integration-tests-common-funcs.sh"

TEST_FILES:append:ewaol-virtualization = " \
    file://integration-tests-common-virtual-funcs.sh \
    file://login-console-funcs.expect \
    file://run-command.expect \
    file://k3s-virtualization-funcs.sh \
    "

SRC_URI = "${TEST_FILES} \
           file://run-test-suite \
           file://run-ptest"

require runtime-integration-tests.inc

RDEPENDS:${PN}:ewaol-virtualization += "expect"

K3S_TEST_DESC = "local deployment of K3s pods"
K3S_TEST_DESC:ewaol-virtualization = "remote deployment of K3s pods on the Guest VM, from the Control VM"

do_install:append() {
    # Append a more informative architecture-specific description of the K3s
    # test scenario
    sed -i "s#%K3S_TEST_DESC%#${K3S_TEST_DESC}#g" \
        "${D}/${TEST_DIR}/k3s-integration-tests.bats"
}

do_install:append:ewaol-virtualization() {

    # Load virtualization-specific overrides to the K3s functions
    sed -i "s#load k3s-funcs.sh#load k3s-funcs.sh\nload k3s-virtualization-funcs.sh#g" \
        "${D}/${TEST_DIR}/k3s-integration-tests.bats"

    # Set the hostname of the Guest VM that should run the workload
    sed -i "s#%GUESTNAME%#${EWAOL_GUEST_VM_HOSTNAME}#g" \
        "${D}/${TEST_DIR}/k3s-virtualization-funcs.sh"

    # Add a condition to the deployment to make it only schedulable on the Guest
    # VM
    cat << EOF >> ${D}/${TEST_DIR}/k3s-test-deployment.yaml
      nodeSelector:
        ewaol.node-type: guest-vm
EOF

}
