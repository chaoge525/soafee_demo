# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

inherit kernelcfg_check

# Current checksum, should be updated to track latest containers requirements
# http://git.yoctoproject.org/cgit/cgit.cgi/yocto-kernel-cache/tree/features/docker/docker.cfg
CONTAINERS_CONFIG_FILE ?= "docker.cfg"
CONTAINERS_CONFIG_FILE_MD5 ?= "ee014efe5fd4fd406db99e2cce9c0ae0"

python do_containers_kernelcfg_check() {
    kernelcfg_check(d, \
                    d.getVar('CONTAINERS_CONFIG_FILE'), \
                    d.getVar('CONTAINERS_CONFIG_FILE_MD5'))
}

addtask containers_kernelcfg_check before do_compile after do_configure
