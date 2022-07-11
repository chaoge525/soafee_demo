# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

OVERRIDES:append = "${EWAOL_OVERRIDES}"
OVERRIDES:append:ewaol-virtualization = "${@bb.utils.contains('MACHINE_FEATURES', \
        'xen-pci-passthrough', \
        bb.utils.contains('BB_CURRENT_MC', \
                'ewaol-guest-vm', \
                ':xen-pci-passthrough-guest-vm', '', d), \
        '', d)}"

FILESEXTRAPATHS:prepend:xen-pci-passthrough-guest-vm := "${THISDIR}:"

KERNEL_FEATURES:append:xen-pci-passthrough-guest-vm = " \
    features/ewaol/i40e_driver.scc \
    "

SRC_URI:append:xen-pci-passthrough-guest-vm = " \
    file://ewaol-kmeta-extra;type=kmeta;name=ewaol-kmeta-extra;destsuffix=ewaol-kmeta-extra \
    "
