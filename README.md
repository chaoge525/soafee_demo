# Edge Workload Abstraction and Orchestration Layer (EWAOL)

EWAOL is the reference implementation for SOAFEE (Scalable Open Architecture
For Embedded Edge), the Arm lead industry initiative for extending cloud-native
software development to automotive, with a special focus on real-time and
functional safety. For more details on SOAFEE, please see <http://soafee.io>.

The Edge Workload Abstraction and Orchestration Layer (EWAOL) project provides
users with a standards based framework using containers for the deployment and
orchestration of applications on edge platforms.

## EWAOL Documentation

The project's documentation can be browsed at
<https://ewaol.sites.arm.com/meta-ewaol>.

To build a local version of the documentation, a Python build script that
automates the documentation build process is available under
`tools/build/doc-build.py`. It will generate an HTML version of the
documentation under `public/`. To use this script and generate the
documentation, you should use Python 3.6 or higher:

    ./tools/build/doc-build.py

For more information about the parameters, call the help function of the
script:

    ./tools/build/doc-build.py --help

To render and explore the documentation, simply open `public/index.html` in a
web browser.

## Repository License

The software is provided under an MIT license.

License details may be found in the [local license file](license.rst), or as
part of the project documentation.

Contributions to the project should follow the same license.

## Contact

Please see the project documentation for the list of maintainers, as well as the
process for contributions, bug reports, feedback and support.
