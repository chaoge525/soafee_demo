# Copyright (c) 2022 Arm Limited or its affiliates. All rights reserved.
#
# SPDX-License-Identifier: MIT

# This file centralizes the variables and links used throughout the EWAOL
# documentation. The dictionaries are converted to a single string that is used
# as the rst_prolog (see the Sphinx Configuration documentation at
# https://www.sphinx-doc.org/en/master/usage/configuration.html for more info).

# There are two types of key-value substitutions:
#     1. simple string replacements
#     2. replacement with a rendered hyperlink, where the key defines what the
#        rendered hyerplink text will be

# Prepend the key with "link:" to identify it as a Sphinx target name for use as
# a hyperlink. The "link:" prefix is dropped from the substitution name.
#
# For example:
#   "link:This URL": "www.arm.com"
#   "company name": "arm"
# Can be used as:
#   The |company name| website can be found at |This URL|_.
#
# Note the "_" which renders the substitution as a hyperlink is only possible
# because the variable is defined as a link, to be resolved as a Sphinx target.

yocto_release = "kirkstone"
yocto_doc_version = "4.0/"
yocto_linux_version = "5.15"
xen_version = "4.16"
kas_version = "3.0.2"
ewaol_version = "v1.0"

general_links = {
  "link:Yocto Project Documentation": f"https://docs.yoctoproject.org/{yocto_doc_version}",
  "link:Yocto Release Process": "https://docs.yoctoproject.org/ref-manual/release-process.html",
  "link:kernel module compilation": f"https://docs.yoctoproject.org/{yocto_doc_version}kernel-dev/common.html#building-out-of-tree-modules-on-the-target",
  "link:profiling and tracing": f"https://docs.yoctoproject.org/{yocto_doc_version}profile-manual/index.html",
  "link:runtime package management": f"https://docs.yoctoproject.org/{yocto_doc_version}dev-manual/common-tasks.html#using-runtime-package-management",
  "link:Multiple Configuration Build": f"https://docs.yoctoproject.org/{yocto_doc_version}dev-manual/common-tasks.html#building-images-for-multiple-targets-using-multiple-configurations",
  "link:list of essential packages": f"https://docs.yoctoproject.org/{yocto_doc_version}singleindex.html#required-packages-for-the-build-host",
  "link:Yocto Check Layer Script": f"https://docs.yoctoproject.org/{yocto_doc_version}singleindex.html#yocto-check-layer-script",
  "link:DEFAULTTUNE": f"https://docs.yoctoproject.org/{yocto_doc_version}ref-manual/variables.html#term-DEFAULTTUNE",
  "link:Yocto Docker config": f"https://git.yoctoproject.org/yocto-kernel-cache/tree/features/docker/docker.cfg?h=yocto-{yocto_linux_version}",
  "link:Yocto K3s config": f"https://git.yoctoproject.org/cgit/cgit.cgi/meta-virtualization/tree/recipes-kernel/linux/linux-yocto/kubernetes.cfg?h={yocto_release}",
  "link:Yocto Xen config": f"https://git.yoctoproject.org/cgit/cgit.cgi/yocto-kernel-cache/tree/features/xen/xen.cfg?h=yocto-{yocto_linux_version}",
  "link:kas build tool": f"https://kas.readthedocs.io/en/{kas_version}/userguide.html",
  "link:kas Dependencies & installation": f"https://kas.readthedocs.io/en/{kas_version}/userguide.html#dependencies-installation",
  "link:meta-arm-bsp": f"https://git.yoctoproject.org/meta-arm/tree/meta-arm-bsp/documentation/n1sdp.md?h={yocto_release}",
  "link:xl domain configuration": f"https://xenbits.xen.org/docs/{xen_version}-testing/man/xl.cfg.5.html",
  "link:xl documentation": f"https://xenbits.xen.org/docs/{xen_version}-testing/man/xl.1.html",
  "link:N1SDP Technical Reference Manual": "https://developer.arm.com/documentation/101489/0000",
  "link:PEP 8": "https://peps.python.org/pep-0008/",
  "link:pycodestyle Documentation": "https://pycodestyle.pycqa.org/en/latest/",
  "link:Shellcheck": "https://github.com/koalaman/shellcheck",
  "link:Shellcheck wiki pages": "https://github.com/koalaman/shellcheck/wiki/Checks",
  "link:Docker documentation": "https://docs.docker.com",
  "link:K3s documentation": "https://rancher.com/docs/k3s/latest/en",
  "link:Xen documentation": "https://wiki.xenproject.org/wiki/Main_Page",
  "link:yamllint documentation": "https://yamllint.readthedocs.io/en/stable/",
  "link:Yocto Package Test": "https://wiki.yoctoproject.org/wiki/Ptest",
  "link:Bash Automated Test System": "https://github.com/bats-core/bats-core",
  "link:Python Datetime Format Codes": "https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes",
  "link:Nginx": "https://www.nginx.com/",
  "link:Potential firmware damage notice": "https://community.arm.com/developer/tools-software/oss-platforms/w/docs/604/notice-potential-damage-to-n1sdp-boards-if-using-latest-firmware-release",
  "link:GitLab Issues": "https://gitlab.arm.com/ewaol/meta-ewaol/-/issues",
}

layer_definitions = {
  "meta-ewaol contributions branch": f"``{yocto_release}-dev``",
  "meta-ewaol repository": "https://gitlab.arm.com/ewaol/meta-ewaol",
  "meta-ewaol repository host": "https://gitlab.arm.com",
  "meta-ewaol remote": "https://git.gitlab.arm.com/ewaol/meta-ewaol.git",
  "meta-ewaol branch": f"{yocto_release}-dev",
  "meta-cassini branch": "cassini-integration",
  "meta-ewaol version": f"{ewaol_version}",
  "poky branch": f"{yocto_release}",
  "meta-openembedded branch": f"{yocto_release}",
  "meta-virtualization branch": f"{yocto_release}",
  "meta-arm branch": f"{yocto_release}",
  "poky revision": "453be4d258f71855205f45599eea04589eb4a369",
  "meta-virtualization revision": "2fae71cdf0e8c6f398f51219bdf31eac76c662ec",
  "meta-openembedded revision": "166ef8dbb14ad98b2094a77fcf352f6c63d5abf2",
  "meta-arm revision": "fc09cc0e8db287600625e64905170a6de24f2686",
  "layer dependency statement": f"The layer revisions are related to the EWAOL ``{ewaol_version}`` release.",
}

other_definitions = {
  "kas version": f"{kas_version}",
  "virtualization customization yaml":
      """
      EWAOL_GUEST_VM_INSTANCES: "1"                      # Number of Guest VM instances
      EWAOL_GUEST_VM1_NUMBER_OF_CPUS: "4"                # Number of CPUs for Guest VM1
      EWAOL_GUEST_VM1_MEMORY_SIZE: "6144"                # Memory size for Guest VM1 (MB)
      EWAOL_GUEST_VM1_ROOTFS_EXTRA_SPACE: ""             # Extra storage space for Guest VM1 (KB)
      EWAOL_CONTROL_VM_MEMORY_SIZE: "2048"               # Memory size for Control VM (MB)
      EWAOL_CONTROL_VM_ROOTFS_EXTRA_SPACE: "1000000"     # Extra storage space for Control VM (KB)
      """,
}

# Potentially old definitions required for documenting migrations, changelog
release_definitions = {
  "v1.0:migration version": "v1.0",
  "v1.0:kas version": other_definitions["kas version"],
}

def generate_link(key, link):

  definition = f".. _{key}: {link}"
  key_mapping = f".. |{key}| replace:: {key}"
  return f"{definition}\n{key_mapping}"

def generate_replacement(key, value):

  replacement = f".. |{key}| replace:: {value}"
  return f"{replacement}"

def generate_rst_prolog():

  rst_prolog = ""

  for variables_group in [general_links,
                          layer_definitions,
                          other_definitions,
                          release_definitions]:

    for key, value in variables_group.items():
      if key.startswith("link:"):
        rst_prolog += generate_link(key.split("link:")[1], value) + "\n"
      else:
        rst_prolog += generate_replacement(key, value) + "\n"

  return rst_prolog
