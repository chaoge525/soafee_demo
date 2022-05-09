# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

SUMMARY = "Cassini distro packages"
DESCRIPTION = "The list of packages included with Cassini distro by default"
PR = "r00"

inherit packagegroup

RDEPENDS:${PN} = "\
    bash \
    bash-completion-extra \
    ca-certificates \
    docker-ce \
    k3s-server \
    procps \
    sudo \
    wget \
    "
