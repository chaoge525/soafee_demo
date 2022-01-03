# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:prepend:ewaol := "${THISDIR}/files:"

SRC_URI:append:ewaol = " file://ewaol_admin_group.in"

DEPENDS:append:ewaol = " gettext-native"

do_install:append:ewaol() {

    export ADMIN_GROUP="${EWAOL_ADMIN_GROUP}"
    export ADMIN_GROUP_OPTIONS="${EWAOL_ADMIN_GROUP_OPTIONS}"

    envsubst < ${WORKDIR}/ewaol_admin_group.in > ${D}${sysconfdir}/sudoers.d/ewaol_admin_group
    chmod 644 ${D}${sysconfdir}/sudoers.d/ewaol_admin_group
}
