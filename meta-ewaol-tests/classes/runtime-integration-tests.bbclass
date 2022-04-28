# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# This class holds common variables and functions for
# runtime integration tests.

inherit ptest allarch

RDEPENDS:${PN}:append = " bats runtime-integration-tests-common"

DEPENDS:append = " gettext-native"

# ptest aborts if it cannot find libgcc for pthread_cancel
RDEPENDS:${PN}-ptest += "libgcc"

EWAOL_TEST_ACCOUNT ??= "test"

TEST_DIR = "${datadir}/${BPN}"
TEST_SUITE_NAME = "${BPN}"

SRC_URI = "${TEST_FILES} \
           file://run-test-suite \
           file://run-ptest.in"

ENVSUBST_VARS = "\$TEST_SUITE_NAME \
                 \$EWAOL_TEST_ACCOUNT \
                 \$TEST_DIR \
                 \$EWAOL_GUEST_VM_HOSTNAME"

export TEST_SUITE_NAME
export EWAOL_TEST_ACCOUNT
export TEST_DIR
export EWAOL_GUEST_VM_HOSTNAME

do_install() {

    install -d "${D}/${TEST_DIR}"

    test_files=`echo ${TEST_FILES} | sed 's/file:\/\///g'`

    for test_file in ${test_files}; do
        envsubst "${ENVSUBST_VARS}" < "${WORKDIR}/${test_file}" \
            > "${D}/${TEST_DIR}/${test_file}"
    done

    envsubst "${ENVSUBST_VARS}" < "${WORKDIR}/run-test-suite" \
        > "${D}/${TEST_DIR}/run-${TEST_SUITE_NAME}"

    chmod +x "${D}/${TEST_DIR}/run-${TEST_SUITE_NAME}"

    envsubst "${ENVSUBST_VARS}" < "${WORKDIR}/run-ptest.in" \
        > "${WORKDIR}/run-ptest"

    additional_tests="$(find "${WORKDIR}" -maxdepth 1 \
                       -name *append-*.bats -printf "%f ")"


    for test in ${additional_tests}; do
        # Append the additional tests to the deployed test suite
        # Skip the first 2 lines to omit the shebang
        tail -n +3 "${D}/${TEST_DIR}/${test}" \
            >> "${D}/${TEST_DIR}/${TEST_SUITE_NAME}.bats"
        rm -fv "${D}/${TEST_DIR}/${test}"
    done
}
