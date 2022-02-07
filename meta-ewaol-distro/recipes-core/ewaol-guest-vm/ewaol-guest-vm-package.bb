# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "This recipe packages the Guest VM configuration, kernel and disk \
           image generated in EWAOL_GUEST_VM_IMAGE_RECIPE recipe to be \
           installed on the virtualization image"

LICENSE = "MIT"
LIC_FILES_CHKSUM = "\
    file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302 \
    "

SRC_URI = "file://ewaol-guest-vm.conf.sample"

inherit features_check
REQUIRED_DISTRO_FEATURES += "ewaol-virtualization"

inherit allarch
inherit ewaol_guest_vm_config

DEPENDS += "gettext-native"

# EWAOL Guest VM image recipe which generates Guest VM disk image
EWAOL_GUEST_VM_IMAGE_RECIPE ??= "ewaol-guest-vm-image"

# Guest VM disk image type
EWAOL_GUEST_VM_IMAGE_EXT = "wic.qcow2"
EWAOL_GUEST_VM_DISK_IMG = "${EWAOL_GUEST_VM_IMAGE_BASENAME}-${EWAOL_GUEST_VM_MACHINE}.${EWAOL_GUEST_VM_IMAGE_EXT}"
EWAOL_GUEST_VM_DEPLOY_DIR = "${EWAOL_GUEST_VM_TMPDIR}/deploy/images/${EWAOL_GUEST_VM_MACHINE}"

EWAOL_GUEST_VM_DATA = "${datadir}/guest-vms"

# EWAOL_GUEST_VM_*_SRC variables defines file paths within the build tree.
EWAOL_GUEST_VM_CFG_SRC = "${WORKDIR}/ewaol-guest-vm.conf.sample"
EWAOL_GUEST_VM_DISK_SRC = "${EWAOL_GUEST_VM_DEPLOY_DIR}/${EWAOL_GUEST_VM_DISK_IMG}"
EWAOL_GUEST_VM_KERNEL_SRC = "${EWAOL_GUEST_VM_DEPLOY_DIR}/${EWAOL_GUEST_VM_KERNEL_IMAGETYPE}"

EWAOL_GUEST_VM_PACKAGE_EXTRA_DEPENDS ??= "mc::${EWAOL_GUEST_VM_MC}:${EWAOL_GUEST_VM_IMAGE_RECIPE}:do_image_complete"

do_configure[noexec] = "1"
do_compile[noexec] = "1"

do_install() {
    install -d ${D}${sysconfdir}/xen/auto

    for ewaol_guest_vm_instance in $(seq 1 ${EWAOL_GUEST_VM_INSTANCES})
    do
        GUEST_VM_HOSTNAME=$(grep -oP "(?<=EWAOL_GUEST_VM${ewaol_guest_vm_instance}_HOSTNAME=\")[^\"]*" \
                      ${EWAOL_GUEST_VM_DEPLOY_DIR}/${EWAOL_GUEST_VM_IMAGE_BASENAME}.env)
        GUEST_VM_MEMORY_SIZE=$(grep -oP "(?<=EWAOL_GUEST_VM${ewaol_guest_vm_instance}_MEMORY_SIZE=\")[^\"]*" \
                         ${EWAOL_GUEST_VM_DEPLOY_DIR}/${EWAOL_GUEST_VM_IMAGE_BASENAME}.env)
        GUEST_VM_NUMBER_OF_CPUS=$(grep -oP "(?<=EWAOL_GUEST_VM${ewaol_guest_vm_instance}_NUMBER_OF_CPUS=\")[^\"]*" \
                           ${EWAOL_GUEST_VM_DEPLOY_DIR}/${EWAOL_GUEST_VM_IMAGE_BASENAME}.env)

        export EWAOL_GUEST_VM_NUMBER_OF_CPUS="${GUEST_VM_NUMBER_OF_CPUS}"
        export EWAOL_GUEST_VM_MEMORY_SIZE="${GUEST_VM_MEMORY_SIZE}"
        export EWAOL_GUEST_VM_HOSTNAME=${GUEST_VM_HOSTNAME}

        # EWAOL_GUEST_VM_*_DST variables defines file destination paths on the host rootfs.
        export EWAOL_GUEST_VM_KERNEL_DST=${EWAOL_GUEST_VM_DATA}/${GUEST_VM_HOSTNAME}/${EWAOL_GUEST_VM_KERNEL_IMAGETYPE}
        export EWAOL_GUEST_VM_DISK_DST=${EWAOL_GUEST_VM_DATA}/${GUEST_VM_HOSTNAME}/${EWAOL_GUEST_VM_DISK_IMG}
        export EWAOL_GUEST_VM_CFG_DST=${sysconfdir}/xen/auto/${GUEST_VM_HOSTNAME}.cfg

        envsubst < ${EWAOL_GUEST_VM_CFG_SRC} > ${D}${EWAOL_GUEST_VM_CFG_DST}

        install -d ${D}${EWAOL_GUEST_VM_DATA}/${GUEST_VM_HOSTNAME}
        install -Dm 0644 ${EWAOL_GUEST_VM_DISK_SRC} ${D}${EWAOL_GUEST_VM_DISK_DST}
        install -Dm 0644 ${EWAOL_GUEST_VM_KERNEL_SRC} ${D}${EWAOL_GUEST_VM_KERNEL_DST}
    done
}

FILES:${PN} = "${datadir} ${sysconfdir}"

do_install[mcdepends] += "${EWAOL_GUEST_VM_PACKAGE_EXTRA_DEPENDS}"
