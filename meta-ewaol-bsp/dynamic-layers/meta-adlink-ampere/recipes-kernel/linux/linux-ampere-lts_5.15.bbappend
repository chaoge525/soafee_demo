# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

OVERRIDES:append = "${EWAOL_OVERRIDES}"
OVERRIDES:append:ewaol-virtualization = "${@bb.utils.contains('MACHINE_FEATURES', \
        'xen-pci-passthrough', \
        ':xen-pci-passthrough', '', d)}"

FILESEXTRAPATHS:prepend:xen-pci-passthrough := "${THISDIR}:${THISDIR}/files:"

KERNEL_FEATURES:append:xen-pci-passthrough = " features/ewaol/xen_pci_passthrough.scc"

SRC_URI:append:xen-pci-passthrough = " \
    file://ewaol-kmeta-extra;type=kmeta;name=ewaol-kmeta-extra;destsuffix=ewaol-kmeta-extra \
    file://0001-xen-pciback-make-xen-pciback-driver-workon-ARM.patch \
    "
