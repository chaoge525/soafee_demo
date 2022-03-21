#!/usr/bin/env python3
#
# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

import argparse
import copy
import enum
import glob
import os
import pathlib
import signal
import subprocess
import sys
import tarfile
import time
import yaml


class ContainerEngine:
    """ Simple class used to configure and run kas under a container """

    def __init__(self, engine, image, image_version):
        self.CONTAINER_NAME = f"kas_build.{int(time.time())}"
        self.args = [f"--rm --name {self.CONTAINER_NAME}"]
        self.container_engine = engine
        self.container_image = image
        self.container_image_version = image_version

    def add_arg(self, arg):
        """ Add a container engine run argument """
        print(f"Adding arg: {arg}")
        self.args.append(arg)

    def add_env(self, key, value):
        """ Add a container engine run environment argument """
        arg = f'--env {key}="{value}"'
        self.add_arg(arg)

    def add_volume(self, path_host, path_container, perms="rw", env_var=None):
        """ Add a container engine run volume argument.
        When 'env_var' is used, also add an environment argument with 'env_var'
        being the key and 'path_container' the value """

        path_host_absolute = path_host
        if not os.path.isabs(path_host):
            path_host_absolute = os.path.realpath(path_host)

        self.add_arg(f"--volume {path_host_absolute}:{path_container}:{perms}")
        if env_var:
            self.add_env(env_var, path_container)

    def run(self, kas_config, kas_command):
        """ Invoke the container engine with all arguments previously added to
            the object. """

        command = (f"{self.container_engine} run {' '.join(self.args)}"
                   f" {self.container_image}:{self.container_image_version}"
                   f" {kas_command} {kas_config}")

        def handle_interrupt(signum, frame):
            """ If this script is aborted while we have started a detached
                container subprocess, we should stop it before exiting """

            # Additional signals should be handled normally, so deregister
            signal.signal(signal.SIGINT, signal.default_int_handler)
            signal.signal(signal.SIGTERM, signal.SIG_DFL)

            print((f"Recieved signal ({signum}) during the run process, "
                  "sending a stop command to the build container"),
                  file=sys.tee)

            # Stop the container
            stop_cmd = [self.container_engine, "stop", self.CONTAINER_NAME]
            stop_proc = subprocess.Popen(stop_cmd,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         universal_newlines=True)

            stop_stdout, stop_stderr = stop_proc.communicate()
            print(stop_stdout)
            print(stop_stderr)

            stop_proc.wait()
            if stop_proc.returncode is None or stop_proc.returncode > 0:
                print(("Error: failed to stop the build container via:\n."
                       " ".join(stop_cmd)), file=sys.tee)

            exit(1)

        signal.signal(signal.SIGINT, handle_interrupt)
        signal.signal(signal.SIGTERM, handle_interrupt)

        # Start the build container
        print(command, file=sys.tee)
        proc = subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                shell=True)

        for next_line in proc.stdout:
            print(next_line.decode(), end='')

        proc.wait()

        # Deregister the signal handler as the subprocess is complete
        signal.signal(signal.SIGINT, signal.default_int_handler)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

        if proc.returncode is None or proc.returncode > 0:
            print((f"Error: container command: \n{command}\n"
                  f"Failed with return code {proc.returncode}"), file=sys.tee)
            return 1

        return 0


# Create a directory only if it doesn't already exist
def mk_newdir(path):
    if not os.path.exists(path):
        os.makedirs(path)


# Error to raise when a resolve function fails.
class RunnerResolveError(ValueError):
    pass


# Class containing all the details of how the value of a setting is found.
#
# * The default value of the setting {default}.
# * This is set with a command line argument with the flag --{setting_name} or
#   optional short flag {short_name}.
# * The value can also be set in config file using {setting_name}.
# * The message displayed in the help message is set using {help} and can
#   reference other RunnerSetting parameters (e.g. default=foo,
#   help="default {default}" -> help="default foo")
# * Any key words parameters other than those specified in init will be passed
#   directly to argparse.add_argument.
# * If positional=True the command line argument is set using positional args
# * If internal=True the setting is calculated in the script and is valid as a
#   command or in config files.
# * The resolve_function is for extra processing of the setting before it is
#   used such as transforming a path string to a Path object. This function is
#   also used to validate by raising a RunnerResolveError if the setting value
#   is invalid.
class RunnerSetting():

    def __init__(self, setting_name, short_name=None, default=None,
                 positional=False, help="", resolve_function=None,
                 internal=False, **kwargs):

        self.setting_name = setting_name
        self.short_name = short_name
        self.default = default
        self.positional = positional
        self.help = self.format_help(help)
        self.resolve_function = resolve_function
        self.arg_kwargs = kwargs
        self.internal = internal

    def format_help(self, help_string):
        return help_string.format_map(self.__dict__)

    # Add this setting to the argparser.
    def add_to_args(self, argparser):

        if self.internal:
            return

        arg_args = []

        if self.short_name is not None:
            arg_args.append(f"{self.short_name}")

        if self.positional:
            arg_args.append(self.setting_name)
        else:
            arg_args.append(f"--{self.setting_name}")

        arg_kwargs = self.arg_kwargs
        arg_kwargs["help"] = self.help

        argparser.add_argument(*arg_args, **arg_kwargs)

    # Call the resolve function for this setting.
    def resolve(self, config, value):
        if self.resolve_function is None:
            return value
        return self.resolve_function(config, value)


# Class containing all the details to make a boolean flag setting with negation
#
# * Using BoolRunnerSetting instead of RunnerSetting automatically sets up the
#   command line argument --{setting_name} to set not {default} and adds a
#   second command line argument --no_{setting_name} to set {default}.
# * Optional n_short_name allows a new short name for the negated command.
# * Optional n_help adds a seperate help message for the negated option
# * The default resolve function validates the setting is a boolean.
class BoolRunnerSetting(RunnerSetting):

    def validate_bool(config, value):
        if isinstance(value, bool):
            return value
        else:
            print(f"ERROR: Expected boolean but was '{value}'")
            raise RunnerResolveError()

    def __init__(self, setting_name, short_name=None, n_short_name=None,
                 default=False, help="", n_help="",
                 resolve_function=validate_bool, **kwargs):

        # Add required kwargs for a boolean flag if not already defined
        if "action" not in kwargs:
            kwargs["action"] = "store_const"
        if "const" not in kwargs:
            kwargs["const"] = not default

        super().__init__(setting_name, short_name=short_name, default=default,
                         help=help, resolve_function=resolve_function,
                         **kwargs)

        self.n_short_name = n_short_name
        self.n_help = self.format_help(n_help)

    def add_to_args(self, argparser):

        # Create a mutually exclusive group so both arguments cannot be passed
        # at once.
        group = argparser.add_mutually_exclusive_group()

        # Add normal argument to the group instead of the argparser
        super().add_to_args(group)

        # Create and add negated argument to the group
        arg_args = []

        if self.n_short_name is not None:
            arg_args.append(f"{self.n_short_name}")

        arg_args.append(f"--no_{self.setting_name}")

        arg_kwargs = self.arg_kwargs
        arg_kwargs["help"] = self.n_help
        arg_kwargs["dest"] = self.setting_name
        # Store default for the negated flag
        if "const" in arg_kwargs:
            arg_kwargs["const"] = self.default

        group.add_argument(*arg_args, **arg_kwargs)


# Class to contain the value of each setting.
#
# The value of settings are stored on this object as variables and can be
# accessed using runner_setting.{setting_name}.
# The settings_details contains all information needed to resolve and validate
# the setting values. This is initialized as a list of RunnerSettings.
# Note: The order of settings in setting_details_list matters for positional
# settings and for the order settings are resolved in.
# The value of settings is intialized to the default value definied in the
# settings_details and can be overriden using override_settings.
class RunnerSettings():

    def __init__(self, settings_details_list):
        self.settings_details = self.setup_settings_details(
            settings_details_list)

        self.set_to_default()
        self.resolved = False

    # Convert list of settings to a dictionary indexed by name.
    def setup_settings_details(self, settings_details):
        return {s.setting_name: s for s in settings_details}

    # Set the value of all settigns to their default values.
    def set_to_default(self):
        default_dict = {x[0]: x[1].default
                        for x in self.settings_details.items()}
        self.__dict__.update(default_dict)

    # Override settings
    def override_settings(self, new_values_dict):

        if not self.validate_incoming(new_values_dict):
            return False

        self.__dict__.update(new_values_dict)
        self.resolved = False
        return True

    # Validate that all settings being set exist and are not internal.
    def validate_incoming(self, config):
        is_valid = True
        for setting, value in config.items():
            if (setting not in self.settings_details or
                    self.settings_details[setting].internal):
                print(f"ERROR: Invalid setting '{setting}' specified")
                is_valid = False
                continue

        return is_valid

    # Call the resolve function on every setting
    def resolve_settings(self):
        if self.resolved:
            print(f"ERROR: settings already resolved.")
            raise RunerResolveError()
        for name, setting in self.settings_details.items():
            try:
                value = getattr(self, name)
                value = setting.resolve(self, value)
                setattr(self, name, value)
            except RunnerResolveError as e:
                print(f"ERROR: Cannot resolve '{name}': {value}")
                raise e
        self.resolved = True

    # Get a dictionary containing all settings
    def setting_values(self):
        return dict(filter(lambda i: i[0] in self.settings_details.keys(),
                           self.__dict__.items()))

    def __str__(self):
        return f"Runtime Config with {self.setting_values()}"


# Get a list of the runner settings details.
def get_settings_details():

    def resolve_config_reference(config, value):
        try:
            return value.format_map(config.setting_values())
        except KeyError as e:
            print(f"ERROR: Invalid config, string {value} couldn't be"
                  f" evaluated")
            raise RunnerResolveError(e)

    def resolve_to_path(_, value):
        return pathlib.Path(value).resolve()

    def resolve_config_reference_to_path(config, value):
        return resolve_to_path(config,
                               resolve_config_reference(config, value))

    def resolve_kas_file_paths(config, value):
        if isinstance(value, list):
            if len(value) > 1:
                print(f"ERROR: Only one set of kasfiles should be"
                      f" sepecified.")
                raise RunnerResolveError()
            if len(value) == 0:
                print(f"ERROR: No kasfiles specified.")
                raise RunnerResolveError()
            value = value[0]

        if bool(value) is False:
            print(f"ERROR: No kasfiles specified.")
            raise RunnerResolveError()

        kas_paths = string_to_paths(value)
        kas_paths = path_resolve_with_root(
            kas_paths, config.project_root)

        missing_kas_files = list(filter(
            lambda kpath:
                not (kpath.exists() and kpath.is_file()),
            kas_paths))

        if any(missing_kas_files):
            missing_kas_files_string = paths_to_string(missing_kas_files,
                                                       separator="\n")
            print((f"ERROR: The kas config files:\n"
                   f"{missing_kas_files_string}\n"
                   f"were not found."))
            raise RunnerResolveError()

        return kas_paths

    settings_details = [
        # Positional Settings
        RunnerSetting(
            "kasfile",
            positional=True,
            nargs='?',
            metavar='config.yml',
            default=None,
            resolve_function=resolve_kas_file_paths,
            help=("The path to the yaml files containing the config for"
                  " the kas build. Can provide multiple space-separated build"
                  " configs, where each config can be a colon (:) separated"
                  " list of .yml files to merge.")),

        # Flag Argument Settings
        RunnerSetting(
            "out_dir",
            short_name="-o",
            default="{project_root}/build",
            resolve_function=resolve_config_reference_to_path,
            help="Path to build directory (default: {default})."),

        RunnerSetting(
            "sstate_dir",
            short_name="-sd",
            default="{out_dir}/yocto-cache/sstate",
            resolve_function=resolve_config_reference_to_path,
            help=("Path to local sstate cache for this build (default:"
                  " {default}).")),

        RunnerSetting(
            "dl_dir",
            short_name="-dd",
            default="{out_dir}/yocto-cache/downloads",
            resolve_function=resolve_config_reference_to_path,
            help=("Path to local downloads cache for this build (default:"
                  " {default}).")),

        RunnerSetting(
            "sstate_mirror",
            short_name="-sm",
            help=("Path to read-only sstate mirror on local machine or the URL"
                  " of a server to be used as a sstate mirror.")),

        RunnerSetting(
            "downloads_mirror",
            short_name="-dm",
            help=("Path to read-only downloads mirror on local machine or the"
                  " URL of a server to be used as a downloads mirror.")),

        BoolRunnerSetting(
            "deploy_artifacts",
            short_name="-d",
            n_short_name="-D",
            default=False,
            help=("Generate artifacts for CI, and store in artifacts dir"
                  " (Off by default)"),
            n_help=("Disable --{setting_name} if enabled in configs")),

        RunnerSetting(
            "artifacts_dir",
            short_name="-a",
            default="{out_dir}/artifacts",
            resolve_function=resolve_config_reference_to_path,
            help=("Specify the directory to store the build logs, config and"
                  " images after the build if --deploy_artifacts is enabled"
                  " (default: {default}).")),

        RunnerSetting(
            "network_mode",
            short_name="-n",
            default="bridge",
            help=("Set the network mode of the container (default:"
                  " {default}).")),

        RunnerSetting(
            "container_engine",
            short_name="-e",
            default="docker",
            help="Set the container engine (default: {default})."),

        RunnerSetting(
            "container_image",
            short_name="-i",
            default="ghcr.io/siemens/kas/kas",
            help="Set the container image (default: {default})."),

        RunnerSetting(
            "engine_arguments",
            short_name="-ea",
            help=("Optional string of arguments for running the container,"
                  " e.g. --{setting_name} '--volume /host/dir:/container/dir"
                  " --env VAR=value'.")),

        RunnerSetting(
            "container_image_version",
            short_name="-v",
            default="3.0",
            help=("Set the container image version (default: {default})."
                  " Note: version {default} is the only version that"
                  " kas-runner.py is currently validated with.")),

        RunnerSetting(
            "number_threads",
            short_name="-j",
            default=f"{os.cpu_count()}",
            help=("Sets number of threads used by bitbake, by exporting"
                  " environment variable BB_NUMBER_THREADS = J. Usually it is"
                  " set to ({default}), unless a different number of threads"
                  " is set in a kas config file used for the build.")),

        RunnerSetting(
            "kas_arguments",
            short_name="-k",
            default="build",
            help=("Arguments to be passed to kas executable within the"
                  " container (default: {default}).")),

        RunnerSetting(
            "log_file",
            short_name="-log",
            help=("Write output to the given log file as well as to stdout"
                  " (default: {default}).")),

        RunnerSetting(
            "project_root",
            short_name="-r",
            default=pathlib.Path.cwd().resolve(),
            resolve_function=resolve_to_path,
            help="Project root path (default: {default})."),

        # Internal Settings
        RunnerSetting(
            "build_dir_name",
            internal=True,
            resolve_function=lambda config, _:
                "_".join(kpath.stem for kpath in config.kasfile)),

        RunnerSetting(
            "build_dir",
            internal=True,
            resolve_function=lambda config, _:
                config.out_dir / config.build_dir_name),
    ]

    return settings_details


def get_command_line_args(settings_details):

    desc = (f"{os.path.basename(__file__)} is used for building yocto based "
            "projects, using the kas container image to handle build "
            "dependencies.")
    usage = ("A kas config yaml file must be provided, and any optional "
             "arguments.")
    example = (f"Example:\n$ {os.path.basename(__file__)} "
               "path/to/kas-config1.yml:path/to/kas-config2.yml\nTo pull the "
               "required layers and build an image using the 2 provided "
               "configs.")

    # Parse Arguments and assign to args object
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=f"{desc}\n{usage}\n{example}\n\n")

    # Command line only arguments
    parser.add_argument(
        "-c",
        "--config",
        help="Load script parameters from file (default: %(default)s).")

    parser.add_argument(
        "-l",
        "--list_configs",
        action="store_true",
        dest="list_configs",
        help=("List all named configs from the config file specified with a"
              " '--config' parameter."))

    parser.add_argument(
        "-p",
        "--print",
        dest="print",
        help=("Print a parameter of the config being built. For this argument"
              " to work, a config must be selected"))

    # Add arguments for runner settings
    for runner_setting in settings_details:
        runner_setting.add_to_args(parser)

    return vars(parser.parse_args())


def merge_configs(base_config, override_config):
    merged_config = copy.copy(base_config)
    if not merged_config.override_settings(override_config):
        exit(1)
    return merged_config


# Get the configuration(s) to run this script with, as a combination
# of default parameter values, values from a config file, and values
# given in the command-line, with the below priority:
#
# The default config used is 'default_config'
# If given, values from configs in a config file override the defaults
# If no named config is provided, use just the first config in the file
# Command line arguments override values in all loaded configs
def get_configs(default_config, args):
    runner_configs = list()
    settings_details = default_config.settings_details
    config_names = dict()

    if args["config"]:
        # 'config' is a string like "path/to/config_file.yml[:named_config]"
        # check if named_config is specified
        config_input = args["config"].split(":", maxsplit=1)
        config_file = config_input[0]
        named_config = config_input[1] if len(config_input) == 2 else None

        with open(config_file, "r") as yaml_file:
            try:

                yaml_content = yaml.safe_load(yaml_file)
                header = yaml_content["header"]
                yaml_configs = yaml_content["configs"]
                config_names = yaml_configs.keys()

                # Check if header version is supported
                if header["version"] < 1:
                    print(f"ERROR: Incompatible version of config file")
                    exit(1)

                # Check that there are configs in this file
                if len(yaml_configs) == 0:
                    print(f"ERROR: No configs defined in config file")
                    exit(1)

                if named_config is not None:
                    selected_name = named_config
                else:
                    selected_name = next(iter(yaml_configs.keys()))
                config_dict = yaml_configs[selected_name]
                runner_configs.append(merge_configs(default_config,
                                                    config_dict))

            except KeyError:
                print(f"ERROR: Invalid configs {args['config']}")
                exit(1)

    else:
        runner_configs.append(default_config)

    # Overwrite values in all prior configs with command-line arguments
    # Ignore any None or empty-list arguments from the command-line parser
    # Ignore any args that are not valid external settings.
    supplied_args = dict(filter(lambda arg:
                                arg[0] in settings_details and (
                                    bool(arg[1]) is True or
                                    isinstance(arg[1], bool)
                                ), args.items()))
    runner_configs = [merge_configs(config, supplied_args)
                      for config in runner_configs]

    valid = True
    for settings in runner_configs:
        try:
            settings.resolve_settings()
        except RunnerResolveError:
            valid = False

    if not valid:
        print("ERROR: Invalid configuration")
        exit(1)

    return (runner_configs, config_names)


# Deploy generated artifacts like build configs and logs.
def deploy_artifacts(build_dir, build_artifacts_dir):

    # Collect config
    build_conf_dir = os.path.join(build_dir, "conf")

    if os.path.exists(build_conf_dir):
        tar_conf_filename = os.path.join(build_artifacts_dir, "conf.tgz")
        with tarfile.open(tar_conf_filename, "w:gz") as conf_tar:
            conf_tar.add(build_conf_dir,
                         arcname=os.path.basename(build_conf_dir))

        print("Deployed build configuration artifacts into "
              f"{tar_conf_filename}")
    else:
        print("No build configuration files to archive")

    tar_logs_filename = os.path.join(build_artifacts_dir, "logs.tgz")
    tar_image_filename = os.path.join(build_artifacts_dir, "images.tgz")
    with tarfile.open(tar_logs_filename, "w:gz") as log_tar,\
            tarfile.open(tar_image_filename, "w:gz") as image_tar:

        # Collect logs
        cooker_log = os.path.join(build_dir, "bitbake-cookerdaemon.log")
        if os.path.exists(cooker_log):
            arcname = os.path.join("logs/tmp", os.path.basename(cooker_log))
            log_tar.add(cooker_log, arcname=arcname)

        for tmp_dir in glob.glob(f"{build_dir}/tmp*"):
            console_dir = os.path.join(tmp_dir, "log/cooker")
            for path, dirs, files in os.walk(console_dir):
                if "console-latest.log" in files:

                    log_link = os.path.join(path, "console-latest.log")
                    log = os.path.join(path, os.readlink(log_link))

                    arcname = os.path.relpath(log_link, console_dir)
                    arcname = os.path.join(os.path.basename(tmp_dir), arcname)
                    arcname = os.path.join("logs", arcname)
                    log_tar.add(log, arcname=arcname)

            work_dir = os.path.join(tmp_dir, "work")
            for path, dirs, files in os.walk(work_dir):

                if "temp" in dirs:
                    log_dir = os.path.join(path, "temp")
                    arcname = os.path.relpath(path, work_dir)
                    arcname = os.path.join(os.path.basename(tmp_dir), arcname)
                    arcname = os.path.join("logs", arcname)
                    log_tar.add(log_dir, arcname=arcname)

                if "pseudo.log" in files:
                    pseudo_log = os.path.join(path, "pseudo.log")
                    arcname = os.path.relpath(pseudo_log, work_dir)
                    arcname = os.path.join(os.path.basename(tmp_dir), arcname)
                    arcname = os.path.join("logs", arcname)
                    log_tar.add(pseudo_log, arcname=arcname)

            print(f"Deployed build logs from {tmp_dir} into "
                  f"{tar_logs_filename}")

            # Collect images
            base_image_dir = os.path.join(tmp_dir, "deploy/images")
            if os.path.exists(base_image_dir):

                image_tar.add(base_image_dir,
                              arcname=os.path.basename(base_image_dir))

                print(f"Deployed images from {tmp_dir} into "
                      f"{tar_image_filename}")
            else:
                print("No image directory found, did not archive images")


# Convert string of paths with specified separator to a list of path objects
def string_to_paths(kas_files, separator=":"):
    return [pathlib.Path(kfile) for kfile in kas_files.split(separator)]


# Convert list of path objects to string with specified separator
def paths_to_string(paths, separator=":"):
    return separator.join(map(lambda path: str(path), paths))


# Get the highest common ancestor of two path objects
def _get_highest_common_ancestor(a, b):
    a_ancestors = a.parts
    b_ancestors = b.parts

    i = 0
    end = min(len(a_ancestors), len(b_ancestors))
    while i < end and a_ancestors[i] == b_ancestors[i]:
        i += 1

    return pathlib.Path(*a_ancestors[:i])


# Get the highest common ancestor of a list of path objects
def get_highest_common_ancestor(paths):
    highest_common_ancestor = paths[0]

    for path in paths[1:]:
        highest_common_ancestor = _get_highest_common_ancestor(
            path, highest_common_ancestor)

    return highest_common_ancestor


# Resolve list of path objects and combining relative paths with root.
def path_resolve_with_root(paths, root):
    absolute_paths = []
    for path in paths:
        if path.is_absolute():
            absolute_paths.append(path.resolve())
        else:
            absolute_paths.append((root / path).resolve())
    return absolute_paths


# Get the directory containing all kas_paths
def get_kas_file_common_dir(kas_paths, project_root):
    return get_highest_common_ancestor(kas_paths + [project_root])


# Convert kas_paths to be relative to container
def get_kas_container_paths(kas_paths, new_root, mount_path):
    paths_relative = []
    for path in kas_paths:
        paths_relative.append(path.relative_to(new_root))

    paths_inside = []
    for path in paths_relative:
        paths_inside.append(mount_path / path)

    return paths_inside


# Entry Point
def main():
    exit_code = 0

    settings_details = get_settings_details()

    # Parse command line arguments and split build configs
    # for different targets into a list
    args = get_command_line_args(settings_details)
    default_config = RunnerSettings(settings_details)
    configs, config_names = get_configs(default_config, args)

    # List the available configs if the list_config flag was selected
    if args["list_configs"]:
        if args["config"] is None:
            print("ERROR: No kas-runner configs specified!")
            exit(1)
        else:
            print(f"Build targets: "
                  f"{' '.join(elem for elem in config_names)}")
            exit(0)

    if len(configs) == 0:
        print("ERROR: No config was provided")
        exit(1)

    for config in configs:

        if config.log_file:
            mk_newdir(os.path.dirname(os.path.realpath(config.log_file)))
            log_file = open(config.log_file, "w")

            # By default, if we have a log file then only write to it
            # But provide a logger to write to both terminal
            # and the log file for important messages
            sys.tee = TeeLogger(LogOpt.TO_BOTH, log_file)
            sys.stdout = TeeLogger(LogOpt.TO_FILE, log_file)

        else:
            # If we have no log file,
            # write both stdout and tee to only terminal
            sys.tee = TeeLogger(LogOpt.TO_TERM)

        kas_file_common_dir = get_kas_file_common_dir(config.kasfile,
                                                      config.project_root)

        config_volume_mount = "/common_configs"
        kas_paths_inside = get_kas_container_paths(
            config.kasfile, kas_file_common_dir,
            pathlib.Path(config_volume_mount))

        # Print the argument
        if args["print"]:
            config_dict = config.setting_values()
            if args['print'] in config_dict:
                if len(configs) == 1:
                    print(f"{args['print']}: {config_dict[args['print']]}")
                else:
                    print(f"kasfile: {config.kasfile}\n"
                          f"{args['print']}: {config_dict[args['print']]}")
            else:
                print(f"ERROR: parameter {args['print']} cannot be found")
                exit(1)
            continue

        print(f"Starting build task: {paths_to_string(config.kasfile)}",
              file=sys.tee)

        # Create directories if they don't exist
        mk_newdir(config.out_dir)
        mk_newdir(config.build_dir)

        engine = ContainerEngine(config.container_engine,
                                 config.container_image,
                                 config.container_image_version)

        # Pass user and group ID to container engine env
        engine.add_env("USER_ID", os.getuid())
        engine.add_env("GROUP_ID", os.getgid())

        # Mount and set up workdir
        work_dir_name = "/work"
        engine.add_volume(config.project_root, work_dir_name)
        engine.add_arg(f"--workdir={work_dir_name}")
        engine.add_env("KAS_WORK_DIR", work_dir_name)

        # Mount config directory
        engine.add_volume(kas_file_common_dir, config_volume_mount, "ro")

        # Mount and set up build directory
        kas_build_dir_name = "/kas_build_dir"
        engine.add_volume(config.build_dir,
                          kas_build_dir_name)
        engine.add_env("KAS_BUILD_DIR", kas_build_dir_name)

        # Configure local caches
        engine.add_volume(config.sstate_dir,
                          "/sstate_dir",
                          env_var="SSTATE_DIR")
        mk_newdir(config.sstate_dir)

        engine.add_volume(config.dl_dir, "/dl_dir", env_var="DL_DIR")
        mk_newdir(config.dl_dir)

        # Set network mode
        network_mode = config.network_mode
        engine.add_arg(f"--network={network_mode}")

        # Configure cache mirrors
        if config.sstate_mirror:
            if config.sstate_mirror.startswith("http"):
                SSTATE_MIRRORS = (f"file://.* {config.sstate_mirror}/PATH;"
                                  "downloadfilename=PATH")
            else:
                path = "/sstate_mirrors"
                mk_newdir(config.sstate_mirror)
                engine.add_volume(config.sstate_mirror, path, "ro")
                SSTATE_MIRRORS = (f"file://.* file://{path}/PATH;"
                                  "downloadfilename=PATH")

            engine.add_env("SSTATE_MIRRORS", SSTATE_MIRRORS)

        if config.downloads_mirror:
            if config.downloads_mirror.startswith("http"):
                SOURCE_MIRROR_URL = config.downloads_mirror
            else:
                path = "/source_mirror_url"
                mk_newdir(config.downloads_mirror)
                engine.add_volume(config.downloads_mirror, path, "ro")
                SOURCE_MIRROR_URL = f"file://{path}"

            engine.add_env("SOURCE_MIRROR_URL", SOURCE_MIRROR_URL)
            engine.add_env('INHERIT', "own-mirrors")
            engine.add_env('BB_GENERATE_MIRROR_TARBALLS', "1")

        if config.engine_arguments:
            engine.add_arg(config.engine_arguments)

        if config.number_threads:
            engine.add_env('BB_NUMBER_THREADS', config.number_threads)

        kas_files_string = paths_to_string(kas_paths_inside)

        # Execute the command
        exit_code |= engine.run(kas_files_string, config.kas_arguments)

        # Grab build artifacts and store in artifacts_dir/buildname
        if config.deploy_artifacts:
            mk_newdir(config.artifacts_dir)

            build_artifacts_dir = os.path.join(config.artifacts_dir,
                                               config.build_dir_name)
            mk_newdir(build_artifacts_dir)

            deploy_artifacts(config.build_dir, build_artifacts_dir)

        print(f"Finished build task: {paths_to_string(config.kasfile)}\n",
              file=sys.tee)

    exit(exit_code)


class LogOpt(enum.Enum):
    TO_TERM = enum.auto()
    TO_FILE = enum.auto()
    TO_BOTH = enum.auto()


class TeeLogger(object):
    """ Logging class that outputs to either stdout or a log file, or both """

    def __init__(self, log_opt, log_file_handler=None):
        self.terminal = sys.stdout
        self.log_opt = log_opt
        self.log_file = log_file_handler

    def write(self, msg):
        if self.log_opt == LogOpt.TO_BOTH:
            self.terminal.write(msg)
            self.log_file.write(msg)

        elif self.log_opt == LogOpt.TO_TERM:
            self.terminal.write(msg)

        elif self.log_opt == LogOpt.TO_FILE:
            self.log_file.write(msg)

    def flush(self):
        self.terminal.flush()
        if self.log_file:
            self.log_file.flush()

    def __del__(self):
        if self.log_file and not self.log_file.closed:
            self.log_file.close()


if __name__ == "__main__":
    main()
