EWAOL Quickstart
==================

This documentation explains how to quickly get started with the EWAOL project,
and the functionalities it provides.

Build Host Setup
-------------------

A number of packages are needed to build projects with Yocto. The Documentation
provides a list of essential packages that can be found here:
- https://www.yoctoproject.org/docs/latest/mega-manual/mega-manual.html#required-packages-for-the-build-host

meta-ewaol-config contains build configs for kas, a tool for easily setting up
bitbake based projects.

kas uses yaml files to define a build config. Each config downloads sources and
creates configurations that would otherwise need to be created manually, and can
initiate the bitbake build process.

To install kas you should follow the User Guide:
 - https://kas.readthedocs.io/en/latest/userguide.html

Build
-----
Currently there are yaml files to support the following MACHINES:
 - FVP-Base
 - N1SDP

To build the docker and podman images using kas:
``kas build meta-ewaol/meta-ewaol-config/kas/fvp-base.yml``
Or
``kas build meta-ewaol/meta-ewaol-config/kas/n1sdp.yml``

Alternatively, to provide another supported machine:
``KAS_MACHINE=[machine] kas build meta-ewaol/meta-ewaol-config/kas/base.yml``

The resulting images will be:
 - build/tmp/deploy/images/[machine]/ewaol-image-docker-[machine].*
 - build/tmp/deploy/images/[machine]/ewaol-image-podman-[machine].*
