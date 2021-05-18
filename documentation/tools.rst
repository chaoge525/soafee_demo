Tools
=====

CI Build Tool
-------------

In addition to the kas config files, ``meta-ewaol-config`` contains a Python
script for enabling Continuous Integration (CI) builds:

    ``meta-ewaol-config/tools/kas-ci-build.py``

Given a space-separated list of build targets (each consisting of one or more
colon-separated YAML files), this script will run a containerised kas command
for each target. The container instance will configure and build the image,
then package and deploy it along with relevant build artifacts for use by later
CI pipeline stages.

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

    ./meta-ewaol-config/tools/kas-ci-build.py n1sdp.yml:tests.yml

The available build config YAML files can be queried by passing to the script:

* ``--list-build-machines``
* ``--list-build-modifiers``

While all specified build config files must be available in the
``meta-ewaol-config/kas`` directory, if ``all`` is provided as the build target,
then all default CI build targets will be built. These default CI build targets
can be queried by passing:

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
``./meta-ewaol-config/tools/kas-ci-build.py``.

Note that by default no cache mirrors will be configured, and no artifacts will
be deployed.

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
``SOURCE_MIRROR_URL`` will be carried through to the containerised bitbake
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
file will recieve the full output. If enabled, the log file should be consulted
to check the current progress of the containerised build.

The log path will be created if it does not exist.
