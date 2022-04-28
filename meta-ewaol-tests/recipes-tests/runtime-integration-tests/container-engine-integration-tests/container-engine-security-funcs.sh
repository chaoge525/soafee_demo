#!/usr/bin/env bash
#
# Copyright (c) 2022, Arm Limited.
#
# SPDX-License-Identifier: MIT

# Should only be called by virtualization-specific version of the environment
# clean-up
extra_cleanup() {
    guest_vm_reset_password
}
