# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

# This class holds common variables and functions for
# runtime integration tests.

inherit ptest allarch

RDEPENDS:${PN}:append = " bats runtime-integration-tests-common"

DEPENDS:append = " gettext-native"

CASSINI_TEST_ACCOUNT ??= "test"
CASSINI_TEST_BATS_OPTIONS ?= "--show-output-of-passing-tests"

TEST_DIR = "${datadir}/${BPN}"
TEST_SUITE_NAME = "${BPN}"

SRC_URI = "${TEST_FILES} \
           file://run-test-suite \
           file://run-ptest.in"

ENVSUBST_VARS = "\$TEST_SUITE_NAME \
                 \$CASSINI_TEST_ACCOUNT \
                 \$TEST_DIR \
                 \$CASSINI_TEST_BATS_OPTIONS"

export TEST_SUITE_NAME
export CASSINI_TEST_ACCOUNT
export TEST_DIR
export CASSINI_TEST_BATS_OPTIONS

do_install[vardeps] += "\
    ENVSUBST_VARS \
    TEST_SUITE_NAME \
    CASSINI_TEST_ACCOUNT \
    TEST_DIR \
    CASSINI_TEST_BATS_OPTIONS \
    "

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

    additional_tests="$(find ${D}/${TEST_DIR} -maxdepth 1 \
                       -name *append-*.bats -printf "%f ")"

    for test in ${additional_tests}; do

        # Append the additional tests to the deployed test suite
        # Skip the first 2 lines to omit the shebang
        tail -n +3 "${D}/${TEST_DIR}/${test}" \
            >> "${D}/${TEST_DIR}/${TEST_SUITE_NAME}.bats"
        rm -fv "${D}/${TEST_DIR}/${test}"

    done
}
