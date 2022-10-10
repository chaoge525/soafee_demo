# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

OVERRIDES:append = "${EWAOL_OVERRIDES}"
OVERRIDES:append:ewaol-virtualization = "${@bb.utils.contains('MACHINE_FEATURES', \
            'xen-pci-passthrough', \
            ':xen-pci-passthrough', '', d)}"

XEN_PCI_PASSTHROUGH_REQUIRE ?= ""
XEN_PCI_PASSTHROUGH_REQUIRE:xen-pci-passthrough = "xen-pci-passthrough.inc"

require ${XEN_PCI_PASSTHROUGH_REQUIRE}

# Only inherit ewaol_guest_vm_config if building EWAOL Guest VM(s)
inherit ${@ oe.utils.vartrue('BUILD_EWAOL_GUEST_VM', 'ewaol_guest_vm_config', '', d)}

do_deploy:prepend:xen-pci-passthrough (){

    if [ -n "${EWAOL_PCI_PASSTHROUGH_DEVICES_XEN_FORMAT}" ]; then
        export EWAOL_PCI_PASSTHROUGH_DEVICES_KERNEL_OPT="xen-pciback.hide=${EWAOL_PCI_PASSTHROUGH_DEVICES_XEN_FORMAT}"
    else
        export EWAOL_PCI_PASSTHROUGH_DEVICES_KERNEL_OPT=""
    fi

}
