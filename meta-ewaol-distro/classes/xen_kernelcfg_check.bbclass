# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

inherit kernelcfg_check

# Current checksum, should be updated to track latest xen requirements
# http://git.yoctoproject.org/cgit/cgit.cgi/yocto-kernel-cache/tree/features/xen/xen.cfg
XEN_CONFIG_FILE ?= "xen.cfg"
XEN_CONFIG_FILE_MD5 ?= "1a3c770197a4c0c720b0ae1d73f4c090"

# List of XEN configs not valid or not wanted for aarch64 machines
XEN_CONFIG_IGNORE_LIST ?= "CONFIG_HYPERVISOR_GUEST \
                           CONFIG_XEN_PVHVM \
                           CONFIG_XEN_SAVE_RESTORE \
                           CONFIG_PCI_XEN \
                           CONFIG_XEN_PCIDEV_FRONTEND \
                           CONFIG_XEN_SCRUB_PAGES \
                           CONFIG_XEN_PCIDEV_BACKEND \
                           CONFIG_XEN_ACPI_PROCESSOR \
                           CONFIG_XEN_MCE_LOG \
                           CONFIG_XEN_HAVE_PVMMU \
                           CONFIG_XEN_PVCALLS_FRONTEND \
                           CONFIG_XEN_PVCALLS_BACKEND \
                          "

python do_xen_kernelcfg_check() {
    kernelcfg_check(d.getVar('XEN_CONFIG_FILE'), \
                    d.getVar('XEN_CONFIG_FILE_MD5'), d, \
                    d.getVar('XEN_CONFIG_IGNORE_LIST'))
}
addtask xen_kernelcfg_check before do_compile after do_configure
