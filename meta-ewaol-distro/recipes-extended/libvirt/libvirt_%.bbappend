# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

OVERRIDES:append = "${EWAOL_OVERRIDES}"

SYSTEMD_AUTO_ENABLE:${PN}-libvirtd:ewaol-virtualization = "disable"
