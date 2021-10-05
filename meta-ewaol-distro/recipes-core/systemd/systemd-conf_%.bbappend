# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

# This file includes host network configuration responsible for creating
# a network bridge to share the host eth physical interface with the guests
# virtual interfaces (vif) in bridged mode.

OVERRIDES:append = "${EWAOL_OVERRIDES}"

FILESEXTRAPATHS:prepend:ewaol-virtualization := "${THISDIR}/files:"

NETWORK_CONF_FILE:ewaol-virtualization = "01-no-vif.conf"
XENBR_NETWORK:ewaol-virtualization = "xenbr0.network"
XENBR_NETDEV:ewaol-virtualization = "xenbr0.netdev"

SRC_URI:append:ewaol-virtualization = "\
                                       file://${NETWORK_CONF_FILE} \
                                       file://${XENBR_NETWORK} \
                                       file://${XENBR_NETDEV} \
                                       "

do_install:append:ewaol-virtualization() {
    if ${@bb.utils.contains('PACKAGECONFIG', 'dhcp-ethernet', 'true', 'false', d)}; then
            NETWORK_CONF_DIR="${sysconfdir}/systemd/network/80-wired.network.d"
            install -Dm 0644 ${WORKDIR}/${NETWORK_CONF_FILE} \
                ${D}${NETWORK_CONF_DIR}/${NETWORK_CONF_FILE}
    fi

    install -Dm 0644 ${WORKDIR}/${XENBR_NETDEV} \
        ${D}${sysconfdir}/systemd/network/${XENBR_NETDEV}
    install -Dm 0644 ${WORKDIR}/${XENBR_NETWORK} \
        ${D}${sysconfdir}/systemd/network/${XENBR_NETWORK}
}

FILES:${PN}:append:ewaol-virtualization = " ${sysconfdir}/systemd/"
