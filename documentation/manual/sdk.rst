..
 # Copyright (c) 2022, Arm Limited.
 #
 # SPDX-License-Identifier: MIT

Software Development Kit (SDK)
==============================

EWAOL SDK distribution images enable users to perform common development tasks
on the target, such as:

  * Application and kernel module compilation
  * Remote debugging
  * Profiling
  * Tracing
  * Runtime package management

.. note::
    The precise list of packages and image features provided as part of the
    EWAOL SDK can be found in
    ``meta-ewaol-distro/conf/distro/include/ewaol-sdk.inc``.

The Yocto project provides guidance for some of these common development tasks,
for example `kernel module compilation`_, `profiling and tracing`_, and
`runtime package management`_.

The EWAOL SDK is available as a build target only if ``ewaol-sdk`` is included
in ``DISTRO_FEATURES``.

When building a virtualization SDK distribution image, the SDK will be available
on both the Control VM and any EWAOL Guest VMs built during the image build
process.

  .. _kernel module compilation:
      https://docs.yoctoproject.org/3.4.2/kernel-dev/common.html#building-out-of-tree-modules-on-the-target

  .. _profiling and tracing: https://docs.yoctoproject.org/3.4.2/profile-manual/index.html

  .. _runtime package management:
      https://docs.yoctoproject.org/3.4.2/dev-manual/common-tasks.html#using-runtime-package-management

