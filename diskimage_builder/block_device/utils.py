# Copyright 2016 Andreas Florath (andreas@florath.net)
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import re
import subprocess

logger = logging.getLogger(__name__)


SIZE_UNIT_SPECS = [
    ["TiB", 1024**4],
    ["GiB", 1024**3],
    ["MiB", 1024**2],
    ["KiB", 1024**1],
    ["TB", 1000**4],
    ["GB", 1000**3],
    ["MB", 1000**2],
    ["KB", 1000**1],
    ["T", 1000**4],
    ["G", 1000**3],
    ["M", 1000**2],
    ["K", 1000**1],
    ["B", 1],
    ["", 1],   # No unit -> size is given in bytes
]

# Basic RE to check and split floats (without exponent)
# and a given unit specification (which must be non-numerical).
size_unit_spec_re = re.compile("^([\d\.]*) ?([a-zA-Z0-9_]*)$")


def _split_size_unit_spec(size_unit_spec):
    """Helper function to split unit specification into parts.

    The first part is the numeric part - the second one is the unit.
    """
    match = size_unit_spec_re.match(size_unit_spec)
    if match is None:
        raise RuntimeError("Invalid size unit spec [%s]" % size_unit_spec)

    return match.group(1), match.group(2)


def _get_unit_factor(unit_str):
    """Helper function to get the unit factor.

    The given unit_str needs to be a string of the
    SIZE_UNIT_SPECS table.
    If the unit is not found, a runtime error is raised.
    """
    for spec_key, spec_value in SIZE_UNIT_SPECS:
        if unit_str == spec_key:
            return spec_value
    raise RuntimeError("unit_str [%s] not known" % unit_str)


def parse_abs_size_spec(size_spec):
    size_cnt_str, size_unit_str = _split_size_unit_spec(size_spec)
    unit_factor = _get_unit_factor(size_unit_str)
    return int(unit_factor * (
        float(size_cnt_str) if len(size_cnt_str) > 0 else 1))


def parse_rel_size_spec(size_spec, abs_size):
    """Parses size specifications - can be relative like 50%

    In addition to the absolute parsing also a relative
    parsing is done.  If the size specification ends in '%',
    then the relative size of the given 'abs_size' is returned.
    """
    if size_spec[-1] == '%':
        percent = float(size_spec[:-1])
        return True, int(abs_size * percent / 100.0)

    return False, parse_abs_size_spec(size_spec)


def exec_sudo(cmd):
    """Run a command under sudo

    Run command under sudo, with debug trace of output.  This is like
    subprocess.check_call() but sudo wrapped and with output tracing
    at debug levels.

    Arguments:
    :param cmd: str command list; for Popen()
    :return: nothing
    :raises: subprocess.CalledProcessError if return code != 0

    """
    assert isinstance(cmd, list)
    sudo_cmd = ["sudo"]
    sudo_cmd.extend(cmd)
    try:
        logger.info("Calling [%s]" % " ".join(sudo_cmd))
    except TypeError:
        # Popen actually doesn't care, but we've managed to get mixed
        # str and bytes in argument lists which causes errors logging
        # commands.  Give a clue as to what's going on.
        logger.exception("Ensure all arguments are str type!")
        raise

    proc = subprocess.Popen(sudo_cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)

    for line in iter(proc.stdout.readline, b""):
        logger.debug("exec_sudo: %s" % line.rstrip())

    proc.wait()
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode,
                                            ' '.join(sudo_cmd))


def sort_mount_points(mount_points):
    logger.debug("sort_mount_points called [%s]" % mount_points)

    def insert_sorted(mp, sorted_mount_points):
        if len(sorted_mount_points) == 0:
            sorted_mount_points.append(mp)
            return
        for idx in range(0, len(sorted_mount_points)):
            if sorted_mount_points[idx].startswith(mp):
                sorted_mount_points.insert(idx, mp)
                return
        sorted_mount_points.append(mp)

    sorted_mount_points = []
    for mp in mount_points:
        insert_sorted(mp, sorted_mount_points)
    logger.debug("sort_mount_points result [%s]" % sorted_mount_points)
    return sorted_mount_points
