..
 # Copyright (c) 2022, Arm Limited.
 #
 # SPDX-License-Identifier: MIT

##################
Security Hardening
##################

EWAOL distribution images can be hardened to reduce potential sources or attack
vectors of security vulnerabilities. EWAOL security hardening modifies the
distribution to:

  * Force password update for each user account after first logging in.
    An empty and expired password is set for each user account by default.
  * Enhance the kernel security, kernel configuration is extended with the
    ``security.scc`` in ``KERNEL_FEATURES``.
  * Enable the 'Secure Computing Mode' (seccomp) Linux kernel feature by
    appending ``seccomp`` to ``DISTRO_FEATURES``.
  * Ensure that all available packages from ``meta-openembedded``,
    ``meta-virtualization`` and ``poky`` layers are configured with:
    ``--with-libcap[-ng]``.
  * Remove ``debug-tweaks`` from ``IMAGE_FEATURES``.
  * Disable SSH login using the ``root`` account.

Security hardening is not enabled by default, see
:ref:`manual_build_system_security_hardening` for details on including the
security hardening on the EWAOL distribution image.

EWAOL security hardening does not reduce the scope of the
:ref:`validation_run-time_integration_tests`.
