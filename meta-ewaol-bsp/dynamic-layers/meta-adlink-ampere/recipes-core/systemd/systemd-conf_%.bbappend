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

I40E_NETWORK:ewaol = "79-i40e.network"

do_install:append:ewaol() {
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

FILES:${PN}:append:ewaol = " ${sysconfdir}/systemd/"
