# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Upstream project is not hosting the source code in ftp.pcre.org anymore.
# Change based on https://git.yoctoproject.org/poky/commit/meta/recipes-support/libpcre?h=hardknott&id=7c58687a402a1622921963a089995471ec5c4348
SRC_URI = "${SOURCEFORGE_MIRROR}/pcre/pcre-${PV}.tar.bz2 \
            file://run-ptest \
            file://Makefile \
            "
