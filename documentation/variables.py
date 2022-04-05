# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# This file centralizes the variables and links used throughout the EWAOL
# documentation. The dictionaries are converted to a single string that is used
# as the rst_prolog (see the Sphinx Configuration documentation at
# https://www.sphinx-doc.org/en/master/usage/configuration.html for more info).

external_links = {
  "Yocto Project Documentation": "https://docs.yoctoproject.org",
  "Yocto Release Process": "https://docs.yoctoproject.org/ref-manual/release-process.html",
  "kernel module compilation": "https://docs.yoctoproject.org/3.4.2/kernel-dev/common.html#building-out-of-tree-modules-on-the-target",
  "profiling and tracing": "https://docs.yoctoproject.org/3.4.2/profile-manual/index.html",
  "runtime package management": "https://docs.yoctoproject.org/3.4.2/dev-manual/common-tasks.html#using-runtime-package-management",
  "Multiple Configuration Build": "https://docs.yoctoproject.org/3.4.2/dev-manual/common-tasks.html#building-images-for-multiple-targets-using-multiple-configurations",
  "list of essential packages": "https://docs.yoctoproject.org/3.4.2/singleindex.html#required-packages-for-the-build-host",
  "Yocto Check Layer Script": "https://docs.yoctoproject.org/3.4.2/singleindex.html#yocto-check-layer-script",

  "Yocto Docker config": "http://git.yoctoproject.org/cgit/cgit.cgi/yocto-kernel-cache/tree/features/docker/docker.cfg",
  "Yocto K3s config": "http://git.yoctoproject.org/cgit/cgit.cgi/meta-virtualization/tree/recipes-kernel/linux/linux-yocto/kubernetes.cfg",
  "Yocto Xen config": "http://git.yoctoproject.org/cgit/cgit.cgi/yocto-kernel-cache/tree/features/xen/xen.cfg",
  "kas build tool": "https://kas.readthedocs.io/en/latest/userguide.html",

  "xl documentation": "https://xenbits.xen.org/docs/unstable/man/xl.1.html",
  "xl domain configuration": "https://xenbits.xen.org/docs/4.16-testing/man/xl.cfg.5.html",
  "meta-arm-bsp": "https://git.yoctoproject.org/cgit/cgit.cgi/meta-arm/tree/meta-arm-bsp/documentation",
  "N1SDP Technical Reference Manual": "https://developer.arm.com/documentation/101489/0000",
  "kas Dependencies & installation": "https://kas.readthedocs.io/en/latest/userguide.html#dependencies-installation",
  "PEP 8": "https://peps.python.org/pep-0008/",
  "pycodestyle Documentation": "https://pycodestyle.pycqa.org/en/latest/",
  "Shellcheck": "https://github.com/koalaman/shellcheck",
  "Shellcheck wiki pages": "https://github.com/koalaman/shellcheck/wiki/Checks",
  "Docker documentation": "https://docs.docker.com",
  "K3s documentation": "https://rancher.com/docs/k3s/latest/en",
  "Xen documentation": "https://wiki.xenproject.org/wiki/Main_Page",
  "Yocto Package Test": "https://wiki.yoctoproject.org/wiki/Ptest",
  "Bash Automated Test System": "https://github.com/bats-core/bats-core",
  "Python Datetime Format Codes": "https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes",
  "Nginx": "https://www.nginx.com/",
  "Potential firmware damage notice": "https://community.arm.com/developer/tools-software/oss-platforms/w/docs/604/notice-potential-damage-to-n1sdp-boards-if-using-latest-firmware-release",
}

layer_definitions = {
  "meta-ewaol contributions branch": "honister-dev",
  "meta-ewaol repository": "https://gitlab.arm.com/ewaol/meta-ewaol",
  "meta-ewaol repository host": "https://gitlab.arm.com",
  "meta-ewaol remote": "https://git.gitlab.arm.com/ewaol/meta-ewaol.git",
  "meta-ewaol branch": "honister-dev",
  "poky branch": "honister",
  "meta-openembedded branch": "honister",
  "meta-virtualization branch": "honister",
  "meta-arm branch": "honister",
  "poky revision": "HEAD",
  "meta-virtualization revision": "HEAD",
  "meta-openembedded revision": "HEAD",
  "meta-arm revision": "HEAD",
  "layer dependency statement": "The layer revisions are related to EWAOL's current development branch.",
}

other_definitions = {
  "kas version": "2.6.1",
  "virtualization customization yaml":
      """
      EWAOL_GUEST_VM_INSTANCES: "1"                      # Number of Guest VM instances
      EWAOL_GUEST_VM1_NUMBER_OF_CPUS: "4"                # Number of CPUs for Guest VM1
      EWAOL_GUEST_VM1_MEMORY_SIZE: "6144"                # Memory size for Guest VM1 (MB)
      EWAOL_GUEST_VM1_ROOTFS_EXTRA_SPACE: ""             # Extra storage space for Guest VM1 (KB)
      EWAOL_CONTROL_VM_MEMORY_SIZE: "2048"               # Memory size for Control VM (MB)
      EWAOL_CONTROL_VM_ROOTFS_EXTRA_SPACE: "1000000"     # Extra storage space for Control VM (KB)
      EWAOL_ROOTFS_EXTRA_SPACE: "2000000"                # Extra storage space for the Control VM and each Guest VM (KB)
      """,
}

def generate_external_link(key, link):

  definition = f".. _{key}: {link}"
  key_mapping = f".. |{key}| replace:: {key}"
  return f"{definition}\n{key_mapping}"

def generate_replacement(key, value):

  replacement = f".. |{key}| replace:: {value}"
  return f"{replacement}"

def generate_rst_prolog():

  rst_prolog = ""

  rst_prolog = "\n".join([generate_external_link(key, link) for key, link in
                         external_links.items()]) + "\n"

  rst_prolog += "\n".join([generate_replacement(key, value) for key, value in
                         layer_definitions.items()]) + "\n"

  rst_prolog += "\n".join([generate_replacement(key, value) for key, value in
                         other_definitions.items()]) + "\n"

  return rst_prolog
