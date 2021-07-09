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
Functions for getting information on the current running platform.
"""
import platform
import subprocess
from typing import Optional
from xml.etree import ElementTree

import cpuinfo
import psutil

gl_available = True
try:
    from OpenGL.GL import glGetString, GL_RENDERER
    from OpenGL.GLUT import (glutInit, glutCreateWindow, glutIdleFunc,
        glutDisplayFunc, glutMainLoop, glutLeaveMainLoop, glutSetOption,
        GLUT_ACTION_ON_WINDOW_CLOSE, GLUT_ACTION_GLUTMAINLOOP_RETURNS)
except ImportError:
    gl_available = False
    pass

from ._models import GPU, CPU
from .helpers import find_gpu_by_model, find_cpu_by_model, SystemSetup


# formed with help from https://docs.microsoft.com/en-us/windows/win32/cimwin32prov/win32-videocontroller
WMIC_QUERY_COMMAND = ["WMIC", "PATH", "Win32_VideoController", "GET", "Name"]
# and that one is just straight taken from the manpage
IOREG_COMMAND = ["/usr/sbin/ioreg", "-la"]


_cached_cpu = 0
_cached_gpu = 0


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
    if not gl_available:
        # then we can just forget it directly
        raise NotImplemented("GL couldn't be loaded!")

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

    WARNING: Only implemented for Linux, Woe and Mac yet! No BSD or Sun. Raises
    a NotImplemented if the platform isn't supported (yet).
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

    elif system == "Darwin":
        # the idea is to parse the output of `/usr/sbin/ioreg -la`, which is
        # XML, and then to find the one string value which contains "MTLDriver"
        # that's the GPU
        
        # first of all, run ioreg
        ioreg_output = subprocess.check_output(IOREG_COMMAND, text=True)

        # for parsing the XML etree isn't a bad choice I guess
        tree = ElementTree.fromstring(ioreg_output)
        root = tree.getroot()

        # iterate through all <string> elements and find the designated one by
        # looking if it contains "MTLDriver"
        for string_element in root.iter(tag="string"):
            if (string_element.text is not None
                and "MTLDriver" in string_element.text):
                # that's the one!
                gpu_model = string_element.text.removesuffix("MTLDriver")
                break

    else:
        raise NotImplemented(f"Platform '{system}' not implemented!")

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
    Tries to extract the current system configuration.

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


# vim:tw=80:
