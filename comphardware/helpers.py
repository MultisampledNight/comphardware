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
Some helper functions for easier parsing of values.
"""
import difflib

from .data import ALL_GPUS, ALL_CPUS, MODEL_TO_GPU, MODEL_TO_CPU
from ._models import GPU, CPU, SystemSetup


def _resource_contents(resource: str, subfolder: str = "resources") -> dict:
    """
    Returns the JSON contents of the given resource.

    A resource is a JSON file stored in the "resources" folder. It will be
    packaged and delivered to the enduser alongside with the actual package.
    """
    subpath = join(subfolder, resource)
    content = pkg_resources.resource_string(__name__, subpath)
    return json.loads(content)


def human_readable_to_bytes(value: int, unit: str) -> int:
    """
    Converts the given value and unit to bytes.

    As an example, it should convert (8, GB) to 8388608.
    Even though technically MB means 1000 * 1000, many producers actually mean
    MiB, which is 1024 * 1024. Even Windows displays as unit MB, even though
    it's actually MiB.
    """
    unit = unit.casefold()

    if unit == "b":
        return value
    elif unit == "kb" or unit == "kib":
        return value * 1024
    elif unit == "mb" or unit == "mib":
        return value * (1024 ** 2)
    elif unit == "gb" or unit == "gib":
        return value * (1024 ** 3)
    elif unit == "tb" or unit == "tib":
        return value * (1024 ** 4)
    else:
        # there's more, but that's extremely unlikely
        return value


def human_readable_to_hertz(value: int, unit: str) -> int:
    """
    Converts the given hertz and unit (GHz or MHz or whatever) to Hz.
    """
    unit = unit.casefold()

    if unit == "khz":
        return value * (10 ** 3)
    elif unit == "mhz":
        return value * (10 ** 6)
    elif unit == "ghz":
        return value * (10 ** 9)
    elif unit == "thz":
        return value * (10 ** 12)
    else:
        # see human_readable_to_bytes
        return value


def _find_by_model(cls, database: dict, unexact_model: str):
    """
    Finds the vaguely given model in the model-to-component database and returns
    it.
    """
    # don't worry about the function signature, I just didn't find any suitable
    # way to say typing that a class comes in here and an object depending on
    # the database comes out

    # use difflib to find the closest match
    # we use a SequenceMatcher here as we can just feed in all models in the
    # database and take the longest match
    sequence_matcher = difflib.SequenceMatcher(b=unexact_model)

    # we use current_score to hold state which model was the best one until yet,
    # and exact_model for the full model name in the DB then
    current_score = 0
    exact_model = None

    for model in database.keys():
        # find match and compare it to the existing one

        # say the SequenceMatcher which sequence we want to match on
        sequence_matcher.set_seq1(model)

        # yep, a bit confusing, but basically
        # the first two arguments mean start:end of seq1 to search
        # the second two arguments mean start:end of seq2 to search
        match = sequence_matcher.find_longest_match(0, len(model), 0,
                len(unexact_model))

        # is it even better than any matches before?
        if match[2] > current_score:
            # if you look up in the docs of difflib.SequenceMatcher, you'll see
            # that k practically says the substring length
            current_score = match[2]
            exact_model = model

    if exact_model is None:
        # didn't find any matches :(
        return None

    # exact_model contains the full model, and only gets updated in sync with
    # longest_match
    component = database[exact_model]

    return component


def find_cpu_by_model(model: str) -> CPU:
    """
    Finds the CPU with the given model and returns it, or None if it couldn't be
    found.

    The model doesn't have to match exactly the searched model, it must only
    contain the model. This is because I have no idea how I should implement
    proper parsing of the actual model out of a string.

    In case of multiple matches, the first one in the database is returned.
    """
    return _find_by_model(CPU, MODEL_TO_CPU, model)


def find_gpu_by_model(model: str) -> GPU:
    """
    Finds the GPU which has the given model (name), and returns it. Returns None
    if it hasn't been found.

    The model doesn't have to match exactly the searched model, it must only
    contain the model. This is because I have no idea how I should implement
    proper parsing of the actual model out of a string.

    If in the database are multiple matches, the first one is returned.
    """
    return _find_by_model(GPU, MODEL_TO_GPU, model)

def setup_from_clutter(cpu_clutter: str, gpu_clutter: str, ram_clutter: str) -> SystemSetup:
    """
    Tries to get a SystemSetup using the given strings for the CPU, GPU and RAM.

    With "clutter" I mean strings that contain somewhere in them the actual
    model specifications, but have additional non-interesting information in
    them. For example, these are the requirements of Satisfactory, out of the
    Epic store:

    Processor  i5-3570k 3.4 GHz 4 Core (64-Bit)
    Memory     8 GB RAM
    Graphics   GTX 760 2GB

    You don't have to care about getting the important information out of
    the string, you should be able to feed in for the CPU "i5-3570k 3.4 GHz 4
    Core (64-Bit)", for the GPU "GTX 760 2GB" and for the RAM "8 GB RAM", and
    this function will figure it out. Somehow.
    """
    # we already have functions for getting the GPU and CPU out of cluttered (or
    # how these call them, "vague") strings
    cpu = find_cpu_by_model(cpu_clutter)
    gpu = find_gpu_by_model(gpu_clutter)

    # for the RAM we need some parsing though
    # the idea is to find the first number in the string, the word after it is
    # probably the unit
    try:
        ram_clutter = ram_clutter.casefold().split(" ")
        value = None
        unit = None
        for i, part in enumerate(ram_clutter):
            if part.isdigit():
                # it's the number! but what's the unit?
                value = int(part)
                if i == len(ram_clutter) - 1:
                    # oh no, but it's the last element, let's just set it to
                    # bytes
                    unit = "b"
                else:
                    # so it's hopefully just 1 word after it
                    unit = ram_clutter[i + 1]
                break
        
        ram = human_readable_to_bytes(value, unit)
    except:
        # ¯\_(ツ)_/¯
        ram = None

    # now that we have CPU, GPU and RAM, make a setup and return to the studio
    setup = SystemSetup(cpu, gpu, ram)
    return setup


# vim:textwidth=80:
