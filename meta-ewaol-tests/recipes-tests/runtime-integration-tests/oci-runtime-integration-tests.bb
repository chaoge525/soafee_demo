# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "OCI runtime integration tests."
DESCRIPTION = "Integration tests for the OCI runtime subsystem \
               (Docker/Podman). Tests may be run standalone via \
               run-oci-runtime-integration-tests, or via the ptest framework \
               using ptest-runner."

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

TEST_FILES = "file://oci-runtime-integration-tests.bats \
              file://oci-runtime-funcs.sh \
              file://integration-tests-common-funcs.sh"

SRC_URI = "${TEST_FILES} \
           file://run-oci-runtime-integration-tests \
           file://run-ptest"

inherit ptest

RDEPENDS_${PN} += "bats"

# ptest aborts if it cannot find libgcc for pthread_cancel
RDEPENDS_${PN}-ptest += "libgcc"

TEST_DIR ?= "${datadir}/${BPN}"

do_install() {

    install -d "${D}/${TEST_DIR}"

    test_files=`echo ${TEST_FILES} | sed 's/file:\/\///g'`

    for test_file in ${test_files}; do
        install "${WORKDIR}/${test_file}" "${D}/${TEST_DIR}"
    done

    install -m 755 "${WORKDIR}/run-oci-runtime-integration-tests" "${D}/${TEST_DIR}"

}

do_install_ptest() {

    # Point the deployed run-ptest script to the test suite install directory
    # Use '#' as delimiter for sed as we are replacing with a path

    sed -i "s#%TESTDIR%#${TEST_DIR}#g" ${D}${PTEST_PATH}/run-ptest

}
