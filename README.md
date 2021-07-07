## Repository Structure

The high-level structure of the `meta-ewaol` repository is as follows:

**meta-ewaol-distro**:
  Yocto layer that provides the top-level image recipes and general policies
  available to be implemented as a EWAOL project distribution.

**meta-ewaol-config**:
  Directory that contains kas configurations files for building EWAOL images.

**meta-ewaol-tests**:
  Yocto layer that provides recipes and configuration to enable the validation
  of images built for the EWAOL project.

**documentation**:
  Directory that provides documentation for the `meta-ewaol` repository.

**tools**:
  Directory that provides tools that perform quality-assurance checks on the
  repository as well as tools and scripts to support EWAOL images builds.

## Building the documentation

See the :ref:`Documentation build` section of the tools documentation page.

## Layers Dependencies


The repository contains Yocto layers that require dependencies as follows.

The `meta-ewaol-distro` layer depends on:

    URI: git://git.yoctoproject.org/poky/meta
    branch: hardknott
    revision: HEAD

    URI: git://git.yoctoproject.org/poky/meta-poky
    branch: hardknott
    revision: HEAD

    URI: git://git.yoctoproject.org/meta-virtualization
    branch: hardknott
    revision: HEAD

    URI: git://git.yoctoproject.org/meta-security
    branch: hardknott
    revision: HEAD

The `meta-ewaol-tests` layer depends on:

    URI: git://git.yoctoproject.org/poky/meta
    branch: hardknott
    revision: HEAD

## Repository License

The software is provided under an MIT license (more details in :ref:`License`).

Contributions to the project should follow the same license.

## Contributions and Bug Reports

This project has not put in place a process for contributions or bug reporting
currently. If you would like to contribute or have found a bug, please contact
the maintainers.

## Maintainer(s)

* Diego Sueiro <diego.sueiro@arm.com>
* <support@arm.com>
