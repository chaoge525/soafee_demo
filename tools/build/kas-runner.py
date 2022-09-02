#!/usr/bin/env python3
#
# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

import argparse
import copy
import enum
import os
import pathlib
import platform
import signal
import subprocess
import sys
import tarfile
import time
import yaml


# Any function with external effects should be called with this methods so it
# does not have any external effects when dry run is enabled. The message
# provided to this method is always printed.
# * func_call: function containing external effect to run unless dry run.
# * message: message to print.
# * print_kwargs: dictionary with extra kwargs to pass to print function.
#
# Example Usage:
#     def func_external_effect():
#         foo()
#     run_external_effect(func_external_effect, "Perform foo external effect")
#     run_external_effect(lambda: bar(), "Perform bar external effect")
def run_external_effect(func_call, message, print_kwargs={}):
    print(message, **print_kwargs)
    if not is_dry_run:
        return func_call()


class RunSystem():

    def __init__(self, project_root, kas_arguments):

        self.project_root = project_root
        self.kas_arguments = kas_arguments

        self.key_paths = {}
        self.key_paths_access = {}
        self.env_vars = {}
        self.kas_files = []

    def add_path(self, key, path, access="rw", env_var=None):
        if isinstance(path, str):
            path = pathlib.Path(path)
        if not isinstance(path, pathlib.Path):
            print(f"ERROR: path {path} is not a valid string or pathlib.Path")
            exit(1)

        path = self.project_root / path

        self.key_paths[key] = path
        self.key_paths_access[key] = access

        if env_var is not None:
            self.add_env(env_var, f"{{{key}}}")

    def get_path(key):
        return self.key_paths[key]

    def add_env(self, env_name, env_value):

        self.env_vars[env_name] = str(env_value)

    def set_kas_files(self, kas_files):
        self.kas_files = kas_files

    def get_kas_files_string(self):
        return paths_to_string(self.kas_files)

    def get_env_string(self):
        return " ".join((f'{key}="{value.format_map(self.key_paths)}"'
                         for key, value in self.env_vars.items()))

    def build_command(self):

        env_string = self.get_env_string()
        kas_files_string = self.get_kas_files_string()

        return f"{env_string} kas {self.kas_arguments} {kas_files_string}"

    def _run(self, command):
        """ Internal run function that produces side effects so should be
            called using run_external_effect. """

        # Start the build container
        proc = subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                shell=True)

        for next_line in proc.stdout:
            print(next_line.decode(), end='')

        proc.wait()

        if proc.returncode is None or proc.returncode > 0:
            print((f"Error: command: \n{command}\n"
                   f"Failed with return code {proc.returncode}"), file=sys.tee)
            return 1

        return 0

    def run(self):
        """ Run command as a subprocess """

        command = self.build_command()

        if sys.tee.log_file:
            message = (f"\nRunning kas command:\n{command}\n\nRedirected"
                       f" command output to {sys.tee.log_file.name}\n")
        else:
            message = (f"\nRunning kas command:\n{command}\n")

        retcode = run_external_effect(lambda: self._run(command),
                                      message,
                                      dict(file=sys.tee))
        if retcode is None:
            retcode = 0
        return retcode


class ContainerEngine(RunSystem):
    """ Simple class used to configure and run kas under a container """

    def __init__(self, project_root, kas_arguments, image, image_version):

        super().__init__(project_root, kas_arguments)

        self.CONTAINER_NAME = f"kas_build.{int(time.time())}"
        self.engine_args = [f"--rm --name {self.CONTAINER_NAME}"]
        self.container_image = image
        self.container_image_version = image_version

    def add_arg(self, arg):
        """ Add a container engine run argument """
        print(f"Adding arg: {arg}")
        self.engine_args.append(arg)

    def add_env_arg(self, key, value):
        """ Add a container engine run environment argument """
        arg = f'--env {key}="{value}"'
        self.add_arg(arg)

    def add_volume_arg(self, path_host, path_container, perms="rw",
                       env_var=None):
        """ Add a container engine run volume argument.
        When 'env_var' is used, also add an environment argument with 'env_var'
        being the key and 'path_container' the value """

        path_host_absolute = path_host
        if not os.path.isabs(path_host):
            path_host_absolute = os.path.realpath(path_host)

        self.add_arg(f"--volume {path_host_absolute}:{path_container}:{perms}")
        if env_var:
            self.add_env(env_var, path_container)

    def build_command(self):
        key_paths_container = dict(
            ((key, f"/{key}") for key in self.key_paths))

        for key, host_path in self.key_paths.items():
            container_path = key_paths_container[key]
            access = self.key_paths_access[key]
            self.add_volume_arg(host_path, container_path, access)

        for env_key, value in self.env_vars.items():
            self.add_env_arg(env_key, value.format_map(key_paths_container))

        kas_files_string = self.get_kas_files_string()

        return (f"docker run {' '.join(self.engine_args)}"
                f" {self.container_image}:{self.container_image_version}"
                f" {self.kas_arguments} {kas_files_string}")

    def _run(self, command):
        """ Subset of the run function that produces side effects so should
            be called using run_external_effect. """

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
            stop_cmd = ["docker", "stop", self.CONTAINER_NAME]
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

        retcode = super()._run(command)

        # Deregister the signal handler as the subprocess is complete
        signal.signal(signal.SIGINT, signal.default_int_handler)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

        return retcode


# Create a directory only if it doesn't already exist
def mk_newdir(path):
    if not os.path.exists(path):
        run_external_effect(lambda: os.makedirs(path),
                            f"Create folder at {path}")


# Filter a dictionary using the filter_lambda function.
#
# This works much like a normal filter function but accepts and returns a
# dictionary instead of a list.
# * filter_lambda should accept two arguments (key, value) and return a bool
def dict_filter(filter_lambda, dictionary):
    return dict(filter(lambda kv: filter_lambda(*kv),
                       dictionary.items()))


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
        return self.filter_settings(self.__dict__)

    # Filter a dictionary to remove any keys that are not settings
    def filter_settings(self, dictionary):
        return dict_filter(lambda k, v: k in self.settings_details.keys(),
                           dictionary)

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

    def resolve_bool(config, value):
        if isinstance(value, bool):
            return value
        elif value is not None:
            if str(value).lower() in ["true", "1", "yes"] or value == 1:
                return True
            if str(value).lower() in ["false", "0", "no"] or value == 0:
                return False
        print(f"ERROR: Expected boolean but was '{value}'")
        raise RunnerResolveError()

    settings_details = [
        # Positional Settings
        RunnerSetting(
            "kasfile",
            positional=True,
            nargs='?',
            metavar='CONFIG_1:CONFIG_2:...',
            default=None,
            resolve_function=resolve_kas_file_paths,
            help=("Colon (:) separated set of kas config YAML file paths which"
                  " define the build configuration.")),

        # Flag Argument Settings
        RunnerSetting(
            "project_root",
            short_name="-r",
            metavar="PATH",
            default=pathlib.Path.cwd().resolve(),
            resolve_function=resolve_to_path,
            help="Project root path (default: {default})."),

        RunnerSetting(
            "number_threads",
            short_name="-j",
            metavar="N",
            default=f"{os.cpu_count()}",
            help=("Sets number of threads used by bitbake, by exporting"
                  " environment variable BB_NUMBER_THREADS = J. Usually it is"
                  " set to ({default}), unless a different number of threads"
                  " is set in a kas config file used for the build.")),

        RunnerSetting(
            "out_dir",
            short_name="-o",
            metavar="PATH",
            default="{project_root}/build",
            resolve_function=resolve_config_reference_to_path,
            help="Path to build directory (default: {default})."),

        RunnerSetting(
            "artifacts_dir",
            short_name="-a",
            metavar="PATH",
            default="{out_dir}/artifacts",
            resolve_function=resolve_config_reference_to_path,
            help=("Specify the directory to store the build logs, config and"
                  " images after the build if --deploy_artifacts is enabled"
                  " (default: {default}).")),

        RunnerSetting(
            "kas_arguments",
            short_name="-k",
            metavar="STR",
            default="build",
            help=("Arguments to be passed to kas executable within the"
                  " container (default: {default}).")),

        RunnerSetting(
            "sstate_dir",
            metavar="PATH",
            default="{out_dir}/yocto-cache/sstate",
            resolve_function=resolve_config_reference_to_path,
            help=("Path to local sstate cache for this build (default:"
                  " {default}).")),

        RunnerSetting(
            "dl_dir",
            metavar="PATH",
            default="{out_dir}/yocto-cache/downloads",
            resolve_function=resolve_config_reference_to_path,
            help=("Path to local downloads cache for this build (default:"
                  " {default}).")),

        RunnerSetting(
            "sstate_mirror",
            metavar="MIRROR",
            help=("Path to read-only sstate mirror on local machine or the URL"
                  " of a server to be used as a sstate mirror.")),

        RunnerSetting(
            "downloads_mirror",
            metavar="MIRROR",
            help=("Path to read-only downloads mirror on local machine or the"
                  " URL of a server to be used as a downloads mirror.")),

        RunnerSetting(
            "network_mode",
            metavar="MODE",
            default="bridge",
            help=("Set the network mode of the container (default:"
                  " {default}).")),

        RunnerSetting(
            "engine_arguments",
            metavar="STR",
            help=("Optional string of arguments for running the container,"
                  " e.g. --{setting_name} '--volume /host/dir:/container/dir"
                  " --env VAR=value'.")),

        RunnerSetting(
            "container_image",
            metavar="IMAGE",
            default="ghcr.io/siemens/kas/kas",
            help="Set the container image (default: {default})."),

        RunnerSetting(
            "container_image_version",
            metavar="VERSION",
            default="3.1",
            help=("Set the container image version (default: {default})."
                  " Note: version {default} is the only version that"
                  " kas-runner.py is currently validated with.")),

        RunnerSetting(
            "log_file",
            metavar="FILE",
            help=("Write output to the given log file as well as to stdout"
                  " (default: {default}).")),

        RunnerSetting(
            "containerize",
            metavar="BOOL",
            default=True,
            resolve_function=resolve_bool,
            help=("Run the kas command within a docker container (default:"
                  " {default}).")),

        RunnerSetting(
            "deploy_artifacts",
            metavar="BOOL",
            default=False,
            resolve_function=resolve_bool,
            help=("Archive and compress build artifacts, and deploy to"
                  " 'artifacts_dir' (default: {default}).")),

        RunnerSetting(
            "dry_run",
            metavar="BOOL",
            default=False,
            resolve_function=resolve_bool,
            help=("Print all the variables, arguments and run commands but"
                  " don't execute anything with external effects (default:"
                  " {default})")),

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


# Extend the RawDescriptionHelpFormatter to also format metavar so that the
# placeholder argument value is given once, even for arguments with a short and
# long name.
#
# For example, the help message:
#     -c CONFIG_FILE, --config CONFIG_FILE
# Instead becomes a more simple, easier to read version:
#     -c, --config CONFIG_FILE
class MetavarAndHelpFormatter(argparse.RawDescriptionHelpFormatter):

    # Modified implementation from the argparse module source
    def _format_action_invocation(self, action):
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            metavar, = self._metavar_formatter(action, default)(1)
            return metavar

        else:
            parts = []

            if action.nargs == 0:
                parts.extend(action.option_strings)

            else:
                default = self._get_default_metavar_for_optional(action)
                args_string = self._format_args(action, default)

                # First add the args
                parts.extend(action.option_strings)

                # Then append the placeholder value to the last arg string
                parts[-1] += f" {args_string}"

            return ', '.join(parts)


def get_command_line_args(settings_details):

    desc = (f"{os.path.basename(__file__)} is a wrapper script to support"
            " containerized and convenient execution of the 'kas' build tool"
            " for preparing and building Yocto-based projects.")
    example = (f"Example:\n$ ./{os.path.basename(__file__)} "
               "path/to/kas-config1.yml:path/to/kas-config2.yml\nTo pull the "
               "layer dependencies and build an image according to the 2 "
               "provided kas config files.")

    # Parse Arguments and assign to args object
    parser = argparse.ArgumentParser(
        formatter_class=MetavarAndHelpFormatter,
        description=f"{desc}\n{example}\n\n")

    # Command line only arguments
    parser.add_argument(
        "-l",
        "--list_configs",
        action="store_true",
        dest="list_configs",
        help=("List all named configs from the config file specified with a"
              " '--config' parameter."))

    parser.add_argument(
        "-c",
        "--config",
        metavar="FILE",
        help="Load script parameters from file (default: %(default)s).")

    parser.add_argument(
        "-p",
        "--print",
        dest="print",
        metavar="PARAM",
        help=("Once the tool's configuration process has been completed, print"
              " the resulting value of the target parameter. Execution will"
              " stop once the value has been printed."))

    # Add arguments for runner settings
    for runner_setting in settings_details:
        runner_setting.add_to_args(parser)

    return vars(parser.parse_args())


def merge_configs(base_config, override_config):
    merged_config = copy.copy(base_config)
    if not merged_config.override_settings(override_config):
        exit(1)
    return merged_config


# Remove any arguments that are equivalent to False but not booleans as these
# are likely to be default arguments (such as None or empty list).
def filter_empty_args(args):
    return dict_filter(
        lambda key, value: bool(value) is True or isinstance(value, bool),
        args)


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
    # Ignore any args that are not settings.
    supplied_args = filter_empty_args(args)
    setting_args = default_config.filter_settings(supplied_args)
    runner_configs = [merge_configs(config, setting_args)
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
    # For each file that matches one of the glob patterns,
    # return the full path and the path relative to basepath
    def find_files(basepath, patterns):
        base_folder = pathlib.Path(basepath).absolute()
        for pattern in patterns:
            for filename in base_folder.glob(pattern):
                relative_path = filename.relative_to(base_folder)
                yield filename, str(relative_path)

    # Build a tar file from the given iterator
    def build_tar(outfile, files):
        with tarfile.open(outfile, "w:gz") as tar:
            for filename, arcname in files:
                tar.add(filename, arcname)

    # Collect config
    tar_conf_filename = os.path.join(build_artifacts_dir, "conf.tgz")
    print("Deploying build configuration artifacts into "
          f"{tar_conf_filename}", file=sys.tee)
    build_tar(tar_conf_filename, find_files(build_dir, ['conf']))

    # Collect logs
    tar_logs_filename = os.path.join(build_artifacts_dir, "logs.tgz")
    log_patterns = [
        'bitbake-cookerdaemon.log',
        'tmp*/log',
        'tmp*/work/**/temp/log.*',
        'tmp*/work/**/pseudo.log',
        'tmp*/work/**/testimage',
    ]
    print(f"Deploying build logs into {tar_logs_filename}", file=sys.tee)
    build_tar(tar_logs_filename, find_files(build_dir, log_patterns))

    # Collect images
    def find_image_files():
        for deploydir, _ in find_files(build_dir, ['tmp*/deploy']):
            # images.tgz only contains the "images" subdirectories
            yield from find_files(deploydir, ['images'])
    tar_image_filename = os.path.join(build_artifacts_dir, "images.tgz")
    print(f"Deploying images into {tar_image_filename}", file=sys.tee)
    build_tar(tar_image_filename, find_image_files())


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


# Format a dictionary to a string with each line representing a key value pair.
# Each key can be padded to the length of the longest key.
# * dictionary: Dictionary to format
# * line_format: Format of each key value pair (e.g. "{key}{padding}: {value}")
def format_dict(dictionary, line_format):

    longest_key = len(max(dictionary.keys(), key=len))

    description_string = ""
    for key, value in dictionary.items():
        padding = " " * (longest_key - len(key))
        description_string += line_format.format(
            key=key, value=value, padding=padding)
    return description_string


# Print various details about the running environment.
def print_environment():

    env_dict = {
        "script": pathlib.Path(__file__).resolve(),
        "command": " ".join(sys.argv),
        "python_version": platform.python_version(),
        "system": platform.platform(),
        "working_dir": pathlib.Path.cwd(),
    }

    env_description = format_dict(env_dict, "\t{key}{padding}: {value}\n")
    env_str = (f"Script Environment: \n{env_description}")
    print(env_str)


# Print the supplied args as ready by the argparser (with empty args filtered)
def print_args(args):
    supplied_args = filter_empty_args(args)

    arg_description = format_dict(supplied_args, "\t{key}{padding}: {value}\n")
    arg_str = (f"Arguments Recieved:\n{arg_description}")
    print(arg_str)


# Print all the settings in a config seperated by whether they are set
# internally or externally.
def print_config(config):

    values = config.setting_values()
    settings = config.settings_details

    external_values = {}
    internal_values = {}

    for name, setting in settings.items():
        if setting.internal:
            internal_values[name] = values[name]
        else:
            external_values[name] = values[name]

    external_description = format_dict(external_values,
                                       "\t\t{key}{padding}: {value}\n")
    internal_description = format_dict(internal_values,
                                       "\t\t{key}{padding}: {value}\n")

    config_str = ("Config containing:\n\tExternal Parameters:\n"
                  f"{external_description}\tInternal Variables:\n"
                  f"{internal_description}")

    print(config_str)


# Entry Point
def main():
    exit_code = 0

    settings_details = get_settings_details()

    # Parse command line arguments and split build configs
    # for different targets into a list
    args = get_command_line_args(settings_details)

    global is_dry_run
    is_dry_run = args["dry_run"]
    if is_dry_run:
        print("Entered dry run mode\n")

    print_environment()
    print_args(args)

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

        print_config(config)

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

        if config.containerize:
            run_system = ContainerEngine(config.project_root,
                                         config.kas_arguments,
                                         config.container_image,
                                         config.container_image_version)

            kas_file_common_dir = get_kas_file_common_dir(config.kasfile,
                                                          config.project_root)
            # Translate kas files to container
            config_volume_key = "common_configs"
            kas_paths_inside = get_kas_container_paths(
                config.kasfile, kas_file_common_dir,
                pathlib.Path("/", config_volume_key))
            run_system.add_path(config_volume_key, kas_file_common_dir,
                                access="ro")
            run_system.set_kas_files(kas_paths_inside)

            # Pass user and group ID to container engine env
            run_system.add_env("USER_ID", os.getuid())
            run_system.add_env("GROUP_ID", os.getgid())

            # Set network mode
            run_system.add_arg(f"--network={config.network_mode}")

            if config.engine_arguments:
                run_system.add_arg(config.engine_arguments)

        if not config.containerize:
            run_system = RunSystem(config.project_root, config.kas_arguments)
            run_system.set_kas_files(config.kasfile)

        # Mount and set up workdir
        run_system.add_path("work/kas_work_dir",
                            config.project_root,
                            env_var="KAS_WORK_DIR")

        if config.containerize:
            run_system.add_arg(f"--workdir=/work/kas_work_dir")

        # Mount and set up build directory
        run_system.add_path("work/kas_build_dir",
                            config.build_dir,
                            env_var="KAS_BUILD_DIR")

        # Configure local caches
        mk_newdir(config.sstate_dir)
        run_system.add_path("sstate_dir", config.sstate_dir,
                            env_var="SSTATE_DIR")

        mk_newdir(config.dl_dir)
        run_system.add_path("dl_dir", config.dl_dir, env_var="DL_DIR")

        # Configure cache mirrors
        if config.sstate_mirror:
            if config.sstate_mirror.startswith("http"):
                # Formatted now so not set by run_system.add_env
                SSTATE_MIRRORS = (f"file://.* {config.sstate_mirror}/PATH;"
                                  "downloadfilename=PATH")
            else:
                mk_newdir(config.sstate_mirror)
                run_system.add_path("sstate_mirrors", config.sstate_mirror,
                                    access="ro")
                # Not formatted now so set by run_system.add_env
                SSTATE_MIRRORS = ("file://.* file://{sstate_mirrors}/PATH;"
                                  "downloadfilename=PATH")

            run_system.add_env("SSTATE_MIRRORS", SSTATE_MIRRORS)

        if config.downloads_mirror:
            if config.downloads_mirror.startswith("http"):
                SOURCE_MIRROR_URL = config.downloads_mirror
            else:
                mk_newdir(config.downloads_mirror)
                run_system.add_path("source_mirror_url",
                                    config.downloads_mirror, access="ro")
                SOURCE_MIRROR_URL = "file://{source_mirror_url}"

            run_system.add_env("SOURCE_MIRROR_URL", SOURCE_MIRROR_URL)
            run_system.add_env('INHERIT', "own-mirrors")
            run_system.add_env('BB_GENERATE_MIRROR_TARBALLS', "1")

        if config.number_threads:
            run_system.add_env('BB_NUMBER_THREADS', config.number_threads)

        exit_code |= run_system.run()

        # Grab build artifacts and store in artifacts_dir/buildname
        if config.deploy_artifacts:
            mk_newdir(config.artifacts_dir)

            build_artifacts_dir = os.path.join(config.artifacts_dir,
                                               config.build_dir_name)
            mk_newdir(build_artifacts_dir)

            run_external_effect(
                lambda:
                    deploy_artifacts(config.build_dir, build_artifacts_dir),
                f"Deploying artifacts for {paths_to_string(config.kasfile)}",
                dict(file=sys.tee))

        print(f"Finished build task: {paths_to_string(config.kasfile)}\n",
              file=sys.tee)

    if is_dry_run:
        print("Finished dry run", file=sys.tee)

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
