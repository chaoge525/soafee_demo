Overview
========

The Edge Workload Abstraction and Orchestration Layer (EWAOL) project provides
users with a standards based framework using containers for the deployment and
orchestration of applications on edge platforms. Under this approach, a full
software stack is divided into the following software layers:

* **Workloads**: Applications deployed using containers. These are the users of
  the EWAOL. Note that the EWAOL project does not provide any workload
  containers.

* **Linux based Filesystem**: This is the main component provided by the EWAOL
  project. It contains primarily the container engine and its run-time
  dependencies.

* **System software**: Platform specific software composed of firmware and
  operating system. EWAOL does not provide the system software but uses meta-arm
  and meta-arm-bsp to provide an example reference stack using the N1SDP and
  Base FVP platforms.

More specifically, the ``meta-ewaol`` repository contains Yocto layers,
configuration files, and tools to support building and validating EWAOL
functionalities.

.. note::
    Users of this software stack must consider safety and security implications
    according to their own usage goals.

.. _overview_high-level_architecture:

High-Level Architecture
-----------------------

.. image:: images/ewaol_arch_overview.png

The EWAOL images include the following major features:

  * Based on ``poky.conf`` distro
  * Systemd as init system
  * RPM as the package management system
  * Docker or Podman as container engine
  * runc-opencontainers as the OCI container runtime
  * Development and Test images flavours

.. mdinclude:: ../README.md
