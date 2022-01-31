# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Upstream project source code moved from master to main branch
# Change based on https://git.yoctoproject.org/meta-virtualization/commit/?h=hardknott&id=724e26aaab925372c89080669256feab2d639b05
SRC_URI = " \
    git://github.com/opencontainers/runc;branch=main \
    file://0001-Makefile-respect-GOBUILDFLAGS-for-runc-and-remove-re.patch \
    "
