#!/usr/bin/env python3
#
# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

"""
This QA-check module receives one or more kas build configs, and runs the
Yocto Project's checker script 'yocto-check-layer' on a set of target layers,
in order to validate their compatibility with the Yocto Project.

The check uses the kas-runner.py tool to execute the yocto-check-layer script
within a kas Docker container.

The script is executed independently for each set of kas build configs (where
each set given as an element of the user-provided 'kas_configs' list. For each
set, all target layers (as given by the user-provided 'test_layers' list) are
checked.

Any failure found by yocto-check-layer will be output, detailing the kas build
configs and failing layer, as well as the particular test that failed and the
error message as produced by the script.
"""

import collections
import logging
import os
import re
import subprocess

import common
import abstract_check


class LayerCheck(abstract_check.AbstractCheck):
    """ Class to run the yocto-check-layer function on target Yocto layers. """

    name = "layer"

    @staticmethod
    def get_vars():
        return [
            abstract_check.CheckSetting(
                "kas_configs",
                is_list=True,
                required=True,
                message=("Colon-separated string of kas config YAML files that"
                         " provides the build context for the layer check, as"
                         " required by the kas-runner.py script.")
            ),
            abstract_check.CheckSetting(
                "test_layers",
                is_list=True,
                required=True,
                message=("Yocto layers to be tested, given by their directory"
                         " basenames.")
            ),
            abstract_check.CheckSetting(
                "machines",
                is_list=True,
                message=("Optional names of MACHINEs that should be used for"
                         " the layer check.")
            ),
            abstract_check.CheckSetting(
                "network_mode",
                required=False,
                message=("The docker container network mode to pass to the"
                         " kas-runner.py script. If not set, the default value"
                         " set by the kas-runner.py script will be used.")
            )
        ]

    def __init__(self, logger, *args, **kwargs):
        self.logger = logger
        self.__dict__.update(kwargs)

        self.script = os.path.join(os.path.dirname(__file__),
                                   "../build/kas-runner.py")

    def get_pip_dependencies(self):
        """ There are no non-standard Python package dependencies required to
            run the check. """
        return []

    def get_build_layers(self, kas_config, errors):
        """ This function passes the kas config files to kas, and extracts the
            resulting Yocto layers (according to the BBLAYERS variable). """

        kas_cmd = "shell --command \\\"bitbake-getvar BBLAYERS\\\""
        if self.network_mode:
            network_arg = f" --network_mode=\"{self.network_mode}\""
        else:
            network_arg = ""

        cmd = (f"{self.script} --project_root=\"{self.project_root}\""
               f"{network_arg} --kas_arguments \"{kas_cmd}\" {kas_config}")

        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   shell=True)
        stdout, _ = process.communicate()
        stdout = stdout.decode().strip()

        if process.returncode != 0:
            stdout = stdout.replace("\n", "\n\t")

            errors[kas_config].append(
                f"Could not get the build's BBLAYERS via: {cmd}")
            errors[kas_config].append(f"The output was:\n\t{stdout}")
            errors[kas_config].append(f"Return code was {process.returncode}")

            return None

        lines = re.findall("^BBLAYERS=\"(.*)\"$", stdout, re.M)

        if len(lines) != 1:
            stdout = stdout.replace("\n", "\n\t")

            errors[kas_config].append(
                f"Could not get the build's BBLAYERS via: {cmd}")
            errors[kas_config].append(f"The output was:\n\t{stdout}")

            return None

        layers = lines[0].strip().split()

        return layers

    def run(self):
        """ Run the yocto-check-layer function by invoking the kas-runner.py
            tools. The check is executed independently for each set of
            user-defined kas config files.

            If no errors are found, then report PASS.
            If any errors are found, then report FAIL and list the layers which
            failed, the tests that they failed on and the fail message(s). """

        self.logger.info(f"Running {self.name} check, this may take a while.")

        script_name = "kas-runner.py"
        script_dir = os.path.join(os.path.dirname(__file__), "../build/")
        self.script = common.find_executable(self.logger,
                                             script_name,
                                             script_dir)

        if self.script is None:
            self.logger.error("FAIL")
            self.logger.error(f"Could not find {script_name}.")
            return 1

        errors = collections.defaultdict(list)

        for kas_config in self.kas_configs:

            # Get the test layer directories as defined within the build given
            # by the kas config YAML files
            bblayers = self.get_build_layers(kas_config, errors)

            if bblayers is None:
                continue

            test_bblayers = list()
            for test_layer in self.test_layers:
                bblayer = next((layer for layer in bblayers
                               if test_layer == os.path.basename(layer)),
                               None)

                if bblayer is None:
                    errors[kas_config].append(
                        f"{test_layer}: Could not find this layer within the"
                        " bitbake build.")
                    continue

                test_bblayers.append(bblayer)

            if len(test_bblayers) != len(self.test_layers):
                continue

            dep_bblayers = [layer for layer in bblayers
                            if layer not in test_bblayers]

            # Create the command with the dependent layers as --dependency and
            # the test layers as positional arguments

            dependencies = "--dependency " + " ".join(dep_bblayers)
            test_layers_str = " ".join(test_bblayers)

            # The yocto-check-layer-wrapper script will create a temporary
            # directory in the parent directory of BUILDDIR
            # So set BUILDDIR to a subidrectory of build/
            shell_cmd = ("mkdir -p /work/kas_work_dir/build/layer_check &&"
                         " BUILDDIR=/work/kas_work_dir/build/layer_check"
                         " BB_NO_NETWORK=1"
                         f" yocto-check-layer-wrapper {test_layers_str}"
                         f" {dependencies} --no-auto-dependency")

            if self.machines:
                shell_cmd += f" --machines {' '.join(self.machines)}"

            kas_cmd = f"shell --command \\\"{shell_cmd}\\\""

            if self.network_mode:
                network_arg = f" --network_mode=\"{self.network_mode}\""
            else:
                network_arg = ""

            cmd = (f"{self.script} --project_root=\"{self.project_root}\""
                   f"{network_arg} --kas_arguments \"{kas_cmd}\" {kas_config}")

            self.logger.debug(f"Running layer check via: {cmd}")

            process = subprocess.Popen(cmd,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       shell=True)

            # Instead of doing some regex magic, just iterate through the
            # output and associate any failures to the layer under test

            new_layer_str = "Starting to analyze: "
            fail_str = "INFO: FAIL: "

            current_layer = None
            current_failed_test = None
            current_error = None

            # If the command fails, we want to print the full output.
            # The process.stdout is a raw stream, non-seekable BufferredReader
            # Therefore, record the output into a prefixed list of lines, as
            # they are read
            output_prefix = f"\t{os.path.basename(self.script)}:"
            output = list()

            for next_line in process.stdout:
                line = next_line.decode().strip()

                self.logger.debug(line)
                output.append(line)

                if new_layer_str in line:
                    current_layer = line.split(new_layer_str)[1]

                elif fail_str in line:
                    current_failed_test = line.split(fail_str)[1].split()[0]

                elif current_failed_test is not None:
                    if ("------------------------------" in line or
                            "==============================" in line):

                        if current_error is None:
                            # Start the error message
                            current_error = "\t"
                        else:
                            # Report the error message and reset

                            # To reduce the noise, remove repeat empty lines
                            # and indent the error
                            current_error = re.sub(r"\n\n\n+", "\n",
                                                   current_error)
                            current_error = current_error.replace("\n", "\n\t")
                            current_error = current_error.rstrip()

                            errors[kas_config].append(
                                f"{current_layer}:FAIL {current_failed_test}")
                            errors[kas_config].append(
                                f"The error message was:\n{current_error}")
                            current_failed_test = None
                            current_error = None
                    else:
                        # The current line is part of the error description
                        current_error += f"{line}\n"

            process.wait()

            if len(errors[kas_config]) == 0 and process.returncode != 0:

                prefixed_output = "\n".join([f"{output_prefix}{line}" for line
                                             in output])

                errors[kas_config].append(
                    ("yocto-check-layer returned non-zero error code"
                     f" ({process.returncode}) but no failed test was found."))

                errors[kas_config].append(f"The command was: {cmd}")

                errors[kas_config].append((" The output was:\n"
                                           f"{prefixed_output}"))

        if any(len(errs) > 0 for _, errs in errors.items()):
            self.logger.error("FAIL")
            for kas_config, kas_config_errors in errors.items():
                self.logger.error((f"Found check failures when validating"
                                   " target layers with kas configuration"
                                   f" {kas_config}:"))
                for error in kas_config_errors:
                    self.logger.error(error)
            return 1
        else:
            self.logger.info("PASS")
            return 0
