# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "This recipe packages the VM configuration and disk image generated \
           in EWAOL_VM_IMAGE_RECIPE recipe to be installed on host rootfs"

LICENSE = "MIT"
LIC_FILES_CHKSUM = "\
    file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302 \
    "

SRC_URI = "file://ewaol-vm.conf.sample"

inherit features_check
REQUIRED_DISTRO_FEATURES += "ewaol-virtualization"

DEPENDS += "gettext-native"

# Ewaol VM image recipe which generates VM disk image
EWAOL_VM_IMAGE_RECIPE ??= "ewaol-vm-image"

# Guest disk image type
EWAOL_VM_IMAGE_EXT = "wic.qcow2"

EWAOL_VM_DISK_IMG = "${EWAOL_VM_IMAGE_RECIPE}-${EWAOL_VM_MACHINE}.${EWAOL_VM_IMAGE_EXT}"
EWAOL_VM_DEPLOY_DIR = "${EWAOL_VM_TMPDIR}/deploy/images/${EWAOL_VM_MACHINE}"

EWAOL_VM_DATA = "${datadir}/vms"

# EWAOL_VM_*_PATH variables defines file destination paths on the host rootfs.
EWAOL_VM_CFG_PATH = "${sysconfdir}/xen/auto/${EWAOL_VM_HOSTNAME}.cfg"
EWAOL_VM_DISK_PATH = "${EWAOL_VM_DATA}/${EWAOL_VM_DISK_IMG}"
EWAOL_VM_KERNEL_PATH = "${EWAOL_VM_DATA}/${EWAOL_VM_KERNEL_IMAGETYPE}"

# EWAOL_VM_*_SRC variables defines file paths within the build tree.
EWAOL_VM_CFG_SRC = "${WORKDIR}/ewaol-vm.conf.sample"
EWAOL_VM_DISK_SRC = "${EWAOL_VM_DEPLOY_DIR}/${EWAOL_VM_DISK_IMG}"
EWAOL_VM_KERNEL_SRC = "${EWAOL_VM_DEPLOY_DIR}/${EWAOL_VM_KERNEL_IMAGETYPE}"

EWAOL_VM_PACKAGE_EXTRA_DEPENDS ??= "mc::${EWAOL_VM_MC}:${EWAOL_VM_IMAGE_RECIPE}:do_image_complete"

do_install() {
    install -d ${D}${sysconfdir}/xen/auto

    export EWAOL_VM_HOSTNAME=${EWAOL_VM_HOSTNAME}
    export EWAOL_VM_MEMORY_SIZE=${EWAOL_VM_MEMORY_SIZE}
    export EWAOL_VM_NUMBER_OF_CPUS=${EWAOL_VM_NUMBER_OF_CPUS}
    export EWAOL_VM_KERNEL_PATH=${EWAOL_VM_KERNEL_PATH}
    export EWAOL_VM_DISK_PATH=${EWAOL_VM_DISK_PATH}

    envsubst < ${EWAOL_VM_CFG_SRC} > ${D}${EWAOL_VM_CFG_PATH}

    install -d ${D}${EWAOL_VM_DATA}
    install -Dm 0644 ${EWAOL_VM_DISK_SRC} ${D}${EWAOL_VM_DISK_PATH}
    install -Dm 0644 ${EWAOL_VM_KERNEL_SRC} ${D}${EWAOL_VM_KERNEL_PATH}
}

FILES:${PN} = "${datadir} ${sysconfdir}"

do_install[mcdepends] += "${EWAOL_VM_PACKAGE_EXTRA_DEPENDS}"
