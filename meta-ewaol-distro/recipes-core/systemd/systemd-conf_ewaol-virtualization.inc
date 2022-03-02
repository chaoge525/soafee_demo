# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# This file includes network configuration responsible for creating a network
# bridge to share the Control VM eth interface with the Guest VM virtual
# interfaces (vif) in bridged mode.

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

NETWORK_CONF_FILE = "01-no-vif.conf"
XENBR_NETWORK = "xenbr0.network"
XENBR_NETDEV = "xenbr0.netdev"

SRC_URI:append= "\
                 file://${NETWORK_CONF_FILE} \
                 file://${XENBR_NETWORK} \
                 file://${XENBR_NETDEV} \
                 "

do_install:append() {
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

FILES:${PN}:append = " ${sysconfdir}/systemd/"
