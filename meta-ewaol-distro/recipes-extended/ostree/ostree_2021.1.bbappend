# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# The unauthenticated git protocol on port 9418 is no longer supported in github.
# In this case we need to pass ';protocol=https' in SRC_URI
# Change based on https://cgit.openembedded.org/meta-openembedded/commit/meta-oe/recipes-extended/ostree/ostree_2021.1.bb?h=hardknott&id=7fbb2767186a4db729efe4f440cc9a992f2ab183
SRC_URI = " \
    gitsm://github.com/ostreedev/ostree;branch=main;protocol=https \
    file://run-ptest \
"
