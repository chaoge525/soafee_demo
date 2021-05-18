## Repository Structure

The high-level structure of the `meta-ewaol` repository is as follows:

**meta-ewaol-distro**:
  Yocto layer that provides the top-level image recipes and general policies
  available to be implemented as a EWAOL project distribution.

**meta-ewaol-config**:
  Directory that contains kas configuration files for specifying and building
  a software image for the EWAOL project, as well as tooling to
  support the build process.

**meta-ewaol-tests**:
  Yocto layer that provides recipes and configuration to enable the validation
  of images built for the EWAOL project.

**documentation**:
  Directory that provides documentation for the `meta-ewaol` repository.

## Building the documentation

The documentation uses `Sphinx`, which may be installed via:

    pip3 install sphinx==4.0.2 sphinx-rtd-theme==0.5.2 docutils==0.16 m2r2==0.2.7

A Makefile is provided with the documentation. Running `make help` will produce
a list of available output formats, where each format may be given as a make
target.

For example, an HTML version of the documentation can be built via:

    cd meta-ewaol/documentation
    make html

This will produce HTML-formatted documentation into the
`*documentation/\_build/html` directory.

Please refer to the documentation for more information on the repository and
how to build EWAOL project images.

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
