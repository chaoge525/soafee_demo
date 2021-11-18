#!/usr/bin/env python3
#
# Copyright (c) 2021, Arm Limited.
#
# SPDX-License-Identifier: MIT

import argparse
import enum
import os
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

        command = f"{self.container_engine} run {' '.join(self.args)}\
                    {self.container_image}:{self.container_image_version}\
                    {kas_command} {kas_config}"

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


# replaces colon seperated names of kas config files with full paths
def kasconfig_format(kasfiles, project_root, mnt_dir):

    def format_path(kfile):
        return os.path.join(mnt_dir,
                            kfile)

    return ":".join(map(format_path, kasfiles[0].split(":")))


# Function formatting a string to display it on this tool's help. When the
# argument's default value contains a another argument as a prefix, this
# prefix shouldn't be replaced with its value to make the dependencies clear
# to the user.
def prettify_string_vars(string, prefix_name):
    var_length = len(prefix_name)
    printed_string = string[4 + var_length:]
    printed_string = f"{{{prefix_name}}}{printed_string}"

    return printed_string


# Class to implement a self-referential dictionary, where string-values
# may reference other key-value pairs within the dictionary, by
# including a substring with the format: "%(key)s".
# References are evaluated lazily, each time a key's corresponding value
# is acquired.
class ArgumentsDictionary(dict):
    def __getitem__(self, item):
        value = dict.__getitem__(self, item)
        if isinstance(value, str):
            try:
                evaluated_str = value % self
                return evaluated_str
            except KeyError:
                return value
        else:
            return value

    # The is_valid() function checks if all defined string references exist
    # within the dictionary
    def is_valid(self):
        for value in self.values():
            if isinstance(value, str):
                try:
                    evaluated_str = value % self
                except KeyError:
                    return False
        return True


def get_command_line_args(default_config):

    desc = (f"{os.path.basename(__file__)} is used for building yocto based "
            "projects, using the kas container image to handle build "
            "dependencies.")
    usage = ("A kas config yaml file must be provided, and any optional "
             "arguments.")
    example = (f"Example:\n$ {os.path.basename(__file__)} "
               "path/to/kas-config1.yml:path/to/kas-config2.yml\nTo pull the "
               "required layers and build an image using the 2 provided "
               "configs.")

    formatted_out_dir = prettify_string_vars(
                        dict.__getitem__(default_config, 'out_dir'),
                        'project_root')

    formatted_sstate_dir = prettify_string_vars(
                        dict.__getitem__(default_config, 'sstate_dir'),
                        'out_dir')

    formatted_dl_dir = prettify_string_vars(
                        dict.__getitem__(default_config, 'dl_dir'),
                        'out_dir')

    formatted_artifacts_dir = prettify_string_vars(
                        dict.__getitem__(default_config, 'artifacts_dir'),
                        'out_dir')
    # Parse Arguments and assign to args object
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=f"{desc}\n{usage}\n{example}\n\n")

    parser.add_argument(
        "kasfile",
        nargs='*',
        metavar='config.yml',
        help="The path to the yaml files containing the config for \
             the kas build. Can provide multiple space-separated build \
             configs, where each config can be a colon (:) seperated list of \
             .yml files to merge.")

    parser.add_argument(
        "-c",
        "--config",
        help="Load script parameters from file (default: %(default)s).")

    parser.add_argument(
        "-o",
        "--out_dir",
        help=f"Path to build directory (default: {formatted_out_dir})")

    parser.add_argument(
        "-sd",
        "--sstate_dir",
        help=f"Path to local sstate cache for this build \
             (default: {formatted_sstate_dir})")

    parser.add_argument(
        "-dd",
        "--dl_dir",
        help=f"Path to local downloads cache for this build \
             (default: {formatted_dl_dir})")

    parser.add_argument(
        "-sm",
        "--sstate_mirror",
        help="Path to read-only sstate mirror")

    parser.add_argument(
        "-dm",
        "--downloads_mirror",
        help="Path to read-only downloads mirror")

    parser.add_argument(
        "-d",
        "--deploy_artifacts",
        dest="deploy_artifacts",
        action="store_const",
        const=True,
        help=f"Generate artifacts for CI, and store in artifacts dir (default:\
              {default_config['deploy_artifacts']})")

    parser.add_argument(
        "-a",
        "--artifacts_dir",
        help=f"Specify the directory to store the build logs, config and \
             images after the build if --deploy_artifacts is enabled \
             (default: {formatted_artifacts_dir})")

    parser.add_argument(
        "-n",
        "--network_mode",
        help=f"Set the network mode of the container (default: \
             {default_config['network_mode']}).")

    parser.add_argument(
        "-e",
        "--container_engine",
        help=f"Set the container engine (default: \
             {default_config['container_engine']}).")

    parser.add_argument(
        "-i",
        "--container_image",
        help=f"Set the container image (default: \
             {default_config['container_image']}).")

    parser.add_argument(
        "-ea",
        "--engine_arguments",
        help="Optional string of arguments for running the container, e.g.\
              --engine_arguments '--volume /host/dir:/container/dir \
                                  --env VAR=value'.")

    parser.add_argument(
        "-v",
        "--container_image_version",
        help=f"Set the container image version (default: \
             {default_config['container_image_version']}). Note: it is not \
             recommended to use versions 2.5 or lower for kas containers \
             due to lack of support for KAS_BUILD_DIR.")

    parser.add_argument(
        "-j",
        "--number_threads",
        help=f"Sets number of threads used by bitbake, by exporting \
             environment variable BB_NUMBER_THREADS = J. Usually it is set to \
             ({os.cpu_count()}), unless a different number of threads is set \
             in a kas config file used for the build.")

    parser.add_argument(
        "-k",
        "--kas_arguments",
        help=f"Arguments to be passed to kas executable within the container \
             (default: {default_config['kas_arguments']}).")

    parser.add_argument(
        "-log",
        "--log_file",
        help=f"Write output to the given log file as well as to stdout \
             (default: {default_config['log_file']}).")

    parser.add_argument(
        "-l",
        "--list_configs",
        action="store_true",
        dest="list_configs",
        help="List all named configs from the config file specified with a \
             '--config' parameter.")

    parser.add_argument(
        "-r",
        "--project_root",
        help=f"Project root path (default: {default_config['project_root']}).")

    return ArgumentsDictionary(vars(parser.parse_args()))


def merge_configs(base_config, override_config):
    merged_config = ArgumentsDictionary()
    for key in base_config:
        merged_config[key] = base_config[key]
    merged_config.update(override_config)
    return merged_config


# Separate configs that are including multiple kasfiles in a list of configs
# so that we instead get a config for each kasfile.
def duplicate_configs(configs):
    num_configs = len(configs)
    new_config_list = configs
    config_index = 0
    while config_index < num_configs:
        config = configs[config_index]
        if len(config["kasfile"]) > 1:

            # Remove the last kasfile string from this config
            # A kasfile_string is like "one.yml:two.yml:three.yml"
            kasfile_string = config["kasfile"].pop()

            # Copy this config and set it to have only the single kasfile
            # string that was removed
            new_config = ArgumentsDictionary()
            for key in config:
                new_config[key] = config[key]
            new_config["kasfile"] = [kasfile_string]

            # Add the new config to the end of the config list, and continue to
            # check this config again
            new_config_list.append(new_config)
        else:
            config_index += 1

    return new_config_list


# Get the configuration(s) to run this script with, as a combination
# of default parameter values, values from a config file, and values
# given in the command-line, with the below priority:
#
# The default config used is 'default_config'
# If given, values from configs in a config file override the defaults
# If no named config is provided, use just the first config in the file
# Command line arguments override values in all loaded configs
def get_configs():
    default_config = ArgumentsDictionary({
      "config": None,
      "container_engine": "docker",
      "container_image": "ghcr.io/siemens/kas/kas",
      "container_image_version": "2.6.1",
      "engine_arguments": None,
      "number_threads": f"{os.cpu_count()}",
      "deploy_artifacts": False,
      "kas_arguments": "build",
      "kasfile": [],
      "sstate_mirror": None,
      "downloads_mirror": None,
      "log_file": None,
      "network_mode": "bridge",
      "project_root": f"{os.path.realpath(os.getcwd())}",

      # relative to project_root
      "out_dir": "%(project_root)s/build",

      # relative to out_dir
      "sstate_dir": "%(out_dir)s/yocto-cache/sstate",
      "dl_dir":  "%(out_dir)s/yocto-cache/downloads",
      "artifacts_dir":  "%(out_dir)s/artifacts"
    })

    args = get_command_line_args(default_config)
    # The default config used is 'default_config'
    # If given, values from configs in a config file override the defaults
    # If no named config is provided, use just the first config in the file
    # If 'all' is provided, use all configs in the file
    # Command line arguments override values in all loaded configs
    configs = list()

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

                # Check if header version is supported
                if header["version"] < 1:
                    print(f"ERROR: Incompatible version of config file")
                    exit(1)

                # Check that there are configs in this file
                if len(yaml_configs) == 0:
                    print(f"ERROR: No configs defined in config file")
                    exit(1)
                selected_names = list()

                if named_config is not None:
                    selected_names.append(named_config)
                else:
                    selected_names.append(next(iter(yaml_configs.keys())))
                for name in selected_names:
                    config = yaml_configs[name]
                    configs.append(merge_configs(default_config, config))

            except KeyError:
                print(f"ERROR: Invalid configs {args['config']}")
                exit(1)

    else:
        configs.append(default_config)

    # Overwrite values in all prior configs with command-line arguments
    # Ignore any None or empty-list arguments from the command-line parser
    supplied_args = dict(filter(lambda arg: bool(arg[1]) is True or
                                isinstance(arg[1], bool),
                                args.items()))
    configs = [merge_configs(config, supplied_args) for config in configs]

    configs = duplicate_configs(configs)

    # List the available configs if the list_config flag was selected
    if args["list_configs"]:
        if args["config"] is None:
            print("ERROR: No kas-runner configs specified!")
            exit(1)
        else:
            print(f"Build targets: "
                  f"{' '.join(yaml_configs.keys())}")
            exit(0)

    for config in configs:
        if not config.is_valid():
            print("ERROR: Invalid config, string couldn't get evaluated")
            exit(1)

    return configs


# Deploy generated artifacts like build configs and logs.
def deploy_artifacts(build_dir, build_artifacts_dir):

    # Collect config
    build_conf_dir = os.path.join(build_dir, "conf")

    if os.path.exists(build_conf_dir):
        tar_filename = os.path.join(build_artifacts_dir, "conf.tgz")
        with tarfile.open(tar_filename, "w:gz") as conf_tar:
            conf_tar.add(build_conf_dir,
                         arcname=os.path.basename(build_conf_dir))

        print(f"Deployed build configuration artifacts into {tar_filename}")
    else:
        print("No build configuration files to archive")

    # Collect logs
    tar_filename = os.path.join(build_artifacts_dir, "logs.tgz")
    with tarfile.open(tar_filename, "w:gz") as log_tar:

        cooker_log = os.path.join(build_dir, "bitbake-cookerdaemon.log")
        if os.path.exists(cooker_log):
            arcname = os.path.join("logs", os.path.basename(cooker_log))
            log_tar.add(cooker_log, arcname=arcname)

        tmp_dir = os.path.join(build_dir, "tmp")
        if os.path.exists(tmp_dir):

            console_dir = os.path.join(tmp_dir, "log/cooker")
            for path, dirs, files in os.walk(console_dir):
                if "console-latest.log" in files:

                    log_link = os.path.join(path, "console-latest.log")
                    log = os.path.join(path, os.readlink(log_link))

                    arcname = os.path.relpath(log_link, console_dir)
                    arcname = os.path.join("logs", arcname)
                    log_tar.add(log, arcname=arcname)

            work_dir = os.path.join(tmp_dir, "work")
            for path, dirs, files in os.walk(work_dir):

                if "temp" in dirs:
                    log_dir = os.path.join(path, "temp")
                    arcname = os.path.relpath(path, work_dir)
                    arcname = os.path.join("logs", arcname)
                    log_tar.add(log_dir, arcname=arcname)

                if "pseudo.log" in files:
                    pseudo_log = os.path.join(path, "pseudo.log")
                    arcname = os.path.relpath(pseudo_log, work_dir)
                    arcname = os.path.join("logs", arcname)
                    log_tar.add(pseudo_log, arcname=arcname)

            print(f"Deployed build logs into {tar_filename}")

            # Collect images
            base_image_dir = os.path.join(tmp_dir, "deploy/images")
            if os.path.exists(base_image_dir):

                tar_filename = os.path.join(build_artifacts_dir, "images.tgz")
                with tarfile.open(tar_filename, "w:gz") as image_tar:
                    image_tar.add(base_image_dir,
                                  arcname=os.path.basename(base_image_dir))

                print(f"Deployed images into {tar_filename}")
            else:
                print("No image directory found, did not archive images")

        else:
            print("No tmp directory found, did not archive build artifacts")


# Entry Point
def main():
    exit_code = 0
    # Parse command line arguments and split build configs
    # for different targets into a list
    for config in get_configs():

        if config["log_file"]:
            mk_newdir(os.path.dirname(os.path.realpath(config["log_file"])))
            log_file = open(config["log_file"], "w")

            # By default, if we have a log file then only write to it
            # But provide a logger to write to both terminal
            # and the log file for important messages
            sys.tee = TeeLogger(LogOpt.TO_BOTH, log_file)
            sys.stdout = TeeLogger(LogOpt.TO_FILE, log_file)

        else:
            # If we have no log file,
            # write both stdout and tee to only terminal
            sys.tee = TeeLogger(LogOpt.TO_TERM)

        kas_files = config["kasfile"]
        print(f"Starting build task: {kas_files}", file=sys.tee)

        # Check that all config files for the target exist
        missing_confs = "\n".join(
            filter(lambda kfile:
                   not os.path.isfile(os.path.join(config["project_root"],
                                                   kfile)),
                   kas_files[0].split(":")))

        if missing_confs:
            print((f"Error: The kas config files: \n{missing_confs}\nwere not"
                  " found."), file=sys.tee)
            exit_code = 1
            continue

        # buildname is the kas file names without path or extension
        buildname = "_".join([os.path.basename(os.path.splitext(kfile)[0])
                             for kfile in kas_files[0].split(':')])

        # Name of build dir specific to this config
        config["build_dir"] = os.path.join(config["out_dir"], buildname)

        # Create directories if they don't exist
        mk_newdir(config["out_dir"])
        mk_newdir(config["build_dir"])

        engine = ContainerEngine(config["container_engine"],
                                 config["container_image"],
                                 config["container_image_version"])

        # Pass user and group ID to container engine env
        engine.add_env("USER_ID", os.getuid())
        engine.add_env("GROUP_ID", os.getgid())

        # Mount and set up workdir
        work_dir_name = "/work"
        engine.add_volume(config["project_root"], work_dir_name)
        engine.add_arg(f"--workdir={work_dir_name}")
        engine.add_env("KAS_WORK_DIR", work_dir_name)

        # Mount and set up build directory
        build_dir_name = "/kas_build_dir"
        engine.add_volume(config["build_dir"],
                          build_dir_name)
        engine.add_env("KAS_BUILD_DIR", build_dir_name)

        # Configure local caches
        engine.add_volume(config["sstate_dir"],
                          "/sstate_dir",
                          env_var="SSTATE_DIR")
        mk_newdir(config["sstate_dir"])

        engine.add_volume(config["dl_dir"], "/dl_dir", env_var="DL_DIR")
        mk_newdir(config["dl_dir"])

        # Set network mode
        network_mode = config["network_mode"]
        engine.add_arg(f"--network={network_mode}")

        # Configure cache mirrors
        if config["sstate_mirror"]:
            path = "/sstate_mirrors"
            mk_newdir(config["sstate_mirror"])
            engine.add_volume(config["sstate_mirror"], path, "ro")
            engine.add_env(
                "SSTATE_MIRRORS",
                f"file://.* file://{path}/PATH;downloadfilename=PATH")

        if config["downloads_mirror"]:
            path = "/source_mirror_url"
            mk_newdir(config["downloads_mirror"])
            engine.add_volume(config["downloads_mirror"], path, "ro")
            engine.add_env("SOURCE_MIRROR_URL", f"file://{path}")
            engine.add_env('INHERIT', "own-mirrors")
            engine.add_env('BB_GENERATE_MIRROR_TARBALLS', "1")

        # kasfiles must be relative to container filesystem
        kas_config = kasconfig_format(kas_files,
                                      config["project_root"],
                                      work_dir_name)

        if config['engine_arguments']:
            engine.add_arg(config['engine_arguments'])

        if config['number_threads']:
            engine.add_env('BB_NUMBER_THREADS', config['number_threads'])

        # Execute the command
        exit_code |= engine.run(kas_config, config['kas_arguments'])

        # Grab build artifacts and store in artifacts_dir/buildname
        if config["deploy_artifacts"]:
            mk_newdir(config["artifacts_dir"])

            build_artifacts_dir = os.path.join(config["artifacts_dir"],
                                               buildname)
            mk_newdir(build_artifacts_dir)

            deploy_artifacts(config["build_dir"], build_artifacts_dir)

        print(f"Finished build task: {kas_files}\n", file=sys.tee)

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
