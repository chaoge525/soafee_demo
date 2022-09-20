#!/usr/bin/python3
# Copyright (c) 2021-2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

"""
This QA-check module aims to validate the inclusion of copyright and license
headers within the relevant files of the project, according to an expected
format.

The check runs recursively and independently on the file and directory paths
given by the 'paths' variable, and ensures all non-excluded files have an
appropriate copyright and license header. Exclusions are specified in the regex
strings given within 'exclude_patterns', where any file that matches an exclude
pattern will not be checked (or recursed into).

License headers are validated to be one of the following two formats:

1. Original licensed works:

    Copyright (c) YYYY(-YYYY), <Contributor>
    SPDX-License-Identifier: <LicenseID>

2. Included externally-licensed (and optionally modified within the project)
   works:

    Based on: <Original file>
    In open-source project: <Source project/repository>

    Original file: Copyright (c) YYYY(-YYYY) <Contributor>
    Modifications: Copyright (c) YYYY(-YYYY) <Contributor>

    SPDX-License-Identifier: <LicenseID>

For each file with such a header, the final copyright year of the modifications
must match or be later than the latest year that the file was modified in the
git commit tree. If the file is not yet tracked in the git repository or has
local changes pending, then the final copyright year must instead be equal to
or later than the year of the last modification date of the file on the
filesystem.

The SPDX-License-Identifiers can be validated via the two checker variables:
'original_works_licenses' and 'external_works_licenses'. If license identifier
validation is enabled, the LicenseID value in the above examples much match a
license ID within the appropriate list for the check to pass. If the value
'SPDX' is given in the list, then a valid license list will be read from the
JSON file provided in the 'spdx_licenses_path' option. If a path is not
provided, the JSON file at https://spdx.org/licenses.json will be downloaded
and used, requiring network access (note that this file does not currently
include SPDX license identifier expressions or exceptions, where matching
LicenseIDs should be provided explicitly in the appropriate list if necessary.
See --help for additional guidance on configuring these variables, or disabling
license identifier validation.

On failure, the check will log any files that failed validation along with the
reason for the error.
"""

import datetime
import os
import re
import subprocess
import time

import common
import abstract_check


class HeaderCheck(abstract_check.AbstractCheck):
    """ Class to check the headers in the provided directories or files within
        the 'paths_to_check' list, excluding paths (and subpaths) of those
        found in 'exclude_paths'. """

    name = "header"

    @staticmethod
    def get_vars():
        return [
            abstract_check.CheckSetting(
                "paths",
                is_list=True,
                default=["ROOT"],
                message=("File paths to check, or directories to recurse."
                         " Relative file paths will be considered relative to"
                         " 'project_root'.")
            ),
            abstract_check.CheckSetting(
                "exclude_patterns",
                is_list=True,
                is_pattern=True,
                default=["GITIGNORE_CONTENTS", "*.git", "*.gitignore"],
                message=("Patterns where if any is matched with the"
                         " file/directory name, the check will not be applied"
                         " to it or continue into its subpaths.")
            ),
            abstract_check.CheckSetting(
                "original_works_licenses",
                is_list=True,
                default=["SPDX"],
                message=("Valid SPDX license identifiers for original works"
                         " contributed to the project. If the word 'SPDX' is"
                         " provided, then the full set of SPDX licenses (see"
                         " the 'spdx_licenses_path' option) will be included."
                         " If the list consists of a single empty string, no"
                         " validation will be done.")
            ),
            abstract_check.CheckSetting(
                "external_works_licenses",
                is_list=True,
                default=["SPDX"],
                message=("Valid SPDX license identifiers for external works"
                         " and any modifications of external works contributed"
                         " to the project. If the word 'SPDX' is provided,"
                         " then the full set of SPDX licenses (see the"
                         " 'spdx_licenses_path' option) will be included. If"
                         " the list consists of a single empty string, no"
                         " validation will be done.")
            ),
            abstract_check.CheckSetting(
                "spdx_licenses_path",
                default=None,
                message=("File path to JSON file containing the full set of"
                         " standard SPDX licenses, used only if 'SPDX' has"
                         " been given in the set of acceptable licenses (see"
                         " the 'original_works_licenses' and"
                         " 'external_works_licenses' options). If no file path"
                         " is provided then the JSON file will be downloaded"
                         " from 'https://spdx.org/licenses/licenses.json'"
                         " (requiring network access). A relative file path"
                         " will be considered relative to 'project_root'.")
            ),
        ]

    def __init__(self, logger, *args, **kwargs):
        self.logger = logger
        self.__dict__.update(kwargs)

        # The header block is the first contiguous set of commented lines from
        # the first line that contains a license and copyright header keyword
        # (see below) to the final commented line that contains one.

        # Validation will be performed on this extracted block only, meaning
        # all lines after the first contiguous set of commented lines that meet
        # the above criteria will not be considered.

        header_words = ("Copyright|Original file|Modifications|Based on|"
                        "In open-source project|SPDX")

        self.comment_delim = ["#", "//", "*", ";"]
        self.comment_start = r"^\s*(#|[/][/]|;|[*])+"
        start = (fr"{self.comment_start}.*({header_words})")
        end = (fr"{self.comment_start}.*({header_words})")

        # Delete all lines not after {start}
        # Add remaining lines to H
        # Delete lines that don't match {end}
        # When match {end}, empty pattern space, and exchange with H
        self.header_block_regex = fr"/{start}/,$!d;H;/{end}/!d;s/.*//;x;s/\n//"

        self.num_files_checked = 0

        self.spdx_license_list = list()

    def get_pip_dependencies(self):
        """ There are no non-standard Python package dependencies required to
            run the executable """
        return []

    def validate_system_dependencies(self):
        """ This check requires git version 2.25 or greater. """

        try:
            from distutils.version import StrictVersion

            cmd = "git --version"
            proc = subprocess.run(cmd.split(),
                                  capture_output=True,
                                  check=True)

            version_str = proc.stdout.decode().strip()

            cur_version = version_str.split(" ")[-1]
            req_version = "2.25"

            if StrictVersion(cur_version) < StrictVersion(req_version):
                self.logger.error(f"Detected git version ${cur_version} but"
                                  f" this check requires git {req_version}.")
                return False

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to run {cmd} when validating"
                              " dependencies.")
            return False

        return True

    def load_spdx_license_list(self):

        import urllib.request
        import json

        target = None
        try:
            if self.spdx_licenses_path:

                # Relative path considered relative to project_root
                if not os.path.isabs(self.spdx_licenses_path):
                    absolute_path = os.path.join(self.project_root,
                                                 self.spdx_licenses_path)
                    self.spdx_licenses_path = absolute_path

                target = open(self.spdx_licenses_path, 'r')
            else:
                licenses_url = "https://spdx.org/licenses/licenses.json"
                target = urllib.request.urlopen(licenses_url)

            identifiers_json = json.load(target)
            if identifiers_json:
                self.spdx_license_list = [license["licenseId"] for license
                                          in identifiers_json["licenses"]]
            else:
                raise json.JSONDecodeError()

        except Exception:
            if self.spdx_licenses_path:
                self.logger.error("Could not extract list of valid identifiers"
                                  " from the filepath:"
                                  f" {self.spdx_licenses_path}.")
            else:
                self.logger.error("Could not extract list of valid identifiers"
                                  f" from the url: {licenses_url}.")

        finally:
            if target:
                target.close()

    def get_latest_modification_time(self, path):
        """ If the file is not tracked by git or it is tracked but has local
            changes, then consider the latest modification date to be the
            file's mtime on the filesystem. Otherwise, consider the latest
            modification date to be the author date (GIT_AUTHOR_DATE) of the
            latest git commit that modified it. """

        dirname = os.path.dirname(path)

        try:
            file_is_tracked_cmd = (f"git -C {dirname} ls-files --error-unmatch"
                                   f" {path}")
            proc = subprocess.run(file_is_tracked_cmd.split(),
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL,
                                  check=True)

            local_changes_cmd = (f"git -C {dirname} diff --exit-code --cached"
                                 f" -s {path}")
            subprocess.run(local_changes_cmd.split(),
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           check=True)

            local_changes_cached_cmd = (f"git -C {dirname} diff --exit-code -s"
                                        f" {path}")
            subprocess.run(local_changes_cached_cmd.split(),
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           check=True)

            git_commit_time_cmd = (f"git -C {dirname} log -1 --pretty=%as"
                                   f" {path}")
            proc = subprocess.run(git_commit_time_cmd.split(" "),
                                  check=True,
                                  capture_output=True)

            date_str = proc.stdout.decode().strip()

            return time.strptime(date_str, "%Y-%m-%d")

        except subprocess.CalledProcessError as e:

            return time.gmtime(os.path.getmtime(path))

    def validate_copyright_years(self, years_str, last_modification_year=None):
        """ Validate that copyright is correctly stated as YYYY or YYYY-YYYY
            where each YYYY is a valid numerical year, and the second year is
            greater than the first and matches the last modification year, if
            given. """

        years_list = years_str.split('-')
        error = None
        try:
            years = []
            for year in years_list:
                years.append(datetime.datetime.strptime(year, '%Y').year)

            cur_year = datetime.datetime.now().year
            if any([year > cur_year for year in years]):
                error = ("Copyright year cannot be specified for future years"
                         f" (must be <= {cur_year}).")

            if not error and len(years) > 2:
                error = "Copyright years must be stated as a single range"

            if not error and len(years) == 2:
                if years[0] >= years[1]:
                    error = ("Copyright year range must be stated in ascending"
                             " order")

            if not error and last_modification_year is not None:
                if years[-1] != last_modification_year.tm_year:
                    error = ("Final copyright year does not match file's last"
                             " modification")

        except ValueError:
            error = "Invalid copyright year format"

        return error

    def validate_license_identifier(self, identifier_str, license_list):

        valid_licenses = license_list.copy()

        if len(valid_licenses) == 1 and valid_licenses[0].strip() == "":
            # No validation
            return True

        if "SPDX" in valid_licenses:
            valid_licenses.remove("SPDX")
            valid_licenses.extend(self.spdx_license_list)

        if identifier_str in valid_licenses:
            return True
        else:
            return False

    def validate_internal(self,
                          path,
                          rel_path,
                          file_errors,
                          header_lines,
                          copyright_regex):

        header = "\n".join(header_lines)

        copyright_lines = [copyright for copyright in header_lines
                           if "copyright" in copyright.lower()]

        # Each copyright line must match the correct format

        prev_year = None
        for line_idx, line in enumerate(copyright_lines):

            match = re.findall(fr"{copyright_regex},? (\w+)", line)
            if not match:
                file_errors[rel_path] = ("Invalid copyright format found"
                                         f" on line: {line}")
                return

            # Validate copyright dates
            years_str = match[0][0]
            last_change = None
            if line_idx == len(copyright_lines)-1:
                last_change = self.get_latest_modification_time(path)

            error = self.validate_copyright_years(years_str,
                                                  last_change)
            if error:
                file_errors[rel_path] = (f"{error} on line: {line}")
                return

            # years_str must be castable as integer if pass validation
            year = int(years_str.split("-")[-1])
            if prev_year and year < prev_year:
                file_errors[rel_path] = ("Copyrights must be given in"
                                         " chronologically ascending order"
                                         " (final stated copyright must be"
                                         " the most recent).")
                return

            prev_year = year

            if ("ARM" in line or
                    ("Arm" in line and "Arm Limited" not in line)):
                file_errors[rel_path] = ("Arm should be stated as 'Arm"
                                         " Limited' in a license and"
                                         " copyright header. Line:"
                                         f" {line}")
                return

        # Check that the license identifier is present, and is valid
        spdx_match = re.findall(f"{self.comment_start}"
                                r"\s+SPDX-License-Identifier:\s+(.+)$",
                                header,
                                re.MULTILINE)
        if spdx_match:

            valid = self.validate_license_identifier(
                spdx_match[0][1],
                self.original_works_licenses)

            if not valid:

                error_msg = (f"'{spdx_match[0][1]}' is considered an invalid"
                             " license for original works within the project"
                             " which should be within:"
                             f" {self.original_works_licenses}.")
                if "SPDX" in self.original_works_licenses:
                    error_msg += (" (Note that 'SPDX' expands to the list"
                                  " given at https://spdx.org/licenses).")

                file_errors[rel_path] = error_msg
                return
        else:
            file_errors[rel_path] = ("Could not find a correctly formatted"
                                     " SPDX License Identifier.")
            return

        if len(spdx_match) > 1:
            file_errors[rel_path] = ("Can only define one SPDX License"
                                     " Identifier line (found"
                                     f" {len(spdx_match)}).")
            return

        # Validate the order is correct
        order = re.compile(
                    (f"{self.comment_start}.*{copyright_regex}"
                     fr".*{self.comment_start}.*SPDX"),
                    re.DOTALL | re.MULTILINE).search(header)

        if not order:
            file_errors[rel_path] = ("The license and copyright"
                                     " information must be stated in the"
                                     " correct order.")
            return

    def validate_external(self,
                          path,
                          rel_path,
                          file_errors,
                          header_lines,
                          copyright_regex):

        header = "\n".join(header_lines)

        based_on_lines = [line for line in header_lines
                          if re.match((f"{self.comment_start} Based on:"
                                       r" (\w+)"), line)]

        if not based_on_lines:
            file_errors[rel_path] = ("Included externally-sourced works"
                                     " must have a 'Based on' line that"
                                     " specifies the original file.")
            return

        in_proj_lines = [line for line in header_lines
                         if re.match((f"{self.comment_start} In"
                                      " open-source project:"
                                      r" (\w+)"), line)]

        if not in_proj_lines:
            file_errors[rel_path] = ("Included externally-sourced works"
                                     " must have an 'In open-source"
                                     " project' line that specifies the"
                                     " project where the original file can"
                                     " be found.")
            return

        if len(based_on_lines) > 1 or len(in_proj_lines) > 1:
            file_errors[rel_path] = ("Currently, any included externally-"
                                     "sourced works can only be based on a"
                                     " single original file from a single"
                                     " open-source project.")
            return

        original_copyright = [line for line in header_lines
                              if re.match((f"{self.comment_start} Original"
                                           f" file: {copyright_regex},?"
                                           r" (\w+)"), line)]

        if not original_copyright:
            file_errors[rel_path] = ("Included externally-sourced works"
                                     " must specify the original file's"
                                     " copyright information")
            return

        prev_year = None
        for copyright_line in original_copyright:
            match = re.findall(fr"{copyright_regex},? (\w+)",
                               copyright_line)

            if not match:
                file_errors[rel_path] = ("Original file's copyright format"
                                         " is incorrect. The line is:"
                                         f" {copyright_line}")
                return

            years_str = match[0][0]
            error = self.validate_copyright_years(years_str)
            if error:
                file_errors[rel_path] = (f"{error} on line: "
                                         f"{copyright_line}")
                return

            # years_str must be castable as integer if pass validation
            year = int(years_str.split("-")[-1])
            if prev_year and year < prev_year:
                file_errors[rel_path] = ("Copyrights must be given in"
                                         " chronologically ascending order"
                                         " (final stated copyright must be"
                                         " the most recent).")
                return

            prev_year = year

            if ("ARM" in copyright_line or
                ("Arm" in copyright_line and
                 "Arm Limited" not in copyright_line)):

                file_errors[rel_path] = ("Arm should be stated as 'Arm"
                                         " Limited' in a license and"
                                         " copyright header. Line:"
                                         f" {copyright_line}")
                return

        mods_copyright = [line for line in header_lines
                          if re.match((f"{self.comment_start}"
                                       f" Modifications: {copyright_regex}"
                                       r",? (\w+)"), line)]

        if not mods_copyright:
            file_errors[rel_path] = ("Included externally-sourced works"
                                     " must specify the copyright of any"
                                     " in-project modifications.")
            return

        prev_year = None
        for line_idx, copyright_line in enumerate(mods_copyright):
            match = re.findall(fr"{copyright_regex},? (\w+)",
                               copyright_line)

            if not match:
                file_errors[rel_path] = ("Modifications copyright format"
                                         " is incorrect. The line is:"
                                         f" {copyright_line}")
                return

            years_str = match[0][0]
            last_change = None
            if line_idx == len(mods_copyright)-1:
                last_change = self.get_latest_modification_time(path)

            error = self.validate_copyright_years(years_str,
                                                  last_change)
            if error:
                file_errors[rel_path] = (f"{error} on line: "
                                         f"{copyright_line}")
                return

            # years_str must be castable as integer if pass validation
            year = int(years_str.split("-")[-1])
            if prev_year and year < prev_year:
                file_errors[rel_path] = ("Copyrights must be given in"
                                         " chronologically ascending order"
                                         " (final stated copyright must be"
                                         " the most recent).")
                return

            prev_year = year

            if ("ARM" in copyright_line or
                ("Arm" in copyright_line and
                 "Arm Limited" not in copyright_line)):

                file_errors[rel_path] = ("Arm should be stated as 'Arm"
                                         " Limited' in a license and"
                                         " copyright header. Line:"
                                         f" {copyright_line}")
                return

        # Check that the license identifier is present
        spdx_match = re.findall(f"{self.comment_start}"
                                r"\s+SPDX-License-Identifier:\s+(.+)$",
                                header,
                                re.MULTILINE)
        if not spdx_match:
            file_errors[rel_path] = ("Could not find a correctly formatted"
                                     " SPDX License Identifier.")
            return

        if len(spdx_match) > 1:
            file_errors[rel_path] = ("Can only define one SPDX License"
                                     " Identifier line (found"
                                     f" {len(spdx_match)}).")
            return

        valid = self.validate_license_identifier(
            spdx_match[0][1],
            self.external_works_licenses)

        if not valid:
            error_msg = (f"'{spdx_match[0][1]}' is considered an invalid"
                         " license for externally-sourced works within the"
                         " project, which should be one of:"
                         f" {self.external_works_licenses}.")
            if "SPDX" in self.external_works_licenses:
                error_msg += (" (Note that 'SPDX' expands to the list"
                              " given at https://spdx.org/licenses).")

            file_errors[rel_path] = error_msg
            return

        # Validate the order is correct
        order = re.compile(
                    (f"{self.comment_start} Based on:"
                     fr".*{self.comment_start} In open-source project:"
                     fr".*{self.comment_start}.*{copyright_regex}"
                     fr".*{self.comment_start}.*{copyright_regex}"
                     fr".*{self.comment_start}.*SPDX"),
                    re.DOTALL | re.MULTILINE).search(header)

        if not order:
            file_errors[rel_path] = ("The license and copyright"
                                     " information must be stated in the"
                                     " correct order.")
            return

    def check_header(self, path, file_errors):
        """ This function checks the header in a file. it returns any errors
            as a dict mapping the filepath to the error """

        rel_path = os.path.relpath(path, self.project_root)

        # Find the header block
        cmd = f"sed -r '{self.header_block_regex}' {path}"

        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   shell=True,
                                   universal_newlines=True)

        try:
            header = process.stdout.read()
        except UnicodeDecodeError as e:
            file_errors[rel_path] = ("Couldn't process file due to"
                                     " UnicodeDecodeError")
            return

        # Check that the header block is valid (contiguous comment block)

        header_lines = []
        for line in header.split("\n"):
            line = line.strip()
            if any([line.startswith(delim) for delim in self.comment_delim]):
                header_lines.append(line)
            elif line == "":
                pass
            else:
                break

        header = "\n".join(header_lines)

        # Validate that the header block contains the mandatory content in the
        # correct format. To do this, determine if its an internal work
        # or an externally-sourced work

        # A commented line beginning with one of the 'external words' defines
        # an externally-licensed work
        # A commented line simply beginning with a copyright defines an
        # internal work

        copyright_regex = "Copyright [(]c[)] ([0-9]{4}(-[0-9]{4})?)"

        match_internal = re.compile(fr"{self.comment_start}\s*"
                                    f"{copyright_regex}",
                                    re.MULTILINE).search(header)

        external_words = ("(Original file|Modifications|Based on|"
                          "In open-source project)")
        match_external = re.compile((fr"{self.comment_start}\s*"
                                     fr"{external_words}.*{copyright_regex}"),
                                    re.MULTILINE).search(header)

        if not match_internal and not match_external:
            file_errors[rel_path] = ("Could not find copyright and license"
                                     " header")
            return
        elif match_internal and match_external:
            # Validation error:
            file_errors[rel_path] = ("Copyright and license header mixes"
                                     " internal and externally-sourced header"
                                     " formats")
            return
        elif match_internal:

            self.validate_internal(path,
                                   rel_path,
                                   file_errors,
                                   header_lines,
                                   copyright_regex)

        elif match_external:

            self.validate_external(path,
                                   rel_path,
                                   file_errors,
                                   header_lines,
                                   copyright_regex)

        self.num_files_checked += 1

    def run(self):

        self.logger.debug(f"Running {self.name} check.")

        if not self.validate_system_dependencies():
            self.logger.error("FAIL")
            return 1

        if ("SPDX" in self.original_works_licenses or
                "SPDX" in self.external_works_licenses):
            self.load_spdx_license_list()

        file_errors = dict()
        for path in self.paths:

            if not os.path.isabs(path):
                path = os.path.join(self.project_root, path)

            if not os.path.exists(path):
                file_errors[path] = "File or directory not found."
                continue

            self.logger.debug(f"Running {self.name} check on {path}")
            common.recursively_apply_check(
                path,
                self.check_header,
                file_errors,
                self.exclude_patterns)

        if file_errors:
            self.logger.error("FAIL")
            for filename, error in file_errors.items():
                self.logger.error(f"{filename}:{error}")

            correct_in = ("\tCopyright (c) YYYY(-YYYY), <Contributor>\n"
                          "\tSPDX-License-Identifier: <License name>")

            correct_out = ("\tBased on: <Original filename>\n"
                           "\tIn open-source project: <Project source>\n"
                           "\tOriginal file: Copyright (c) YYYY(-YYYY),"
                           " <Contributor>\n"
                           "\tModifications: Copyright (c) YYYY(-YYYY),"
                           " <Contributor>\n"
                           "\tSPDX-License-Identifier: <License(s)>")

            self.logger.error(("Validation ensures the copyright and license"
                               f" header is of the format:\n{correct_in}\nfor"
                               " original project works, or of the format:\n"
                               f"{correct_out}\nfor included/modified"
                               " externally-sourced works."))

            return 1
        else:
            self.logger.info(f"PASS ({self.num_files_checked} files checked)")
            return 0
