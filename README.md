## Documentation

The project's documentation can be browsed at
https://ewaol.sites.arm.com/meta-ewaol

### Building the documentation

See the :ref:`tools_documentation_build` section of the tools documentation page.

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

.. _readme_layers_dependencies:

## Layers Dependencies

The repository contains Yocto layers that require dependencies as follows. The
layers revisions are related to the EWAOL v0.2-rc1 release.

The `meta-ewaol-distro` layer depends on:

    URI: git://git.yoctoproject.org/poky
    layers: meta, meta-poky
    branch: hardknott
    revision: 5dad70fedb5fc38dbbd498d668b95ea9dba48293

    URI: git://git.openembedded.org/meta-openembedded
    layers: meta-filesystems, meta-networking, meta-oe, meta-perl, meta-python
    branch: hardknott
    revision: 7bd7e1da9034e72ca4262dba55f70b2b23499aae

    URI: git://git.yoctoproject.org/meta-security
    layers: meta-security
    branch: hardknott
    revision: 5050d1267ad41288c903086030594f8702bfa039

    URI: git://git.yoctoproject.org/meta-virtualization
    layers: meta-virtualization
    branch: hardknott
    revision: c19c9927855abb63e89f9d853ba0cb258a2de415


The `meta-ewaol-tests` layer depends on:

    URI: git://git.yoctoproject.org/poky
    layers: meta
    branch: hardknott
    revision: 5dad70fedb5fc38dbbd498d668b95ea9dba48293

## Repository License

The software is provided under an MIT license (more details in
:ref:`license_link:License`).

Contributions to the project should follow the same license.

## Contributions and Bug Reports

This project has not put in place a process for contributions currently.

For bug reports, please submit an Issue via GitLab.

## Feedback and support

To request support please contact Arm at support@arm.com. Arm licensees may
also contact Arm via their partner managers.

## Maintainer(s)

* Diego Sueiro <diego.sueiro@arm.com>
