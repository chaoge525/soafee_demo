# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

inherit kernelcfg_check

# Current checksum, should be updated to track latest k3s requirements
# http://git.yoctoproject.org/cgit/cgit.cgi/meta-virtualization/tree/recipes-kernel/linux/linux-yocto/kubernetes.cfg
K3S_CONFIG_FILE ?= "kubernetes.cfg"
K3S_CONFIG_FILE_MD5 ?= "277cb1c977f7eb3fe8d85c767ebe0cce"

python do_k3s_kernelcfg_check() {
    kernelcfg_check(d, \
                    d.getVar('K3S_CONFIG_FILE'), \
                    d.getVar('K3S_CONFIG_FILE_MD5'))
}

addtask k3s_kernelcfg_check before do_compile after do_configure
