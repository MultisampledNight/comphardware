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
Library for comparing hardware setups.

For most cases, the user_setup and the setup_from_clutter functions should
suffice. As an example, see this interactive session, where the user's setup is
compared with the minimum requirements of Satisfactory:

    In [1]: import comphardware

    In [2]: user_setup = comphardware.user_setup()

    In [3]: # let's just imagine that this response comes from an API

    In [4]: api_response = {
       ...:     "Processor": "i5-3570k 3.4 GHz 4 Core (64-Bit)",
       ...:     "Memory": "8 GB RAM",
       ...:     "Graphics": "GTX 760 2GB",
       ...: }

    In [5]: satisfactory_min_setup = comphardware.setup_from_clutter(
       ...:     api_response["Processor"],
       ...:     api_response["Graphics"],
       ...:     api_response["Memory"],
       ...: )

    In [6]: # can the PC of the user handle Satisfactory?

    In [7]: user_setup > satisfactory_min_setup
    Out[7]: False

    In [8]: # no :(

    In [9]: user_setup.gpu > satisfactory_min_setup.gpu
    Out[9]: True

    In [10]: user_setup.cpu > satisfactory_min_setup.cpu
    Out[10]: False

    In [11]: user_setup.ram > satisfactory_min_setup.ram
    Out[11]: False

    In [12]: # the GPU would actually be okay, but CPU and RAM aren't powerful enough

    In [13]: user_setup.cpu
    Out[13]:
            CPU(
                    model = "i5-2520M",
                    vendor = "intel",
                    corecount = 2,
                    clockspeed = 2500.0 MHz,
                    score = 36.08490566037736
            )

    In [14]: # hehe, well, okay, an i5-2520M might be really not as good as an i5-3570K
"""


__all__ = ["GPU", "CPU", "SystemSetup", "user_setup", "setup_from_clutter"]

__author__ = "MultisampledNight"
__version__ = "0.1.1"


from ._models import GPU, CPU, SystemSetup
from .helpers import user_setup, setup_from_clutter


# vim:textwidth=80:
