# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Used to apply to config for different features of the EWAOL distro, based on
# the contents of DISTRO_FEATURES

# EWAOL_DISTRO_FEATURES is a list of available features.
EWAOL_DISTRO_FEATURES = "ewaol-devel ewaol-test"

# Default must be an item from EWAOL_DISTRO_FEATURES
EWAOL_DISTRO_FEATURES_DEFAULT ?= "ewaol-devel"

# Set EWAOL_DISTRO_FEATURES_FALLBACK to EWAOL_DISTRO_FEATURES_DEFAULT only if
# none of EWAOL_DISTRO_FEATURES are found in DISTRO_FEATURES.
EWAOL_DISTRO_FEATURES_FALLBACK := "${@\
bb.utils.contains_any('DISTRO_FEATURES', d.getVar('EWAOL_DISTRO_FEATURES'),\
'', d.getVar('EWAOL_DISTRO_FEATURES_DEFAULT'), d)}"

# Add EWAOL_DISTRO_FEATURES_FALLBACK to DISTRO_FEATURES, could be empty.
DISTRO_FEATURES_append = " ${EWAOL_DISTRO_FEATURES_FALLBACK}"

# Require inc file for development DISTRO_FEATURE
require ${@bb.utils.contains(\
'DISTRO_FEATURES','ewaol-devel','conf/distro/include/ewaol-devel.inc', '', d)}

# Require inc file for testing DISTRO_FEATURE
require ${@bb.utils.contains(\
'DISTRO_FEATURES','ewaol-test','conf/distro/include/ewaol-test.inc', '', d)}
