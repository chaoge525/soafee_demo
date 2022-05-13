<!--
# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT
-->

# Project Cassini

Project Cassini is the open, collaborative, standards-based initiative to
deliver a seamless cloud-native software experience for devices based on Arm
Cortex-A.

## Cassini Documentation

To build a local version of the documentation, a Python build script that
automates the documentation build process is available under
`tools/build/doc-build.py`. It will generate an HTML version of the
documentation under `meta-cassini/public/`. This script, which is supported
on Ubuntu 18.04 LTS systems running Python 3.6 or higher, can be used to
generate the documentation via:

    ./tools/build/doc-build.py --project_root=./meta-cassini

For more information about the parameters, call the help function of the
script:

    ./tools/build/doc-build.py --help

To render and explore the documentation, simply open
`meta-cassini/public/index.html` in a web browser.

## Repository License

The repository's standard licence is the MIT license, under which most of the
repository's content is provided. Exceptions to this standard license relate to
files that represent modifications to externally licensed works (for example,
patch files). These files may therefore be included in the repository under
alternative licenses in order to be compliant with the licensing requirements of
the associated external works.

License details may be found in the [local license file](../license.rst), or as
part of the project documentation.

Contributions to the project should follow the same licensing arrangement.

## Contact

Please see the project documentation for the list of maintainers, as well as the
process for submitting contributions, raising issues, or receiving feedback and
support.
