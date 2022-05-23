..
 # Copyright (c) 2021-2022, Arm Limited.
 #
 # SPDX-License-Identifier: MIT

#########################
Changelog & Release Notes
#########################

******
v1.0
******

New Features
============

* Updated the EWAOL software stack to provide two system architectures:
  baremetal and virtualization
* Introduced EWAOL User Accounts with multi-level privileges
* Introduced EWAOL Security Hardening to reduce potential sources or attack
  vectors of security vulnerabilities

Changed
=======

Third-party Yocto layers used to build the software stack:

.. code-block:: yaml

    URL: https://git.yoctoproject.org/git/poky
    layers: meta, meta-poky
    branch: kirkstone
    revision: 453be4d258f71855205f45599eea04589eb4a369

    URL: https://git.openembedded.org/meta-openembedded
    layers: meta-filesystems, meta-networking, meta-oe, meta-python
    branch: kirkstone
    revision: 166ef8dbb14ad98b2094a77fcf352f6c63d5abf2

    URL: https://git.yoctoproject.org/git/meta-virtualization
    layers: meta-virtualization
    branch: kirkstone
    revision: 2fae71cdf0e8c6f398f51219bdf31eac76c662ec

    URL: https://git.yoctoproject.org/git/meta-arm
    layers: meta-arm, meta-arm-bsp, meta-arm-toolchain
    branch: kirkstone
    revision: fc09cc0e8db287600625e64905170a6de24f2686

Main software components versions:

  * Systemd (version: ``250.5``) as init system
  * K3s container orchestration engine (version: ``v1.22.6+k3s1+git4262c6b``)
  * Docker (version: ``20.10.12+ce+git906f57f``) as container engine
  * runc-opencontainers (version: ``1.1.0+git0+b9460f26b4``) as the OCI
    container runtime
  * Xen (version: ``4.16+stable0+f265444922``) as the type-1 hypervisor

Configs:

  * Refactored kas configuration files, and separated into three ordered
    categories: "Architecture", "Build Modifier" and "Target Platform" Configs

Distro:

  * Introduced EWAOL Baremetal and Virtualization Distribution images
  * Introduced Xen as type-1 hypervisor for EWAOL Virtualization Distribution
    images
  * Introduced optional EWAOL Security Hardening distro feature
  * Introduced EWAOL User Accounts (``ewaol``, ``user`` and ``test``) with
    various privilege levels
  * Introduced Filesystem Compilation Tuning where EWAOL root filesystems by
    default use the generic ``armv8a-crc`` tune for ``aarch64`` based target
    platforms
  * Introduced ``meta-ewaol-bsp`` Yocto BSP layer with target platform specific
    extensions for particular EWAOL distribution images
  * Introduced the following build-time kernel configuration checks:

    * K3s orchestration support
    * Xen virtualization support
  * Added the installation of docker-ce instead of docker-moby on EWAOL root
    filesystems
  * Added build information inclusion on EWAOL root filesystems

Documentation:

  * Refactored the documentation structure to improve readability
  * Introduced the Contribution Guidelines instructions

Tools:

  * Expanded QA checks to also validate:

    * Documentation build
    * Yocto layer compatibility
    * YAML files formatting

  * Generalized the documentation build tooling to allow building independent
    projects
  * Updated Python minimal required version to ``3.8``
  * Updated Git minimal required version to ``2.25``
  * Updated kas minimal required version to ``3.0.2``
  * Updated kas configuration format version to ``11``
  * Added various fixes and improvements to QA checks tooling
  * Dropped the deprecated CI-specific build tool

Tests:

  * Introduced "Xen Virtualization Tests" and "User Accounts Tests" test suites
  * Expanded appropriate test suites to also include validations of both
    Control and Guest VMs on EWAOL virtualization distribution images
  * Configured all tests suites to be run as the ``test`` user account
  * Added extra security checks for all test suites, performed when the
    Security Hardening distro feature is enabled
  * Changed filesystem storage directories for test suite logs and temporary
    run-time files
  * Refactored test recipes to share common code installed on the root
    filesystem

Limitations
===========

None.

Resolved and Known Issues
=========================

Known Issues:

  * The K3s recipe build involves fetching a substantial amount of source code
    which might fail due to connection timeout. If a similar error message as
    ``ERROR: Task (/<...>/layers/meta-virtualization/recipes-containers/k3s/k3s_git.bb:do_fetch) failed with exit code '1'``
    is displayed, try re-running the build command until it completes.

******
v0.2.4
******

New Features
============

No new features were introduced.

Changed
=======

Bug fixes as listed in `v0.2.4 Resolved and Known Issues`_.

Limitations
===========

None.

.. _v0.2.4 Resolved and Known Issues:

Resolved and Known Issues
=========================

Resolved issues from v0.2.3:

  * ewaol-distro: Fix BitBake fetch for ostree recipe from meta-oe

******
v0.2.3
******

New Features
============

No new features were introduced.

Changed
=======

Bug fixes as listed in `v0.2.3 Resolved and Known Issues`_.

Limitations
===========

None.

.. _v0.2.3 Resolved and Known Issues:

Resolved and Known Issues
=========================

Resolved issues from v0.2.2:

  * qa-checks: Install pip for Python 3.6
  * ewaol-distro: Fix BitBake fetch for runc-opencontainers recipe from
    meta-virtualization

******
v0.2.2
******

New Features
============

No new features were introduced.

Changed
=======

Bug fixes as listed in `v0.2.2 Resolved and Known Issues`_.

Limitations
===========

None.

.. _v0.2.2 Resolved and Known Issues:

Resolved and Known Issues
=========================

Resolved issues from v0.2.1:

  * ewaol-distro: libpcre and libpcre2 to fetch from sourceforge and github

******
v0.2.1
******

New Features
============

No new features were introduced.

Changed
=======

Bug fixes as listed in `v0.2.1 Resolved and Known Issues`_.

Limitations
===========

None.

.. _v0.2.1 Resolved and Known Issues:

Resolved and Known Issues
=========================

Resolved issues from v0.2:

  * qa-checks: shell check running in all relevant files within the repository
  * qa-checks: shell check SC2288 fixes for integration tests scripts
  * qa-checks: Consider latest git commit for matching file's copyright year
  * qa-checks: Fix getting the last modification date of external works
  * qa-checks: Disable SC2086 shellcheck for k3s-killall.sh from K3s package
  * ewaol-distro: Fix BitBake fetch for go-fsnotify recipe from
    meta-virtualization

****
v0.2
****

New Features
============

* Introduced K3s container orchestration support, as well as its integration
  tests
* Removed support for the FVP Base-A reference platform
* Introduced EWAOL Software Development Kit (SDK) distro image type which
  includes packages and features to support software development on the target

Changed
=======

Third-party Yocto layers used to build the software stack:

.. code-block:: yaml

    URI: git://git.yoctoproject.org/poky
    layers: meta, meta-poky
    branch: hardknott
    revision: 269265c00091fa65f93de6cad32bf24f1e7f72a3

    URI: git://git.openembedded.org/meta-openembedded
    layers: meta-filesystems, meta-networking, meta-oe, meta-perl, meta-python
    branch: hardknott
    revision: f44e1a2b575826e88b8cb2725e54a7c5d29cf94a

    URI: git://git.yoctoproject.org/meta-security
    layers: meta-security
    branch: hardknott
    revision: 16c68aae0fdfc20c7ce5cf4da0a9fff8bdd75769

    URI: git://git.yoctoproject.org/meta-virtualization
    layers: meta-virtualization
    branch: hardknott
    revision: 7f719ef40896b6c78893add8485fda995b00d51d

    URI: git://git.yoctoproject.org/meta-arm
    layers: meta-arm, meta-arm-bsp, meta-arm-toolchain
    branch: hardknott
    revision: 71686ac05c34e53950268bfe0d52c3624e78c190

Main software components versions:

  * Systemd (version: ``247.6``) as init system
  * K3s container orchestration engine (version: ``v1.20.11+k3s2``)
  * Docker (version: ``20.10.3+git11ecfe8a81b7040738333f777681e55e2a867160``)
    or Podman (version: ``3.2.1+git0+ab4d0cf908``) as container engines
  * runc-opencontainers (version: ``1.0.0+rc93+git0+249bca0a13``) as the OCI


Configs:

  * Only include meta-arm layers when required

Distro:

  * Introduced EWAOL Software Development Kit (SDK) distro image type
  * Introduced K3s container orchestration support

Documentation:

  * Refactored README.md to not include it in the final rendered documentation

Tools:

  * Introduced the kas-runner.py tool to support loading build environment
    configurations from yaml files. This tool is still in experimental stage
    and will be replacing kas-ci-build.py in the future
  * Added '-j' and '--out-dir' parameters to kas-ci-build.py set the maximum
    number of CPU threads available for BitBake and allow user to change build
    directory
  * Moved project specific configurations for QA checks to meta-ewaol-config
  * Various improvements in QA checks for spelling, commit message and license
    header

Tests:

  * Introduced K3s container orchestration integration tests
  * Improved tests logging and cleanup tasks
  * Multiple tests suites share the same base directory structure and common
    files

Limitations
===========

None.

Resolved and Known Issues
=========================

None.

******
v0.1.1
******

New Features
============

No new features were introduced.

Changed
=======

Documentation:

  * Added manual BitBake build preparation documentation
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

****
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
  * Development and Test image flavors
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

.. code-block:: yaml

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
