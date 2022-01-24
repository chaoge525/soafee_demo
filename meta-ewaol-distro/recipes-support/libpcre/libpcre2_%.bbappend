# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Upstream project is not hosting the source code in ftp.pcre.org anymore.
# Change based on https://git.yoctoproject.org/poky/commit/meta/recipes-support/libpcre?h=hardknott&id=7c58687a402a1622921963a089995471ec5c4348
SRC_URI = "https://github.com/PhilipHazel/pcre2/releases/download/pcre2-${PV}/pcre2-${PV}.tar.bz2"

UPSTREAM_CHECK_URI = "https://github.com/PhilipHazel/pcre2/releases"
