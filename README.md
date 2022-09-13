<!--
# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT
-->

# Edge Workload Abstraction and Orchestration Layer (EWAOL)

EWAOL is the reference implementation for SOAFEE (Scalable Open Architecture
For Embedded Edge), the Arm lead industry initiative for extending cloud-native
software development to automotive, with a special focus on real-time and
functional safety. For more details on SOAFEE, please see <http://soafee.io>.

The Edge Workload Abstraction and Orchestration Layer (EWAOL) project provides
users with a standards based framework using containers for the deployment and
orchestration of applications on edge platforms. The EWAOL software stack is
provided as a custom Linux distribution via the Yocto Project, and extends core
functionality provided by the Cassini Project (see
<https://www.arm.com/solutions/infrastructure/edge-computing/project-cassini>).

## EWAOL Documentation

The project's documentation can be browsed at
<https://ewaol.docs.arm.com>.

To build a local version of the documentation, a Python build script that
automates the documentation build process is available under
`tools/build/doc-build.py`. It will generate an HTML version of the
documentation under `public/`. This script, which is supported on Ubuntu 18.04
LTS systems running Python 3.6 or higher, can be used to generate the
documentation via:

    ./tools/build/doc-build.py

For more information about the parameters, call the help function of the
script:

    ./tools/build/doc-build.py --help

To render and explore the documentation, simply open `public/index.html` in a
web browser.

## Repository License

The repository's standard licence is the MIT license, under which most of the
repository's content is provided. Exceptions to this standard license relate to
files that represent modifications to externally licensed works (for example,
patch files). These files may therefore be included in the repository under
alternative licenses in order to be compliant with the licensing requirements of
the associated external works.

License details may be found in the [local license file](license.rst), or as
part of the project documentation.

Contributions to the project should follow the same licensing arrangement.

## Contact

Please see the project documentation for the list of maintainers, as well as the
process for submitting contributions, raising issues, or receiving feedback and
support.
