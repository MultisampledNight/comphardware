#!/usr/bin/env python3
#
#   Copyright 2021 MultisampledNight
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
Just a helper module which is made for parsing GPU tables on Wikipedia. There
should be no need to execute this manually.
"""
from enum import IntEnum
import re
from typing import Optional

import pandas as pd
import dogelog
from helpers import GPU, save_gpus, human_readable_to_bytes,\
    human_readable_to_hertz


VALUEREGEX = re.compile(r".+\((\w+)\)")


def strip_unimportant(source: str) -> str:
    """
    Strips unimportant information like footnotes, alternative names, or weird
    spaces.
    """
    stripped = ""
    for char in source:
        # remove footnotes like RTX 3080[155]
        if char == "[" or char == "(":
            break
        # remove weird spaces like U+00A0 and make them normal
        if char.isspace():
            char = " "
        
        stripped += char
    stripped = stripped.strip()
    return stripped


def guess_newline(value: str, unit: str) -> float:
    """
    Tries to guess where a newline in the given value with the given unit could
    be, splits there and returns the first value. The unit expected to be
    casefolded.

    This is done because pandas has some trouble reading in table values with a
    newline. pandas interprets this:
        1234
        5678
    not as two values "1234" and "5678", but instead as "12345678"! This causes
    some GPUs having an unrealistic score.
    """
    # first, strip away everything which is not a digit AND in front of the
    # string
    number_begin = 0
    for (i, char) in enumerate(value):
        if char.isdigit():
            number_begin = i
            break
    value = value[number_begin:]
    # second, split up values like "2-4" to only contain the first number
    for i, char in enumerate(value):
        if not char.isdigit():
            value = value[:i]
            break

    if value[-1] == "7":
        # evil footnote delegator, don't ask
        value = value[:-1]

    if unit == "gb" or unit == "gib" or unit == "ghz":
        # pretend that the maximum realistic value is 64, so 2 characters
        if len(value) % 2:
            # example:
            #     32
            #     64
            return float(value[:2])
        else:
            return float(value)
    elif unit == "mb" or unit == "mib" or unit == "mhz":
        # *begins to cry*
        if len(value) == 7:
            return float(value[:3])
        # the realistic character limit here is 4:
        #     1234
        #     5678
        elif len(value) % 4 == 0:
            return float(value[:4])
        # or not, a lot of amd GPUs got their memory listed like this
        #      123
        #      456
        #      7890
        # so... welp, just search for length 10 and take the first 3 ones I guess
        elif len(value) == 10:
            return float(value[:3])
        # or it can be even worse and this
        #     123
        #     4567
        #     8901
        elif len(value) == 11:
            return float(value[:3])
        # here it is 3, many amd cards are displayed as normal clock first, and
        # boost clock second
        #     123
        #     456
        # we only care about the core clock
        # sometimes also there are *three* values, so I'll just use modulo here
        # see GeForce GT 650M
        #     123
        #     456
        #     789
        elif len(value) % 3 == 0:
            return float(value[:3])
    return float(value)


def parse_gpu(row, indices: dict, vendor: str) -> Optional[GPU]:
    """Parses a GPU out of the given row and the given indices."""
    # model (always the first column, but a bit messy)
    model = strip_unimportant(row[0]).casefold()

    # VRAM (assumed to be GiB)
    if indices["vram"] is not None:
        raw = row[indices["vram"][0]]

        raw = strip_unimportant(str(raw))
        raw = guess_newline(raw, indices["vram"][1])

        vram = human_readable_to_bytes(raw, indices["vram"][1])
    else:
        # we're after Gen 8 from intel, let's hardcode 3000 MiB
        vram = human_readable_to_bytes(3000, "mib")

    # core speed (assumed to be MHz)
    # reminder: indices["corespeed"] is a tuple consisting out of
    # (index, unit)
    raw = row[indices["corespeed"][0]]

    raw = strip_unimportant(str(raw))
    raw = guess_newline(raw, indices["corespeed"][1])

    corespeed = human_readable_to_hertz(raw, indices["corespeed"][1])

    # codename (quite simple as it's a string)
    codename = strip_unimportant(row[indices["codename"]])

    # api (a complicated string that needs parsing for enums)
    # apilevels = parse_apilevel(row[indices["apilevel"]])

    gpu = GPU(
        model,
        vendor,
        vram,
        corespeed,
        codename,
    )
    return gpu


def extract_gpus(tables: list[pd.DataFrame], ignore_models: list[str], vendor: str) -> list[GPU]:
    """
    Extracts the GPUs out of the given pandas DataFrames.
    Ignores the given model names.
    """
    gpus = []
    progress = dogelog.Progress(f"Parsing {vendor} tables...", len(tables))

    for table in tables:
        progress.stack()

        skip_table = False
        # find the indices in the table so we can look them up afterwards in the
        # numpy array in table.values
        indices = {
                "vram": None,
                "corespeed": None,
                "codename": None
                #"apilevel": None
            }
        for (i, column_ident) in enumerate(table.axes[1]):
            if isinstance(column_ident, tuple):
                # only the last element in the tuple matters
                column_ident = column_ident[-1]
            if isinstance(column_ident, int):
                # ??? didn't find the actual table for this one, just ignore it
                # I guess
                dogelog.debug(f"That table's weird:\n{table}")
                skip_table = True
                break
            # after this point, we just assume colum_ident is a string

            # case sensitivity doesn't make much sense here
            column_ident = column_ident.casefold()
            
            if (
                    "size" in column_ident or
                    "dvmt" in column_ident  # yes, technically it's not VRAM
                ) and (
                    "mb" in column_ident or
                    "mib" in column_ident or
                    "gb" in column_ident or
                    "gib" in column_ident
                ):
                # vram and corespeed should be a tuple, consisting out of
                # (index, unit)
                match = VALUEREGEX.search(column_ident)
                if "mb" in column_ident and match.group(1) != "mb":
                    dogelog.info(f"String: {column_ident}\nGroups: {match.groups()}")
                indices["vram"] = (i, match.group(1))
            elif (
                    "core" in column_ident or
                    "average" in column_ident or
                    "base" in column_ident or
                    "max" in column_ident# or
                    #"clock" in column_ident
                ) and "boost" not in column_ident and (
                    "mhz" in column_ident or
                    "ghz" in column_ident
                ):
                match = VALUEREGEX.search(column_ident)
                indices["corespeed"] = (i, match.group(1))
            elif "code" in column_ident:
                indices["codename"] = i
            #elif "api" in column_ident:
            #    indices["apilevel"] = i

        # check that we got every column we need, else it's not an important
        # table
        for (name, index) in indices.items():
            if index is None:
                if vendor == "intel" and name == "vram":
                    # on intel gen 8 and later the half of the system memory is
                    # available for graphics use, but since that's kind of hard
                    # to track down, I'll just use fixed 3000 MiB later
                    continue
                dogelog.debug(f"Skipping table:\n{table}\ndue to unfound {name}")
                skip_table = True
        
        if skip_table:
            continue

        # second, walk through the actual table
        for row in table.to_numpy():
            try:
                gpu = parse_gpu(row, indices, vendor)
                if gpu is not None:
                    # parse_gpu returns None if it is unable to parse the GPU
                    gpus.append(gpu)
            except (ValueError, IndexError):
                # we're on the description in the lower part of the table,
                # nothing of interest is here anymore
                break

    progress.finish()
    return gpus


def parse(url: str, old_gpus: list[str], vendor: str) -> list[GPU]:
    """
    Parses all tables at the given URL and notes the given vendor down for the
    GPUs.
    """
    tables = pd.read_html(url)
    gpus = extract_gpus(tables, old_gpus, vendor)
    return gpus


# vim:textwidth=80:
