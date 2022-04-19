# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:prepend:cassini := "${THISDIR}/files:"

SRC_URI:append:cassini = " file://cassini_admin_group.in"

DEPENDS:append:cassini = " gettext-native"

do_install:append:cassini() {

    export ADMIN_GROUP="${CASSINI_ADMIN_GROUP}"
    export ADMIN_GROUP_OPTIONS="${CASSINI_ADMIN_GROUP_OPTIONS}"

    envsubst < ${WORKDIR}/cassini_admin_group.in > ${D}${sysconfdir}/sudoers.d/cassini_admin_group
    chmod 644 ${D}${sysconfdir}/sudoers.d/cassini_admin_group
}
