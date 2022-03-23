..
 # Copyright (c) 2021-2022, Arm Limited.
 #
 # SPDX-License-Identifier: MIT

Validation
==========

Build-Time Kernel Configuration Check
-------------------------------------

After the kernel configuration has been produced during the build, it is checked
to validate the presence of necessary kernel configuration to comply with
specific EWAOL functionalities.

A list of required kernel configs is used as a reference, and compared against
the list of available configs in the kernel build. All reference configs need to
be present either as module (``=m``) or built-in (``=y``). A Bitbake warning
message is produced if the kernel is not configured as expected.

The following kernel configuration checks are performed:

* **Container engine support**:

  Check performed via:
  ``meta-ewaol-distro/classes/containers_kernelcfg_check.bbclass``.
  By default `Yocto Docker config`_ is used as the reference.

* **K3s orchestration support**:

  Check performed via:
  ``meta-ewaol-distro/classes/k3s_kernelcfg_check.bbclass``.
  By default `Yocto K3s config`_ is used as the reference.

* **Xen virtualization support** (available for EWAOL virtualization
  distribution images):

  Check performed via:
  ``meta-ewaol-distro/classes/xen_kernelcfg_check.bbclass``.
  By default `Yocto Xen config`_ is used as the reference.

.. _Yocto Docker config: http://git.yoctoproject.org/cgit/cgit.cgi/yocto-kernel-cache/tree/features/docker/docker.cfg
.. _Yocto K3s config: http://git.yoctoproject.org/cgit/cgit.cgi/meta-virtualization/tree/recipes-kernel/linux/linux-yocto/kubernetes.cfg
.. _Yocto Xen config: http://git.yoctoproject.org/cgit/cgit.cgi/yocto-kernel-cache/tree/features/xen/xen.cfg

Run-Time Integration Tests
--------------------------

The ``meta-ewaol-tests`` Yocto layer contains recipes and configuration for
including run-time integration tests into an EWAOL distribution, to be run
manually after booting the image.

The EWAOL run-time integration tests are a mechanism for validating EWAOL core
functionalities. The integration test suites included on an EWAOL distribution
image depend on its target architecture, as follows:

* Baremetal architecture:
    * `Container Engine Tests`_
    * `K3s Orchestration Tests`_ (testing single K3s node)
* Virtualization architecture:
    * `Container Engine Tests`_
    * `K3s Orchestration Tests`_ (testing K3s server on the Control VM,
      connected with a K3s agent on the Guest VM)
    * `Xen Virtualization Tests`_

The tests are built as a `Yocto Package Test`_ (ptest), and implemented using
the `Bash Automated Test System`_ (BATS).

.. _Yocto Package Test: https://wiki.yoctoproject.org/wiki/Ptest
.. _Bash Automated Test System: https://github.com/bats-core/bats-core

Running the Tests
^^^^^^^^^^^^^^^^^

In order to run the run-time validation tests, they must first be included on
the EWAOL distribution image. See the
:ref:`Reproduce Guide <user_guide/reproduce:Reproduce>` for guidance on
including the tests.

After booting the image, they can be run using the ptest framework via:

.. code-block:: console

   ptest-runner [test-suite-id]

If the test suite identifier (``[test-suite-id]``) is omitted, all integration
tests will be run.  For example, running ``ptest-runner`` on the Control VM of a
virtualization distribution image produces output such as the following:

.. code-block:: console

   $ ptest-runner
   START: ptest-runner
   [...]
   PASS:container-engine-integration-tests
   [...]
   PASS:k3s-integration-tests
   [...]
   PASS:virtualization-integration-tests
   [...]
   STOP: ptest-runner

.. note::
  As different EWAOL architectures support different test suites.
  ``ptest-runner -l`` is a useful command to list the available test suites on
  the image.

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
information will be provided in the output of type ``DEBUG``. The format of
these results are described in `Test Logging`_.

Test Logging
^^^^^^^^^^^^

Test suite execution will be logged to a ``[test-suite-id].log`` file within
the log directory of the test suite, which by default is ``logs/`` within the
test suite installation directory. The log is replaced on each new execution of
a test suite.

This log file will record the results of each top-level integration test, as
well as a result for each individual sub-test up until a failing sub-test is
encountered.

Each top-level result is formatted as:

    ``TIMESTAMP RESULT:[top_level_test_name]``

Each sub-test result is formatted as:

    ``TIMESTAMP RESULT:[top_level_test_name]:[sub_test_name]``

Where ``TIMESTAMP`` is of the format ``%Y-%m-%d %H:%M:%S`` (see
`Python Datetime Format Codes`_), and ``RESULT`` is
either ``PASS``, ``FAIL``, or ``SKIP``.

.. _Python Datetime Format Codes: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes

On a test failure, a debugging message of type ``DEBUG`` will be written to
the log. The format of a debugging message is:

    ``TIMESTAMP DEBUG:[top_level_test_name]:[return_code]:[stdout]:[stderr]``

Additional informational messages may appear in the log file with ``INFO`` or
``DEBUG`` message types, e.g. to log that an environment clean-up action
occurred.

Test Suites
^^^^^^^^^^^

The test suites are detailed below.

Container Engine Tests
""""""""""""""""""""""

The container engine test suite is identified as:

    ``container-engine-integration-tests``

for execution via ``ptest-runner`` or as a standalone BATS suite, as described
in `Running the Tests`_.

On an EWAOL virtualization distribution image, the container engine test suite
is available for execution on both the Control VM and the Guest VM. In addition,
as part of running the test suite on the Control VM, an extra test will be
performed which logs into the Guest VM and runs the container engine test suite
on it, thereby reporting any test failures of the Guest VM as part of the
Control VM's test suite execution.

The test suite is built and installed in the image according to the following
bitbake recipe within
``meta-ewaol-tests/recipes-tests/runtime-integration-tests/container-engine-integration-tests.bb``.

Currently the test suite contains three top-level integration tests, which run
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
|    2.1. Run a containerized, immediate (non-detached) network-based workload
         via the ``docker run`` command
|        - Create and start a container, re-using the existing image
|        - Update package lists within container from external network
| 3. ``run container engine integration tests on the Guest VM from the Control VM``
     is only executed on the Control VM. On the Guest VM this test is skipped.
     The test is composed of two sub-tests:
|    3.1. Check that Xendomains is initialized and the Guest VM is running via
          ``systemctl status`` and ``xendomains status``
|    3.2. Run the container engine integration tests on the Guest VM
|        - Uses an Expect script to log-in and execute the
           ``ptest-runner container-engine-integration-tests`` command
|        - This command will therefore run only the first and second top-level
           integration tests of the container engine integration test suite on
           the Guest VM

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
|  ``CE_TEST_GUEST_VM_NAME``: defines the Xen domain name and Hostname of the
    Guest VM
|    Only available when running the tests on an EWAOL virtualization
     distribution image
|    Represents the target Guest VM to test when executing the suite on the
     Control VM
|    Default: ``${EWAOL_GUEST_VM_HOSTNAME}1``
|    With standard configuration, the default Guest VM will therefore be
     ``ewaol-guest-vm1``

Container Engine Environment Clean-Up
*************************************

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

K3s Orchestration Tests
"""""""""""""""""""""""

The K3s test suite is identified as:

    ``k3s-integration-tests``

for execution via ``ptest-runner`` or as a standalone BATS suite, as described
in `Running the Tests`_.

The test suite is built and installed in the image according to the following
bitbake recipe within
``meta-ewaol-tests/recipes-tests/runtime-integration-tests/k3s-integration-tests.bb``.

Currently the test suite contains a single top-level integration test which
validates the deployment and high-availability of a test workload based on the
`Nginx`_ webserver. The test suite is dependent on the target EWAOL
architecture, as follows.

For baremetal distribution images, the K3s integration tests consider a
single-node cluster, which runs a K3s server together with its built-in worker
agent. The containerized test workload is therefore deployed to this node for
scheduling and execution.

For virtualization distribution images, the K3s integration tests consider a
cluster comprised of two nodes: the Control VM running a K3s server, and the
Guest VM running a K3s agent which is connected to the server. The containerized
test workload is configured to only be schedulable on the Guest VM, meaning that
the server on the Control VM orchestrates a test application which is deployed
and executed on the Guest VM. In addition to the same initialization procedure
that is carried out when running the tests on a baremetal distribution image,
initialization for virtualization distribution images includes connecting the
Guest VM's K3s agent to the Control VM's K3s server (if it is not already
connected). To do this, before the tests run, the Systemd service that provides
the K3s agent on the Guest VM is configured with a Systemd service unit override
that provides the IP and authentication token of the Control VM's K3s server,
and this service is then started. The K3s integration test suite therefore
expects that the target Guest VM is available when running on a virtualization
distribution image, and will not create one if it does not exist.

In both cases, the test suite will not be run until the appropriate K3s services
are in the 'active' state, and all 'kube-system' pods are either running, or
have completed their workload.

.. _Nginx: https://www.nginx.com/

| 1. ``K3s orchestration of containerized web service`` is composed of many
     sub-tests, grouped here by test area:
|    **Workload Deployment:**
|    1.1. Deploy test Nginx workload from YAML file via ``kubectl apply``
|    1.2. Ensure Pod replicas are initialized via ``kubectl wait``
|    1.3. Create NodePort Service to expose Deployment via
          ``kubectl create service``
|    1.4. Get the IP of the node running the Deployment via ``kubectl get``
|    1.5. Ensure web service is accessible on the node via ``wget``
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
|    1.13. Stop K3s server Systemd service via ``systemctl stop``
|    1.14. Ensure web service is still accessible via ``wget``
|    1.15. Restart the Systemd service via ``systemctl start``
|    1.16. Check K3S server is again responding to ``kubectl get``

The tests can be customized via environment variables passed to the execution,
each prefixed by ``K3S_`` to identify the variable as associated to the
K3s orchestration tests:

|  ``K3S_TEST_LOG_DIR``: defines the location of the log file
|  Default: ``/usr/share/k3s-integration-tests/logs``
|  Directory will be created if it does not exist
|  See `Test Logging`_
|  ``K3S_TEST_CLEAN_ENV``: enable test environment cleanup
|  Default: ``1`` (enabled)
|  See `K3s Environment Clean-Up`_
|  ``K3S_TEST_GUEST_VM_NAME``: defines the name of the Guest VM to use for the
   tests
|  Only available when running the tests on a virtualization distribution image
|  Default: ``${EWAOL_GUEST_VM_HOSTNAME}1``
|  With standard configuration, the default Guest VM will therefore be
   ``ewaol-guest-vm1``

K3s Environment Clean-Up
************************

A clean environment is expected when running the K3s integration tests, to
ensure that the system is ready to be validated. For example, the test suite
expects that the Pods created from any previous execution of the integration
tests have been deleted, in order to test that a new Deployment successfully
initializes new Pods for orchestration.

Therefore, if ``K3S_TEST_CLEAN_ENV`` is set to ``1`` (as is default), running
the test suite will perform an environment clean before and after the suite
execution.

The environment clean operation involves:

    * Deleting any previous K3s test Service
    * Deleting any previous K3s test Deployment, ensuring corresponding Pods
      are also deleted

For virtualization distribution images, additional clean up operations are
performed:

    * Deleting the Guest VM node from the K3s cluster
    * Stopping the K3s agent running on the Guest VM, and deleting any test
      Systemd service override on the Guest VM

If enabled then the environment clean operations will always be run, regardless
of test-suite success or failure.

Xen Virtualization Tests
""""""""""""""""""""""""

The Xen Virtualization test suite is identified as:

    ``virtualization-integration-tests``

for execution via ``ptest-runner`` or as a standalone BATS suite, as described
in `Running the Tests`_.

The test suite is built and installed in the image according to the following
bitbake recipe within
``meta-ewaol-tests/recipes-tests/runtime-integration-tests/virtualization-integration-tests.bb``.

The test suite is only available for images that target the virtualization
architecture.

Currently the test suite contains two top-level integration tests, which
validate a correctly running Guest VM, and validate that it can be managed
successfully from the Control VM. These tests are as follows:

| 1. ``validate Guest VM is running`` is composed of two sub-tests:
|    1.1. Check that Xen reports the Guest VM as running via
          ``xendomains status``
|    1.2. Check that the Guest VM is operational and has external network access
|        - Log-in to the Guest VM and access its interactive shell via
           ``xl console``
|        - Ping an external IP with the ``ping`` utility
| 2. ``validate Guest VM management`` is composed of five sub-tests:
|    2.1. Check that Xen reports the Guest VM as running via
          ``xendomains status``
|    2.2. Shutdown the Guest VM via ``systemctl stop``
|    2.3. Check that Xen reports the Guest VM as not running via
          ``xendomains status``
|    2.4. Start the Guest VM via ``systemctl start``
|    2.5. Check that Xen reports the Guest VM as running via
          ``xendomains status``

The tests can be customized via environment variables passed to the execution,
each prefixed by ``VIRT_`` to identify the variable as associated to the
virtualization integration tests:

|  ``VIRT_TEST_LOG_DIR``: defines the location of the log file
|  Default: ``/usr/share/virtualization-integration-tests/logs``
|  Directory will be created if it does not exist
|  See `Test Logging`_
|  ``VIRT_TEST_GUEST_VM_NAME``: defines the name of the Guest VM to use for the
   tests
|  Default: ``${EWAOL_GUEST_VM_HOSTNAME}1``
|  With standard configuration, the default Guest VM will therefore be
   ``ewaol-guest-vm1``

Prior to execution, the Xen Virtualization test suite expects the
``xendomains.service`` Systemd service to be running or in the process of
initializing. The test suite performs no environment clean-up operations.
