meta-ewaol
------------
The Edge Workload Abstraction and Orchestration Layer (EWAOL)

Introduction
------------
This repository contains layers and config for building EWAOL projects with
Yocto. To get started with EWAOL follow the quickstart guide, which can be
found in:
meta-ewaol/documentation/ewaol-quickstart.rst

The reStructuredText format can be built into a more readable format using
Sphinx as described below.

The following layers and repos are provided by the meta-ewaol repo:

docs:
    Documentation for the meta-ewaol repository. The documentation uses Sphinx:
    ```pip install -U Sphinx```
    You can then build the documentation as html files using ```make html```
    inside the docs directory, and viewing the output in docs/_build/html

    Other available output formats can be viewed using ```make help```

meta-ewaol-config:
    A repository containing kas and build configurations files for building
    EWAOL. See the quickstart guide for more information on how to use kas.

meta-ewaol-distro:
    Distro layer providing the configuration for the "ewaol" DISTRO, and
    general policies for the images and SDKs.

Dependencies
------------

The meta-ewaol-distro layer depends on:

    URI: git://git.yoctoproject.org/meta-virtualization
    branch: master
    revision: HEAD

    URI: git://git.yoctoproject.org/meta-security
    branch: master
    revision: HEAD

Contributing
------------
This project has not put in place a process for contributions currently. If you would like to contribute, please contact the maintainers.

Reporting bugs
------------

Maintainer(s)
------------
* Diego Sueiro <diego.sueiro@arm.com>
