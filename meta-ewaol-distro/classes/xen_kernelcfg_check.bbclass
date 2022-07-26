# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

inherit kernelcfg_check

# Current checksum, should be updated to track latest xen requirements
# https://git.yoctoproject.org/cgit/cgit.cgi/yocto-kernel-cache/tree/features/xen/xen.cfg
XEN_CONFIG_FILE ?= "xen.cfg"
XEN_CONFIG_FILE_MD5 ?= "3f6bb365f98587369f867daef6d0dac4"

# List of XEN configs not valid or not wanted for aarch64 machines
XEN_CONFIG_IGNORE_LIST ?= "\
                           CONFIG_XEN_HAVE_PVMMU \
                           CONFIG_XEN_PVCALLS_FRONTEND \
                           CONFIG_XEN_PVCALLS_BACKEND \
                          "

python do_xen_kernelcfg_check() {
    kernelcfg_check(d, \
                    d.getVar('XEN_CONFIG_FILE'), \
                    d.getVar('XEN_CONFIG_FILE_MD5'), \
                    d.getVar('XEN_CONFIG_IGNORE_LIST'))
}
addtask xen_kernelcfg_check before do_compile after do_configure
