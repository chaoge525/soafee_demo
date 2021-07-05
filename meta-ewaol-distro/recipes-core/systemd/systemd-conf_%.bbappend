# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS_prepend_ewaol := "${THISDIR}/files:"

SRC_URI_append_ewaol = " file://01-no-veth.conf"

do_install_append_ewaol() {
    if ${@bb.utils.contains('PACKAGECONFIG', 'dhcp-ethernet', 'true', 'false', d)}; then
        install -Dm 0644 ${WORKDIR}/01-no-veth.conf ${D}${sysconfdir}/systemd/network/80-wired.network.d/01-no-veth.conf
    fi
}

FILES_${PN}_append_ewaol = " ${sysconfdir}/systemd/"
