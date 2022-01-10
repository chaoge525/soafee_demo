Image Validation
================

The ``meta-ewaol-tests`` Yocto layer contains recipes and configuration for
including run-time integration tests into a target image, to be run manually
after booting the image, or within a Continuous Integration (CI) process.

The EWAOL integration tests provide a mechanism to validate that an image has
functionality that is compliant with the EWAOL project, where the
``meta-ewaol-tests`` Yocto layer is independently available for inclusion in
any desired Yocto image build process.

Currently, run-time integration tests are provided for validating the
functionality of:

* Docker Container Engine
* K3S Container Orchestration

These integration tests are described later in this document.

To support building and validating EWAOL images within CI environments, a Python
wrapper script is provided at ``tools/build/kas-ci-build.py`` that runs a
containerized kas command via Docker, and initializes sensible defaults for CI
purposes. The script is highly-configurable, and is documented at
:ref:`tools_ci_build_tool`.

In this page, instructions are provided both for running the kas tool directly,
as well as when using the provided Python wrapper script.

Building the Tests
------------------

As described in :ref:`builds:Image Builds`, the tests can be included by
appending ``ewaol-test`` to the build's ``DISTRO_FEATURES`` variable and
including the ``meta-ewaol-tests`` layer in the bitbake build, or simply by
passing ``tests.yml`` as a build modifier for a kas build.

The tests are built as a Yocto Package Test (ptest_), and implemented and
executed using the Bash Automated Test Suite (BATS_).

.. _ptest: https://wiki.yoctoproject.org/wiki/Ptest
.. _BATS: https://github.com/bats-core/bats-core

.. _validations_n1sdp_build_image_including_tests:

N1SDP: Build Image Including Tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To build images which include tests for the N1SDP board, follow the same
process as described in :ref:`quickstart_build_for_n1sdp`, but append an
additional configuration file ``meta-ewaol-config/kas/tests.yml`` to the kas
build command.

Therefore, to build images which include EWAOL validation tests for N1SDP:

  * Using ``kas`` directly:

    .. code-block:: console

      kas build meta-ewaol-config/kas/n1sdp.yml:meta-ewaol-config/kas/tests.yml

  * Using ``tools/build/kas-ci-build.py``:

    .. code-block:: console

      ./tools/build/kas-ci-build.py n1sdp.yml:tests.yml

To deploy the generated images on the board, please refer to the
:ref:`quickstart_deploy_on_n1sdp` section.

To execute the tests please refer to `N1SDP: Running Tests`_.

Running the Tests
-----------------

Once the tests are built and the image booted, they can be run on the target
using the ptest framework via:

.. code-block:: console

   ptest-runner [test-suite-id]

If the test suite identifier is omitted, all integration tests will be run.

Alternatively, the tests may be run as a standalone BATS script, via a runner
script included in the test suite directory:

.. code-block:: console

   /usr/share/[test-suite-id]/run-[test-suite-id]

Upon completion of the test-suite, a result indicator will be output by the
script, as one of two options: ``PASS:[test-suite-id]`` or
``FAIL:[test-suite-id]``.

A test suite consists of one or more 'top-level' BATS tests, which may be
composed of multiple assertions, where each assertion is considered a named
sub-test. If a sub-test fails, its individual result will be included in the
output with a similar format. In addition, if a test failed then debugging
information will be provided in the output with a ``DEBUG`` prefix. The format
of these results are described in `Test Logging`_.

.. _validations_n1sdp_running_tests:

N1SDP: Running Tests
^^^^^^^^^^^^^^^^^^^^

To run tests on N1SDP you need to:

* Build an image that include tests using the above instructions
  `N1SDP: Build Image Including Tests`_

* Boot an N1SDP board and deploy the image using the information from the
  :ref:`quickstart_deploy_on_n1sdp` section.

* Log-in as ``root`` without password, then execute all tests from the AP
  console with:

    .. code-block:: console

        $ ptest-runner
        START: ptest-runner
        [...]
        PASS:container-engine-integration-tests
        [...]
        PASS:k3s-integration-tests
        [...]
        STOP: ptest-runner

  * To run a specific integration test suite, provide its identifier as an argument
    to ``ptest-runner``.

Test Logging
------------

Test suite execution will be logged to a ``[test-suite-id].log`` file within
the log directory of the test suite, which by default is ``logs/`` within the
test suite directory.

This log file will record the results of each top-level integration test, as
well as a result for each individual sub-test up until a failing sub-test is
encountered.

Each top-level result is formatted as:

    ``TIMESTAMP RESULT:[top_level_test_name]``

Each sub-test result is formatted as:

    ``TIMESTAMP RESULT:[top_level_test_name]:[sub_test_name]``

Where ``TIMESTAMP`` is of the format ``%Y-%m-%d %H:%M:%S`` (see
`Python Datetime Format Codes`_), and ``RESULT`` is
either ``PASS`` or ``FAIL``.

.. _Python Datetime Format Codes: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes

On a test failure, a debugging message of type ``DEBUG`` will be written to
the log. The format of a debugging message is:

    ``TIMESTAMP DEBUG:[top_level_test_name]:[return_code]:[stdout]:[stderr]``

Additional informational messages may appear in the log file with ``INFO`` or
``DEBUG`` message types, e.g. to log that an environment clean-up action
occurred.

The test suites are detailed below.

Test Suites
-----------

Container Engine Tests
^^^^^^^^^^^^^^^^^^^^^^

The container engine test suite is identified as:

    ``container-engine-integration-tests``

for execution via ``ptest-runner`` or as a standalone BATS suite, as described
in `Running the Tests`_.

The test suite is built and installed in the image according to the following
bitbake recipe within
``meta-ewaol-tests/recipes-tests/runtime-integration-tests/container-engine-integration-tests.bb``.

Currently the test suite contains two top-level integration tests, which run
consecutively in the following order.

| 1. ``run container`` is composed of four sub-tests:
|    1.1. Run a containerized detached workload via the ``docker run`` command
|        - Pull an image from the network
|        - Create and start a container
|    1.2. Check the container is running via the ``docker inspect`` command
|    1.3. Remove the running container via the ``docker remove`` command
|        - Stop the container
|        - Remove the container from the container list
|    1.4. Check the container is not found via the ``docker inspect`` command
| 2. ``container network connectivity`` is composed of a single sub-test:
|    2.1 Run a containerized, immediate (non-detached) network-based workload
         via the ``docker run`` command
|        - Create and start a container, re-using the existing image
|        - Update package lists within container from external network

The tests can be customized via environment variables passed to the execution,
each prefixed by ``CE_`` to identify the variable as associated to the
container engine tests:

|  ``CE_TEST_IMAGE``: defines the container image
|    Default: ``docker.io/library/alpine``
|  ``CE_TEST_LOG_DIR``: defines the location of the log file
|    Default: ``/usr/share/container-engine-integration-tests/logs``
|    Directory will be created if it does not exist
|    See `Test Logging`_
|  ``CE_TEST_CLEAN_ENV``: enable test environment cleanup
|    Default: ``1`` (enabled)
|    See `Container Engine Environment Clean-Up`_

Container Engine Environment Clean-Up
"""""""""""""""""""""""""""""""""""""

A clean environment is expected when running the container engine tests. For
example, if the target image already exists within the container engine
environment, then the functionality to pull the image over the network will not
be validated. Or, if there are running containers from previous (failed) tests
then they may interfere with subsequent test executions.

Therefore, if ``CE_TEST_CLEAN_ENV`` is set to ``1`` (as is default), running
the test suite will perform an environment clean before and after the suite
execution.

The environment clean operation involves:

    * Determination and removal of all running containers of the image given by
      ``CE_TEST_IMAGE``
    * Removal of the image given by ``CE_TEST_IMAGE``, if it exists

If enabled then the environment clean operations will always be run, regardless
of test-suite success or failure.

K3S Orchestration Tests
^^^^^^^^^^^^^^^^^^^^^^^

The K3S test suite is identified as:

    ``k3s-integration-tests``

for execution via ``ptest-runner`` or as a standalone BATS suite, as described
in `Running the Tests`_.

The test suite is built and installed in the image according to the following
bitbake recipe within
``meta-ewaol-tests/recipes-tests/runtime-integration-tests/k3s-integration-tests.bb``.

Currently the test suite contains a single top-level integration test which
validates the deployment and high-availability of a test workload based on the
`Nginx`_ webserver. This integration test is described below.

As part of the test-suite initialization, the k3s systemd service will be
started (if it is not already). The test suite will not be run until the service
is in the 'active' state, and all 'kube-system' pods are either running, or have
completed their workload.

.. _Nginx: https://www.nginx.com/

| 1. ``K3S orchestration of containerized web service`` is composed of many
     sub-tests, grouped here by test area:
|    **Workload Deployment:**
|    1.1. Deploy test Nginx workload from YAML file via ``kubectl apply``
|    1.2. Ensure Pod replicas are initialized via ``kubectl wait``
|    1.3. Create Service to expose Deployment via ``kubectl expose``
|    1.4. Get IP of resulting Service via ``kubectl get``
|    1.5. Ensure web service is accessible via ``wget``
|    **Pod Failure Tolerance:**
|    1.6. Get random Pod name from Deployment name via ``kubectl get``
|    1.7. Delete random Pod via ``kubectl delete``
|    1.8. Ensure web service is still accessible via ``wget``
|    **Deployment Upgrade:**
|    1.9. Get image version of random Pod via ``kubectl get``
|    1.10. Upgrade image version of Deployment via ``kubectl set``
|    1.11. Ensure web service is still accessible via ``wget``
|    1.12. Get upgraded image version of random Pod via ``kubectl get``
|    **Server Failure Tolerance:**
|    1.13. Stop K3S server systemd service
|    1.14. Ensure web service remains accessible via ``wget``
|    1.15. Restart the systemd service
|    1.16. Check K3S server is again responding to ``kubectl get``

The tests can be customized via environment variables passed to the execution,
each prefixed by ``K3S_`` to identify the variable as associated to the
K3S orchestration tests:

|  ``K3S_TEST_LOG_DIR``: defines the location of the log file
|    Default: ``/usr/share/k3s-integration-tests/logs``
|    Directory will be created if it does not exist
|    See `Test Logging`_
|  ``K3S_TEST_CLEAN_ENV``: enable test environment cleanup
|    Default: ``1`` (enabled)
|    See `K3S Environment Clean-Up`_

K3S Environment Clean-Up
""""""""""""""""""""""""

A clean environment is expected when running the K3S integration tests, to
ensure that the system is ready to be validated. For example, the test suite
expects that the Pods created from any previous execution of the integration
tests have been deleted, in order to test that a new Deployment successfully
initializes new Pods for orchestration.

Therefore, if ``K3S_TEST_CLEAN_ENV`` is set to ``1`` (as is default), running
the test suite will perform an environment clean before and after the suite
execution.

The environment clean operation involves:

    * Deleting any previous K3S test Service
    * Deleting any previous K3S test Deployment, ensuring corresponding Pods
      are also deleted

If enabled then the environment clean operations will always be run, regardless
of test-suite success or failure.
