# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "Creates an 'EWAOL_TEST_ACCOUNT' account used for running EWAOL \
           runtime integration tests"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"

# Default values, used only if 'meta-ewaol-distro/conf/distro/ewaol.conf'
# is skipped.
EWAOL_TEST_ACCOUNT ??= "test"
EWAOL_ADMIN_GROUP ??= "sudo"

# Comma separated list of groups for 'EWAOL_TEST_ACCOUNT' user
EWAOL_TEST_GROUPS = "${EWAOL_ADMIN_GROUP}"

inherit allarch useradd

USERADD_PACKAGES = "${PN}"
USERADD_PARAM:${PN} = "--create-home \
                       --password '' \
                       --groups ${EWAOL_TEST_GROUPS} \
                       --user-group ${EWAOL_TEST_ACCOUNT};"

ALLOW_EMPTY:${PN} = "1"

do_fetch[noexec] = "1"
do_unpack[noexec] = "1"
do_patch[noexec] = "1"
do_configure[noexec] = "1"
do_compile[noexec] = "1"
do_install[noexec] = "1"
