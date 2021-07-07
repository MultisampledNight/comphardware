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
import platform
import subprocess
from typing import Optional

import cpuinfo
import psutil
from OpenGL.GL import glGetString, GL_RENDERER
from OpenGL.GLUT import (glutInit, glutCreateWindow, glutIdleFunc,
    glutDisplayFunc, glutMainLoop, glutLeaveMainLoop, glutSetOption,
    GLUT_ACTION_ON_WINDOW_CLOSE, GLUT_ACTION_GLUTMAINLOOP_RETURNS)

from .data import ALL_GPUS, ALL_CPUS, MODEL_TO_GPU, MODEL_TO_CPU
from ._models import GPU, CPU, SystemSetup


# formed with help from https://docs.microsoft.com/en-us/windows/win32/cimwin32prov/win32-videocontroller
WMIC_QUERY_COMMAND = ["WMIC", "PATH", "Win32_VideoController", "GET", "Name"]

_cached_cpu = 0
_cached_gpu = 0


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
        match = sequence_matcher.find_longest_match()

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


def user_cpu() -> CPU:
    """
    Tries to determine the user's CPU, depending on the current platform.
    Returns None if the CPU can't be found in the database or is unable to be
    determined.
    """
    global _cached_cpu

    # there is no need in trying to extract it again if we know it already
    if not isinstance(_cached_cpu, int):
        return _cached_cpu

    # first find the CPU model itself (just misuse py-cpuinfo here)
    # thanks Dummerle! uwu
    cluttered_cpu = cpuinfo.get_cpu_info().get("brand_raw", None)

    # returning preliminary if the CPU string is empty
    if not cluttered_cpu:
        return None

    # cluttered_cpu could now look like Intel(R) Core(TM) i9-1337M CPU @ 4.20GHz
    # since the model is actually i9-1337M, we have to search every single entry
    # if it's in it
    actual_cpu = find_cpu_by_model(cluttered_cpu)

    _cached_cpu = actual_cpu

    return actual_cpu


def _user_gpu_by_opengl() -> str:
    """
    Tries to determine the GPU model name by quickly opening a window with GLUT,
    retrieving the renderer, and exiting as fast as possible.

    NOTE: Raises an exception (OpenGL.error.NullFunctionError to be exact) if
    GLUT/freeglut isn't installed. Be sure to catch that/everything if you don't
    want your application to randomly crash.
    NOTE 2: Don't even try to call this a second time. GLUT really doesn't like
    being initialized twice.
    """
    # this is the most portable solution I found, even though on laptops with
    # iGPU and dGPU this might not be consistent (such as on mine)
    glutInit()
    # if this is unset, GLUT just thinks that exiting the whole application is
    # fine (a bit like the "this is fine" meme)
    glutSetOption(GLUT_ACTION_ON_WINDOW_CLOSE, GLUT_ACTION_GLUTMAINLOOP_RETURNS)
    glutCreateWindow("comphardware tries to get the GPU, please ignore")

    renderer = None
    
    def get_renderer_and_exit():
        """
        Our one-way function to give to GLUT for getting the renderer and
        exiting directly
        """
        nonlocal renderer
        # yeet the renderer in
        renderer = glGetString(GL_RENDERER)\
            .decode(errors="ignore")\
            .strip()\
            .casefold()
        # exit asap
        glutLeaveMainLoop()
    
    # doubled won't hurt too much I guess
    glutIdleFunc(get_renderer_and_exit)
    glutDisplayFunc(get_renderer_and_exit)
    glutMainLoop()

    return renderer


def _user_gpu_by_platform() -> str:
    """
    Tries to get the user's GPU by a platform dependent way, such as with WMIC
    on Woe and lspci on Linux (or pciconf on BSD, but that's unimplemented yet.)

    WARNING: Only implemented for Linux and Woe yet! No Mac OS, no BSD. Raises
    an NotImplemented if the platform isn't supported (yet).
    """
    gpu_model = None
    system = platform.system()

    if system == "Linux":
        lspci_output = subprocess.check_output("lspci", text=True).split("\n")
        # a line in the output of lspci looks like this
        #   01:00.0 VGA compatible controller: NVIDIA Corporation GF119M [NVS 4200M] (rev a1)
        # I'll just split at : and take the last element (note the : directly at
        # the start)
        for line in lspci_output:
            if line.strip() == "":
                continue
            elif "VGA compatible controller" in line:
                colon_splitted = line.split(":")
                raw_model = colon_splitted[-1]

                gpu_model = ""
                # let's remove clutter like (rev a1)
                for i, char in enumerate(raw_model):
                    if char == "(":
                        # well, the perfect example: (rev a1)
                        break
                    elif char == "]":
                        # oh, that's way more interesting than the rest of the
                        # raw model (like you see above with [NVS 4200M])

                        # illustration:
                        #   doging doge 21235 doge [Doge 4450A] (doge)
                        #                                     ^
                        #                                     i
                        before_closing_bracket = raw_model[:i]
                        gpu_model = before_closing_bracket.split("[")[-1]
                        break  # if we wouldn't break here, it would happily
                               # append everything behind ] also to the GPU
                               # model
                    else:
                        gpu_model += char

                # not breaking as I found the last card being more important
                # (heavily depends on the setup though)

    elif system == "Windows":
        # yep, a query using WMIC might seem a bit weird, but maybe relying on
        # WMIC is better than having wmi as dependency (which failed on Wine
        # qwq)
        # the output of the WMIC query looks like this
        #   "Name                    \r\nNVIDIA GeForce GTX 470  \r\n"
        wmic_query_output = subprocess \
            .check_output(WMIC_QUERY_COMMAND) \
            .decode(encoding="utf-16")  # thanks for that jumpscare, UTF-16

        # so what should we do? of course, we just take the second line,
        # whatever
        gpu_model = wmic_query_output.split("\r\n")[1]
    else:
        raise NotImplented(f"Platform {system} not implemented!")

    return gpu_model


def user_gpu(force_no_window=False) -> Optional[GPU]:
    """
    Tries to get the GPU by
    
    1. Trying to open a window with GLUT/freeglut, creating an OpenGL context
       and getting the renderer (not tried if force_no_window is set to True)
    2. Using a platform-dependent way, which is often way less precise though.

    Returns None if all methods failed.
    """
    global _cached_gpu
    # first of all, do we have it cached? if yes, just return it
    if not isinstance(_cached_gpu, int):
        return _cached_gpu

    # then try all methods we've got so far
    gpu_model = None
    if not force_no_window:
        try:
            gpu_model = _user_gpu_by_opengl()
        except:
            # either GLUT wasn't found or I fell in one of the various holes you
            # can fall in when using OpenGL/GLUT
            # either way, unable to extract GPU
            pass
    
    if gpu_model is None:
        try:
            gpu_model = _user_gpu_by_platform()
        except NotImplemented:
            # platform unsupported :(
            pass

    if gpu_model is None:
        return None

    actual_gpu = find_gpu_by_model(gpu_model)
    _cached_gpu = actual_gpu

    return actual_gpu


def user_setup() -> SystemSetup:
    """
    Tries to extract the current system configuration by using platform and
    PyOpenGL's GLUT bindings. GLUT has to be installed for this.

    The CPU and GPU remain cached, the RAM and so the actual setup however are
    not. This is partly due to technical reasons (GLUT doesn't like
    double-initializing) and partly due to the fact that swap, which is also
    counted as RAM, could change anytime. So don't fear calling this
    consequently if you need the user's setup than once.
    """
    cpu = user_cpu()
    gpu = user_gpu()
    total_ram = psutil.virtual_memory().total

    setup = SystemSetup(
        cpu,
        gpu,
        total_ram,
    )

    return setup


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
