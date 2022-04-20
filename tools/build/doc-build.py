#!/usr/bin/env python3
#
# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

import argparse
import os
import pathlib
import logging
import subprocess
import shutil
import sys
import tempfile

path = f'{os.path.dirname(os.path.abspath(__file__))}/../common'
sys.path.append(path)

import modules_virtual_env  # noqa: E402


def generate_venv_script_args_from_opts(opts):
    """ In order to call this script from the virtual environment, convert the
        processed options to a string array, and replace --venv with --no_venv.
        """

    venv_arguments = {'venv', 'keep_venv', 'requirements'}

    args = []
    for opt, value in vars(opts).items():
        if opt in venv_arguments:
            # remove the venv arguments
            continue
        elif opt == "no_venv":
            # set the no_venv argument
            arg = opt
        elif value is None:
            continue
        else:
            arg = f"{opt}={value}"

        args.append(f"--{arg}")

    return args


def resolve_path(path_string, opts):
    """ Resolve a path passed from the commandline into a pathlib.Path object.
        path_string is formatted with opts to allow references to other command
        line options such as '{project_root}/documentation' converting to
        '/path/to/root/documentation'. """

    path_string_formatted = path_string.format_map(vars(opts))
    return pathlib.Path(path_string_formatted).resolve()


def parse_options(logger):

    loglevels = {
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG
    }

    desc = ("doc-build.py is used to build documentation using the sphinx "
            "tool. By default, documentation is built from ./documentation "
            "into the ./public directory. By default, a virtual Python "
            "environment is created to install the Python packages necessary "
            "to build the documentation.")
    usage = ("Optional arguments can be found by passing --help to the script")
    example = ("Example:\n$ ./doc-build.py --log=debug\n"
               "to build the documentation with maximum verbosity")

    # Parse Arguments and assign to args object
    parser = argparse.ArgumentParser(
        prog=os.path.basename(__file__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=f"{desc}\n{usage}\n{example}\n\n")

    venv_only_group = parser.add_argument_group("venv only arguments")

    venv_only_group.add_argument(
        "--venv",
        required=False,
        help=("Provide a Python virtual environment directory"
              " in which to run the build (default: auto"
              " generate a new virtual environment directory)."
              " Cannot be passed with --no_venv."))

    parser.add_argument(
        "--no_venv",
        action="store_true",
        help=("Run the build directly in the calling context"
              " without using a Python virtual environment."
              " Cannot be passed with --venv."))

    venv_only_group.add_argument(
        "--keep_venv",
        action="store_true",
        default=False,
        help=("Do not delete the temporary Python virtual"
              " environment directory after the build has"
              " been completed (Default: False)"))

    parser.add_argument("--log", default="info",
                        choices=["debug", "info", "warning"],
                        help="Set log level.")

    requirements_default = "{documentation_dir}/requirements.txt"
    venv_only_group.add_argument(
        "--requirements",
        default=requirements_default,
        help=("Override the location of the file containing"
              " the pip requirements for the Python virtual"
              f" environment (Default: {requirements_default})."))

    project_root_default = pathlib.Path.cwd()
    parser.add_argument("--project_root",
                        default=project_root_default,
                        help=("Set the root project directory (Default:"
                              f" {project_root_default})."))

    documentation_dir_default = "{project_root}/documentation"
    parser.add_argument("--documentation_dir",
                        default=documentation_dir_default,
                        help=("Set the documentation directory (Default:"
                              f" {documentation_dir_default})."))

    output_dir_default = "{project_root}/public"
    parser.add_argument("--output_dir",
                        default=output_dir_default,
                        help=("Set the output directory (Default:"
                              f" {output_dir_default})."))

    opts = parser.parse_args()

    if opts.venv is not None and opts.no_venv is True:
        logger.error((f"Cannot provide a path via --venv while also setting"
                      " --no_venv."))
        exit(1)

    logger.setLevel(loglevels.get(opts.log.lower()))

    opts.project_root = pathlib.Path(opts.project_root).resolve()
    opts.documentation_dir = resolve_path(opts.documentation_dir, opts)
    opts.output_dir = resolve_path(opts.output_dir, opts)
    opts.requirements = resolve_path(opts.requirements, opts)

    return opts


def parse_requirements_file(requirements_file):

    if not os.path.exists(requirements_file):
        logger.error(f"Dependency file {requirements_file} does not exist.")
        exit(1)
    if not os.path.isfile(requirements_file):
        logger.error(f"Dependency file {requirements_file} is not a file.")
        exit(1)

    requirements = []

    with open(requirements_file, 'r') as f:
        for line in f:
            # Remove comments and leading/trailing whitespace
            requirement = line.partition("#")[0].strip()
            if requirement != "":
                requirements.append(requirement)

    return requirements


def main(logger, opts):
    exit_code = 0

    script_path = os.path.abspath(__file__)
    sphinx_path = None

    if opts.no_venv:
        try:
            os.chdir(opts.project_root)
        except OSError as e:
            logger.error(f"Project root {opts.project_root} not found")
            exit(1)

        if "VENV_BIN" in os.environ:
            sphinx_path = shutil.which("sphinx-build",
                                       path=os.environ["VENV_BIN"])
        else:
            sphinx_path = shutil.which("sphinx-build")

        if sphinx_path is None:
            logger.error(f"Could not find sphinx-build executable")
            exit(1)

        # cleaning and building the documentation
        cmd = (f"{sphinx_path} -a -E -W --keep-going -b html "
               f"{opts.documentation_dir} {opts.output_dir}")

        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   shell=True,
                                   universal_newlines=True)

        (cmdout, cmderr) = process.communicate()
        exit_code = process.returncode

        if exit_code != 0:
            logger.error("Error while building the documentation using"
                         f" '{cmd}' : {cmdout}")
        else:
            logger.info(f"Files generated in {opts.output_dir}")

    else:
        pip_requirements = {
            "documentation": parse_requirements_file(opts.requirements)}

        args = generate_venv_script_args_from_opts(opts)
        arg_str = " ".join(args)

        virt_env = modules_virtual_env.ModulesVirtualEnv(script_path,
                                                         arg_str,
                                                         pip_requirements,
                                                         logger)

        venv_dirname = None
        if opts.venv is not None:
            venv_dirname = opts.venv
            if not os.path.isdir(venv_dirname):
                logger.error("Cannot find the given venv directory:"
                             f"{venv_dirname}. Aborting.")
                exit(1)
            logger.debug(f"Using existing venv directory: {venv_dirname}")
        else:
            venv_dirname = tempfile.mkdtemp()
            if opts.keep_venv:
                logger.info(f"Created new venv directory: {venv_dirname}")
            else:
                logger.debug(f"Created new venv directory: {venv_dirname}")

        virt_env.create(venv_dirname)
        exit_code = virt_env.returncode

        if opts.venv is None and opts.keep_venv is False:
            shutil.rmtree(venv_dirname)
            logger.debug(f"Deleted the venv directory: {venv_dirname}")

    exit(exit_code)


if __name__ == "__main__":
    log_format = "%(levelname)-8s:%(filename)-24s:%(message)s"
    logging.basicConfig(format=log_format)
    logger = logging.getLogger(__name__)

    opts = parse_options(logger)

    main(logger, opts)
