# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

# Used to apply to config for different features of the CASSINI distro, based on
# the contents of DISTRO_FEATURES

# CASSINI_DISTRO_FEATURES is a list of available features.
CASSINI_DISTRO_FEATURES = " \
                         cassini-devel \
                         cassini-test \
                         cassini-sdk \
                         cassini-security \
                         "

# Default must be an item from CASSINI_DISTRO_FEATURES
CASSINI_DISTRO_FEATURES_DEFAULT ?= "cassini-devel"

# Set CASSINI_DISTRO_FEATURES_FALLBACK to CASSINI_DISTRO_FEATURES_DEFAULT only if
# none of CASSINI_DISTRO_FEATURES are found in DISTRO_FEATURES.
CASSINI_DISTRO_FEATURES_FALLBACK := "${@\
bb.utils.contains_any('DISTRO_FEATURES', d.getVar('CASSINI_DISTRO_FEATURES'),\
'', d.getVar('CASSINI_DISTRO_FEATURES_DEFAULT'), d)}"

# Add CASSINI_DISTRO_FEATURES_FALLBACK to DISTRO_FEATURES, could be empty.
DISTRO_FEATURES:append = " ${CASSINI_DISTRO_FEATURES_FALLBACK}"

# Require inc file for development DISTRO_FEATURE
require ${@bb.utils.contains(\
'DISTRO_FEATURES','cassini-devel','conf/distro/include/cassini-devel.inc', '', d)}

# Require inc file for testing DISTRO_FEATURE
require ${@bb.utils.contains(\
'DISTRO_FEATURES','cassini-test','conf/distro/include/cassini-test.inc', '', d)}

# Require inc file for sdk DISTRO_FEATURE
require ${@bb.utils.contains(\
'DISTRO_FEATURES','cassini-sdk','conf/distro/include/cassini-sdk.inc', '', d)}

# Require inc file for security DISTRO_FEATURE
require ${@bb.utils.contains(\
'DISTRO_FEATURES','cassini-security',\
'conf/distro/include/cassini-security.inc', '', d)}
