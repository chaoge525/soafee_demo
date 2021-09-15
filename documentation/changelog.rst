Changelog & Release Notes
#########################

v0.1.1
******

New Features
============

No new features were introduced.

Changed
=======

Documentation:

  * Added manual bitbake build preparation documentation
  * Added QA checks documentation
  * Added meta-ewaol public repository URL
  * CI Build Tool documentation fixes
  * Refactor Sphinx auto section labels and cross-references links
  * Added public documentation URL
  * Added link to SOAFEE URL
  * Refactored Layer Dependencies on README.md
  * Added Gitlab Pages integration via .gitlab-ci.yml
  * Updated kas installation instructions
  * Increased the free storage requirement for building to 65 GBytes

Limitations
===========

Same as `v0.1 Limitations`_.

Resolved and Known Issues
=========================

None.

v0.1
****

New Features
============

The following features and components are included into the reference software
stack implementation:

  * EWAOL Yocto distribution based on ``poky.conf`` distro
  * Systemd (version: ``247.6``) as init system
  * Docker (version: ``20.10.3+git11ecfe8a81b7040738333f777681e55e2a867160``)
    or Podman (version: ``3.2.1+git0+ab4d0cf908``) as container engines
  * runc-opencontainers (version: ``1.0.0+rc93+git0+249bca0a13``) as the OCI
    container runtime
  * Development and Test image flavours
  * Container engine tests
  * Container runtime Kernel configuration check

Supported Arm Reference Platforms:

 * Armv8-A Base RevC AEM FVP (FVP-Base) with
   ``FVP_Base_RevC-2xAEMvA_11.14_21.tgz`` package version.
 * N1SDP


Quality Assurance Checks Tooling:

  * Source code:

    * Shell scripts: shellcheck-py module
    * Python: pycodestyle module (PEP8)
    * Copyright notice inclusion
    * SPDX license identifier inclusion

  * Documentation spelling (pyspellchecker module)
  * Commit message rules

Build Tools:

  * Documentation build
  * CI build

Documentation Pages:

  * Overview
  * Project Quickstart
  * Image Builds
  * Image Validation
  * Yocto Layers
  * Codeline Management
  * Tools
  * License
  * Changelog & Release Notes

Third-party Yocto layers used to build the software stack:

.. code-block:: console

   URI: git://git.yoctoproject.org/poky/meta
   branch: hardknott
   revision: da0ce760c5372f8f2ef4c4dfa24b6995db73c66c

   URI: git://git.yoctoproject.org/poky/meta-poky
   branch: hardknott
   revision: da0ce760c5372f8f2ef4c4dfa24b6995db73c66c

   URI: git://git.openembedded.org/meta-openembedded
   branch: hardknott
   revision: c51e79dd854460c6f6949a187970d05362152e84

   URI: git://git.yoctoproject.org/meta-security
   branch: hardknott
   revision: c6b1eec0e5e94b02160ce0ac3aa9582cbbf7b0ed

   URI: git://git.yoctoproject.org/meta-virtualization
   branch: hardknott
   revision: 3508b13acbf669a5169fafca232a5c4ee705dd16

   URI: git://git.yoctoproject.org/meta-arm
   branch: hardknott
   revision: e82d9fdd49745a6a064b636f2ea1e02c1750d298

Changed
=======

Initial version.

.. _v0.1 Limitations:

Limitations
===========

  * FVP-Base build and emulation only supported on x86_64-linux hosts

Resolved and Known Issues
=========================

None.
