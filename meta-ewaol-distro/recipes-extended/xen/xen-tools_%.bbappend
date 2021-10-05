# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

# This file contains a fix for xen kernel module automatic probbing during
# system boot. The directory "${systemd_unitdir}/modules-load.d/" is not
# considered by systemd-modules-load.service by default, so adding a
# symbolic link to a directory that this service reads files by default.

OVERRIDES:append = "${EWAOL_OVERRIDES}"

do_install:append:ewaol-virtualization() {
    install -d ${D}${nonarch_libdir}/modules-load.d
    ln -r -s ${D}${systemd_unitdir}/modules-load.d/xen.conf \
        ${D}${nonarch_libdir}/modules-load.d/xen.conf
}

FILES:${PN}-xencommons:append:ewaol-virtualization = " \
    ${nonarch_libdir}/modules-load.d/xen.conf"
