# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# config specifc to the ewaol-virtualization distro feature, enabled using
# DISTRO_FEATURES

EWAOL_OVERRIDES:append = ":ewaol-virtualization"

DISTRO_FEATURES:append = " xen"

IMAGE_FEATURES:append = " debug-tweaks"

EWAOL_VM_HOSTNAME ?= "ewaol-vm"
EWAOL_VM_IMAGE_RECIPE ?= "ewaol-vm-image"
EWAOL_VM_MACHINE ??= "generic-arm64"

# Guest multiconfig build configuration file basename without the ".conf"
# suffix.
EWAOL_VM_MC ??= "ewaol-vm"

EWAOL_HOST_MEMORY_SIZE ?= "2048"

KERNEL_CLASSES:append = " xen_kernelcfg_check"
