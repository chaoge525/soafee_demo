# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Extra machine settings for n1sdp

# We need to extent the wks search path to be able to find custom wks file
WKS_SEARCH_PATH:prepend := "${EWAOL_ARM_BSP_DYNAMIC_DIR}/wic:"
WKS_FILE = "ewaol-n1sdp-host-efidisk.wks.in"
GRUB_CFG_FILE ?= "${EWAOL_ARM_BSP_DYNAMIC_DIR}/wic/ewaol-n1sdp-host-grub.cfg"

# Select the extra files to be included in the boot partition
IMAGE_EFI_BOOT_FILES += "xen-n1sdp.efi;xen.efi"
IMAGE_EFI_BOOT_FILES += "n1sdp-single-chip-xen.dtb"

# '-mcpu=' and '-march=' conflicts for xen build
# lets not set '-march=' and let xen to overwrite '-mcpu='
TUNE_CCARGS:aarch64:pn-xen = ""

EWAOL_WIC_IMAGE_EXTRA_DEPENDS ??= ""
do_image_wic[depends] += "${EWAOL_WIC_IMAGE_EXTRA_DEPENDS}"
