# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

# This recipe can be used to modify one or several DTBS to add
# entries required to declare and boot Linux as Dom0 from Xen

LICENSE = "MIT"
LIC_FILES_CHKSUM = "\
    file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302 \
    "

S = "${WORKDIR}"

DESCRIPTION = "Add entries in DTB for Xen and Dom0"
COMPATIBLE_MACHINE = "n1sdp"

XEN_DEVICETREE_DEPEND ?= "virtual/trusted-firmware-a:do_deploy"
XEN_DEVICETREE_DTBS ?= "n1sdp-single-chip.dtb"
XEN_DEVICETREE_XEN_BOOTARGS ?= "noreboot dom0_mem=${XEN_DEVICETREE_DOM0_MEM}\
 console=dtuart dtuart=serial0 bootscrub=0"
XEN_DEVICETREE_DOM0_MEM ?= "2048M,max:2048M"
XEN_DEVICETREE_DOM0_BOOTARGS ?= "console=hvc0 earlycon=xen rootwait \
    root=PARTUUID=6a60524d-061d-454a-bfd1-38989910eccd"
XEN_DEVICETREE_DTSI = "xen.dtsi"

# Our package does not generate any packages for the rootfs, but instead
# contributes to deploy
inherit nopackages deploy
inherit features_check

REQUIRED_DISTRO_FEATURES = 'xen'

DEPENDS += "dtc-native"
PACKAGE_ARCH = "${MACHINE_ARCH}"

do_configure[noexec] = "1"
do_compile[noexec] = "1"
do_install[noexec] = "1"

do_deploy() {
    echo "
/ {
    /delete-node/ pmu;
    /delete-node/ spe-pmu;
    soc {
        /delete-node/ iommu@4f000000;
        /delete-node/ iommu@4f400000;
        pcie@70000000 {
            /delete-property/ msi-map;
            /delete-property/ iommu-map;
            reg = < 0x00 0x70000000 0x00 0x1200000 0x00 0x6000000 0x00 0x80000 0x00 0x60000000 0x00 0x80000 >;
        };
        pcie@68000000 {
            /delete-property/ msi-map;
            /delete-property/ iommu-map;
            reg = < 0x00 0x68000000 0x00 0x1200000 0x00 0x6000000 0x00 0x80000 0x00 0x62000000 0x00 0x80000 >;
        };
    };
    chosen {
        xen,dom0-bootargs = \"${XEN_DEVICETREE_DOM0_BOOTARGS}\";
        xen,xen-bootargs = \"${XEN_DEVICETREE_XEN_BOOTARGS}\";
    };
};
" > "${XEN_DEVICETREE_DTSI}"

    # Generate final dtbs
    for dtbf in ${XEN_DEVICETREE_DTBS}; do
        rdtb=`basename $dtbf`
        if [ ! -f ${DEPLOY_DIR_IMAGE}/$rdtb ]; then
            die "Wrong file in XEN_DEVICETREE_DTBS: ${DEPLOY_DIR_IMAGE}/$rdtb does not exist"
        fi
        dtc -I dtb -O dts -o ${WORKDIR}/dom0-linux.dts ${DEPLOY_DIR_IMAGE}/$rdtb

        echo "/include/ \"${XEN_DEVICETREE_DTSI}\"" >> ${WORKDIR}/dom0-linux.dts

        rdtbnoextn=$(basename $dtbf ".dtb")
        dtc -I dts -O dtb \
            -o ${WORKDIR}/${rdtbnoextn}-xen.dtb ${WORKDIR}/dom0-linux.dts
        install -m 644 ${rdtbnoextn}-xen.dtb ${DEPLOYDIR}/.
    done
}
do_deploy[depends] += "${XEN_DEVICETREE_DEPEND}"

addtask deploy after do_install
