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

inherit allarch
inherit ewaol_vm_config

DEPENDS += "gettext-native"

# Ewaol VM image recipe which generates VM disk image
EWAOL_VM_IMAGE_RECIPE ??= "ewaol-vm-image"

# Guest disk image type
EWAOL_VM_IMAGE_EXT = "wic.qcow2"
EWAOL_VM_DISK_IMG = "${EWAOL_VM_IMAGE_BASENAME}-${EWAOL_VM_MACHINE}.${EWAOL_VM_IMAGE_EXT}"
EWAOL_VM_DEPLOY_DIR = "${EWAOL_VM_TMPDIR}/deploy/images/${EWAOL_VM_MACHINE}"

EWAOL_VM_DATA = "${datadir}/vms"

# EWAOL_VM_*_SRC variables defines file paths within the build tree.
EWAOL_VM_CFG_SRC = "${WORKDIR}/ewaol-vm.conf.sample"
EWAOL_VM_DISK_SRC = "${EWAOL_VM_DEPLOY_DIR}/${EWAOL_VM_DISK_IMG}"
EWAOL_VM_KERNEL_SRC = "${EWAOL_VM_DEPLOY_DIR}/${EWAOL_VM_KERNEL_IMAGETYPE}"

EWAOL_VM_PACKAGE_EXTRA_DEPENDS ??= "mc::${EWAOL_VM_MC}:${EWAOL_VM_IMAGE_RECIPE}:do_image_complete"

do_configure[noexec] = "1"
do_compile[noexec] = "1"

do_install() {
    install -d ${D}${sysconfdir}/xen/auto

    for ewaol_vm_instance in $(seq 1 ${EWAOL_VM_INSTANCES})
    do
        VM_HOSTNAME=$(grep -oP "(?<=EWAOL_VM${ewaol_vm_instance}_HOSTNAME=\")[^\"]*" \
                      ${EWAOL_VM_DEPLOY_DIR}/${EWAOL_VM_IMAGE_BASENAME}.env)
        VM_MEMORY_SIZE=$(grep -oP "(?<=EWAOL_VM${ewaol_vm_instance}_MEMORY_SIZE=\")[^\"]*" \
                         ${EWAOL_VM_DEPLOY_DIR}/${EWAOL_VM_IMAGE_BASENAME}.env)
        VM_NUMBER_OF_CPUS=$(grep -oP "(?<=EWAOL_VM${ewaol_vm_instance}_NUMBER_OF_CPUS=\")[^\"]*" \
                           ${EWAOL_VM_DEPLOY_DIR}/${EWAOL_VM_IMAGE_BASENAME}.env)

        export EWAOL_VM_NUMBER_OF_CPUS="${VM_NUMBER_OF_CPUS}"
        export EWAOL_VM_MEMORY_SIZE="${VM_MEMORY_SIZE}"
        export EWAOL_VM_HOSTNAME=${VM_HOSTNAME}

        # EWAOL_VM_*_DST variables defines file destination paths on the host rootfs.
        export EWAOL_VM_KERNEL_DST=${EWAOL_VM_DATA}/${VM_HOSTNAME}/${EWAOL_VM_KERNEL_IMAGETYPE}
        export EWAOL_VM_DISK_DST=${EWAOL_VM_DATA}/${VM_HOSTNAME}/${EWAOL_VM_DISK_IMG}
        export EWAOL_VM_CFG_DST=${sysconfdir}/xen/auto/${VM_HOSTNAME}.cfg

        envsubst < ${EWAOL_VM_CFG_SRC} > ${D}${EWAOL_VM_CFG_DST}

        install -d ${D}${EWAOL_VM_DATA}/${VM_HOSTNAME}
        install -Dm 0644 ${EWAOL_VM_DISK_SRC} ${D}${EWAOL_VM_DISK_DST}
        install -Dm 0644 ${EWAOL_VM_KERNEL_SRC} ${D}${EWAOL_VM_KERNEL_DST}
    done
}

FILES:${PN} = "${datadir} ${sysconfdir}"

do_install[mcdepends] += "${EWAOL_VM_PACKAGE_EXTRA_DEPENDS}"
