# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

SUMMARY = "This recipe packages the VM configuration and disk image generated \
           in EWAOL_VM_IMAGE_RECIPE recipe to be installed on host rootfs"

LICENSE = "MIT"
LIC_FILES_CHKSUM = "\
    file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302 \
    "

inherit features_check
REQUIRED_DISTRO_FEATURES += "ewaol-virtualization"

EWAOL_VM_IMAGE_RECIPE ??= "ewaol-vm-image"

DEPENDS += "${EWAOL_VM_IMAGE_RECIPE}"

EWAOL_VM_IMAGE_EXT = "wic.qcow2"
EWAOL_VM_DIR = "/vms"
EWAOL_VM_DISK_IMG = "${EWAOL_VM_IMAGE_RECIPE}-${MACHINE}.${EWAOL_VM_IMAGE_EXT}"

EWAOL_VM_MEMORY_SIZE ?= "6144"
EWAOL_VM_NUMBER_OF_CPUS ?= "4"

do_install() {
    install -d ${D}${sysconfdir}/xen/auto
    cat <<EOF >> ${D}${sysconfdir}/xen/auto/${EWAOL_VM_HOSTNAME}.cfg
name = "${EWAOL_VM_HOSTNAME}"
memory = ${EWAOL_VM_MEMORY_SIZE}
vcpus = ${EWAOL_VM_NUMBER_OF_CPUS}
extra = " earlyprintk=xenboot console=hvc0 rw"
root = "/dev/xvda1"
kernel = "/boot/Image"
disk = ['format=qcow2, vdev=xvda, access=rw, backendtype=qdisk, \
target=${datadir}${EWAOL_VM_DIR}/${EWAOL_VM_DISK_IMG}']
vif = ['script=vif-bridge,bridge=xenbr0']
EOF

    install -d ${D}${datadir}${EWAOL_VM_DIR}
    install -Dm 0644 ${DEPLOY_DIR_IMAGE}/${EWAOL_VM_DISK_IMG} \
        ${D}${datadir}${EWAOL_VM_DIR}/${EWAOL_VM_DISK_IMG}
}

do_install[depends] += "${EWAOL_VM_IMAGE_RECIPE}:do_image_complete"
FILES:${PN} = "${datadir} ${sysconfdir}"
