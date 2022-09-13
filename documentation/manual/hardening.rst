..
 # Copyright (c) 2022, Arm Limited.
 #
 # SPDX-License-Identifier: MIT

##################
Security Hardening
##################

EWAOL distribution images can be hardened to reduce potential sources or attack
vectors of security vulnerabilities, by enabling the security features
implemented by Project Cassini. This security hardening modifies the
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
  * Disable all login access to the ``root`` account.
  * Sets the umask to ``0027`` (which translates permissions as ``640`` for
    files and ``750`` for directories).

Security hardening is not enabled by default, see
:ref:`manual_build_system_security_hardening` for details on including the
security hardening on the EWAOL distribution image.

EWAOL security hardening does not reduce the scope of the
:ref:`validation_run-time_integration_tests`.
