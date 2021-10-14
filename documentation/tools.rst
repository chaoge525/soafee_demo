Tools
=====

The following tooling is provided as part of the ``meta-ewaol`` repository:

* `Documentation Build`_
* `Quality Assurance Checks`_
* `CI Build Tool`_

The tools are validated on the Ubuntu 18.04.6 LTS Linux distribution running
Python 3.6. Any particular dependencies required to run the tools are detailed
in their relevant sections, below.

.. _tools_documentation_build:

Documentation Build
-------------------

A script automating the documentation build process is available under
``tools/build/doc-build.py``. It will generate an HTML version of the
documentation under ``public/``. To use this script and generate the
documentation, you should use Python 3.6 or higher:

.. code-block:: console

    ./tools/build/doc-build.py

For more information about the parameters, call the help function of the
script:

.. code-block:: console

    ./tools/build/doc-build.py --help

To render and explore the documentation, simply open ``public/index.html`` in a
web browser.

Quality Assurance Checks
------------------------

The project provides tooling for running quality assurance (QA) checks on the
repository, in order to automatically validate that patches adhere to the
project's minimal code, submission, and documentation standards. The tooling is
provided as a set of Python scripts that can be found within the
``tools/qa-checks/`` directory of the repository.

The ``run-checks.py`` script can be used to perform the validation, for example:

    ``python3 ./tools/qa-checks/run-checks.py``

Detailed usage instructions can be found by passing ``--help`` to the script:

    ``python3 ./tools/qa-checks/run-checks.py --help``

In order to run the tool, the system must have installed Python 3 (version 3.6
or greater), the PyYAML Python package available via pip (5.4.1 is the
project's currently supported version), and Git.

The tooling runs a set of modular checks to validate different aspects of the
repository state. These are briefly described as follows:

* Commit message validation
    This check ensures that the commit message submitted with the patch adheres
    to the project's expected format.
* License and copyright header validation
    This check validates the inclusion of correctly formatted copyright and
    license headers for relevant project files.
* Python code quality validation
    This check ensures that all Python files within the project are compliant
    with the code-style conventions in PEP8 as validated by the pycodestyle
    utility.
* Shell script code quality validation
    This check ensures that all shell scripts and BATS files within the project
    produce no warnings when passed to the ShellCheck static analysis tool.
* Spelling validation
    This check aims to validate that there are no English word misspellings
    within the relevant project files (in particular, the appropriate files
    within the ``documentation/`` directory). A custom dictionary is maintained
    within the ``meta-ewaol-config/qa-checks`` directory that may be used to
    hold exceptions, should the check erroneously highlight valid technical
    terminology.

More detail on the validation steps performed by each check are included at the
top of each check Python module as in-source documentation. In addition, any
failed validation will output the specific reason for the failure, enabling it
to be fixed.

.. _tools_ci_build_tool:

CI Build Tool
-------------

The repository provides a Python script to support building EWAOL images for
Continuous Integration (CI) purposes:

  ``tools/build/kas-ci-build.py``

Given a space-separated list of build targets (each consisting of one or more
colon-separated YAML files present in the ``meta-ewaol-config/kas`` directory),
this script will run a containerized kas command for each target. The container
instance will configure and build the image, then package and deploy it along
with relevant build artifacts for use by later CI pipeline stages.

Dependencies
^^^^^^^^^^^^

The ``kas-ci-build.py`` script requires `Python 3`_ and the `Docker container
engine`_.

.. _Python 3: https://docs.python.org/3/using/unix.html
.. _Docker container engine: https://docs.docker.com/engine/install

All other dependencies of bitbake and kas will be handled by the docker
container image provided for kas:

* Image: ``ghcr.io/siemens/kas/kas``
* Image version: ``2.5``

The container engine, image source, and version are configurable as command
line arguments to the Python script. However, only Docker and the
aforementioned image and version are currently supported.

Building
^^^^^^^^

The script can be passed one or more build targets as its list of positional
arguments, where these build targets will be processed sequentially. Each build
target consists of one or more kas config files, concatenated via a colon (:),
which defines a desired build.

For example, to build an image for the n1sdp machine that includes the tests
build configuration, run:

.. code-block:: console

    ./tools/build/kas-ci-build.py n1sdp.yml:tests.yml

The available build config YAML files can be queried by passing to the script:

* ``--list-build-machines``
* ``--list-build-modifiers``

While all specified build config files must be available in the
``meta-ewaol-config/kas`` directory, if ``all`` is provided as the build target
, then all default CI build targets will be built. These default CI build
targets can be queried by passing:

* ``--list-ci-build-targets``

The results of these options are defined in
``meta-ewaol-config/ci/build-defs.yml``, meaning that changing this build
definitions file will update the default CI targets produced by ``all``.

By default, the script will set:

- Build output: ``ci-build/[build_id]/``
- bitbake ``SSTATE_CACHE``: ``ci-build/yocto-cache/sstate-cache/``
- bitbake ``DL_DIR``: ``ci-build/yocto-cache/downloads/``

The ``[build_id]`` is given by replacing each colon in the list of YAML
files for the build target with an underscore (_), and excluding all ``.yml``
file extensions. For example, the ``n1sdp.yml:tests.yml`` build target above
would result in a default build folder: ``ci-build/n1sdp_tests/``

The script can also be passed a set of optional named arguments, where these
arguments and their defaults can be found by passing  ``--help`` to
``tools/build/kas-ci-build.py``.

Note that by default no cache mirrors will be configured, and no artifacts will
be deployed.

Interactive Build Container
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The script allows the user to customize both the container engine arguments as
well as the kas commands that will be executed, via the following script
options:

* ``--engine-arguments '--foo bar="baz"' ['--bar' [...]]`` allows for additional
  engine-specific options to be passed to the container engine, e.g. ``-it`` to
  enable interactive access to a docker container.

* ``--kas-arguments ARGS`` customizes the arguments string passed to the kas
  command, allowing the user to run custom commands (e.g. to enter the bitbake
  environment by passing the ``shell`` string, or to pass specific options for
  running tests). The default string is ``build``.

Cache Mirrors
^^^^^^^^^^^^^

The Python build script supports read-only mirrors for the ``SSTATE_MIRRORS``
and ``SOURCE_MIRROR_URL`` mounted as local filepaths. Currently there is no
support for http(s) paths.

These paths can be provided using:

* ``--sstate-mirror=[path]``
* ``--downloads-mirror=[path]``

Here, ``[path]`` refers to the path on the local machine, not a path internal
to the container image execution.

As an alternative option, the environment variables ``SSTATE_MIRRORS`` and
``SOURCE_MIRROR_URL`` will be carried through to the containerized bitbake
build if set in the build environment. ``INHERIT`` and
``BB_GENERATE_MIRROR_TARBALLS`` are also passed through to bitbake using
``BB_ENV_EXTRAWHITE``.

Artifacts
^^^^^^^^^

Passing ``--deploy-artifacts`` to the build script will package and compress
files produced in the bitbake build directories:

* ``conf.tgz`` containing build config files stored within
  ``ci-build/[build_id]/conf/``
* ``logs.tgz`` containing the following log files:

    * ``bitbake-cookerdaemon.log``
    * ``console-latest.log``
    * All package build logs found in
      ``ci-build/[build_id]/tmp/work/*/*/*/temp/``
    * All ``pseudo.log`` files found in
      ``ci-build/[build_id]/tmp/work/*/*/*/pseudo/``

* ``images.tgz`` containing all files found in
  ``ci-build/[build_id]/tmp/deploy/images/[machine]/``

By default the artifacts will be deployed in ``ci-build/artifacts/``, but this
can be configured by passing:

    ``--artifacts-dir=[path]``

The artifacts path will be created if it does not exist.

Logging
^^^^^^^

The script produces a significant volume of build output to the terminal by
default. Much of this output can be redirected to a log file using:

    ``--log-file=[path]``

This will cause ``STDOUT`` to contain only important messages, while the log
file will receive the full output. If enabled, the log file should be consulted
to check the current progress of the containerized build.

The log path will be created if it does not exist.
