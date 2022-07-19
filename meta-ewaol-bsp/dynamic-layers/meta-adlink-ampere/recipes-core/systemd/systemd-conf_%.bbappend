# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# This file contains settings for additional ethernet interfaces based on
# the 'i40e' driver. This configuration inherits Yocto default 'wired.network'
# file, but is limited to impact only 'i40e' interfaces - 'enp1s0f*'.
# It sets the 'RequiredForOnline' parameter to 'no' to allow the correct online
# state report for the 'systemd-networkd-wait-online' service.
# Current configuration assumes network connection via ethernet interface based
# on 'igb' driver - 'enP4p4s0'.

OVERRIDES:append = "${EWAOL_OVERRIDES}"

I40E_NETWORK_OVERRIDE:ewaol = "true"
I40E_NETWORK_OVERRIDE:ewaol-virtualization = "${@bb.utils.contains('BB_CURRENT_MC', \
                                                'ewaol-guest-vm', \
                                                'false', 'true', d)}"

OVERRIDES:append:ewaol = "${@bb.utils.contains('I40E_NETWORK_OVERRIDE', \
                           'true', \
                           ':i40e-network-override', '', d)}"

I40E_NETWORK:i40e-network-override = "79-i40e.network"

do_install:append:i40e-network-override() {
        if ${@bb.utils.contains('PACKAGECONFIG', 'dhcp-ethernet', 'true', 'false', d)}; then
                install -D -m0644 ${WORKDIR}/wired.network \
                    ${D}${sysconfdir}/systemd/network/${I40E_NETWORK}
                cat <<-'EOF' >> ${D}${sysconfdir}/systemd/network/${I40E_NETWORK}

			[Match]
			Driver=i40e

			[Link]
			RequiredForOnline=no
			EOF
        fi
}

FILES:${PN}:append:i40e-network-override = " ${sysconfdir}/systemd/"
