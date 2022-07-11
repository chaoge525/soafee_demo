# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

OVERRIDES:append = "${EWAOL_OVERRIDES}"

XEN_TOOLS_PCI_PASSTHROUGH_REQUIRE ?= ""
XEN_TOOLS_PCI_PASSTHROUGH_REQUIRE:ewaol-virtualization = " \
        ${@bb.utils.contains('MACHINE_FEATURES', \
            'xen-pci-passthrough', \
            'xen-pci-passthrough.inc', '', d)}"

require ${XEN_TOOLS_PCI_PASSTHROUGH_REQUIRE}
