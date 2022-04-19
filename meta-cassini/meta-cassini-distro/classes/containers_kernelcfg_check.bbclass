# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

inherit kernelcfg_check

# Current checksum, should be updated to track latest containers requirements
# http://git.yoctoproject.org/cgit/cgit.cgi/yocto-kernel-cache/tree/features/docker/docker.cfg
CONTAINERS_CONFIG_FILE ?= "docker.cfg"
CONTAINERS_CONFIG_FILE_MD5 ?= "61e59db3a77cea4b81320305144e9de5"

python do_containers_kernelcfg_check() {
    kernelcfg_check(d, \
                    d.getVar('CONTAINERS_CONFIG_FILE'), \
                    d.getVar('CONTAINERS_CONFIG_FILE_MD5'))
}

addtask containers_kernelcfg_check before do_compile after do_configure
