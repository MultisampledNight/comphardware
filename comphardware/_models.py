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
Data models, like CPUs, GPUs, or a system configuration.
"""
import json


class GPU:
    """
    A graphics processing unit. VRAM is always thought in bytes, clockspeed
    always in hertz.
    
    The score is the primary value you should use for comparing these, 0
    represents all stats being 0, and 100 represents an nvidia RTX 3080.

    Hint: <, > and == delegate to comparing the score.
    """
    def __init__(self, model: str, vendor: str, vram: int, clockspeed: float, score: float):
        self.model = model
        self.vendor = vendor
        self.vram = vram
        self.clockspeed = clockspeed
        self.score = score

    def __repr__(self) -> str:
        # goal is to look like
        # GPU(
        #     model = "stonks",
        #     vendor = "notstonks,
        #     ...
        # )
        return f'''\tGPU(
\t\tmodel = "{self.model}",
\t\tvendor = "{self.vendor}",
\t\tvram = {self.vram / (1024 ** 2)} MiB,
\t\tclockspeed = {self.clockspeed / (10 ** 6)} MHz,
\t\tscore = {self.score}
\t)'''
    
    def __str__(self) -> str:
        # suitable for the end user
        return f"{self.vendor} {self.model}"

    def __lt__(self, other) -> bool:
        if other is None:
            return False
        if isinstance(other, float):
            return self.score < other

        return self.score < other.score

    def __gt__(self, other) -> bool:
        if other is None:
            return False
        if isinstance(other, float):
            return self.score > other

        return self.score > other.score

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        if isinstance(other, float):
            return self.score == other

        return self.score == other.score

    @staticmethod
    def from_dict_entry(key: str, value: dict):
        """
        Tries to construct a GPU from the given database entry.
        """
        # as an example, here is a nvidia GeForce 1080:
        # "GeForce GTX 1080": {
        #     "vendor": "nvidia",
        #     "vram": 8589934592.0,
        #     "corespeed": 160000000.0,
        #     "codename": "GP104-410-A1",
        #     "score": 45.55555555555556
        # }
        return GPU(
                key,
                value["vendor"],
                value["vram"],
                value["corespeed"],
                value["score"],
            )


class CPU:
    """
    Central processing unit. Core count does actually mean core count and not
    thread count, clock speed is always hertz.

    The score is the value you should use for comparing and sorting different
    CPUs. Value 0 of the score means corecount and clockspeed being 0, 100 means
    an intel i9-11900K.

    Hint: You can use >, < and == of two CPU instances to compare the score
    implicitly.
    """
    def __init__(self,
            model: str,
            vendor: str,
            corecount: int,
            clockspeed: float,
            score: float):
        self.model = model
        self.vendor = vendor
        self.corecount = corecount
        self.clockspeed = clockspeed
        self.score = score

    def __repr__(self) -> str:
        # optimally I want this to look like
        # CPU(
        #     model = "wow",
        #     vendor = "doge",
        #     ...
        # )
        return f'''\tCPU(
\t\tmodel = "{self.model}",
\t\tvendor = "{self.vendor}",
\t\tcorecount = {self.corecount},
\t\tclockspeed = {self.clockspeed / (10.0 ** 6)} MHz,
\t\tscore = {self.score}
\t)'''
    
    def __str__(self) -> str:
        # intended to be displayed to the end user
        return f"{self.vendor} {self.model}"

    def __lt__(self, other) -> bool:
        if other is None:
            return False
        if isinstance(other, float):
            return self.score < other

        return self.score < other.score

    def __gt__(self, other) -> bool:
        if other is None:
            return False
        if isinstance(other, float):
            return self.score > other

        return self.score > other.score

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        if isinstance(other, float):
            return self.score == other

        return self.score == other.score

    @staticmethod
    def from_dict_entry(key: str, value: dict):
        """
        Tries to construct a CPU from the given entry in the database.
        """
        # and here is an intel i7-975
        # "i7-975": {
        #     "product_id": 37153,
        #     "vendor": "intel",
        #     "corecount": 4,
        #     "corespeed": 3330000000.0,
        #     "score": 56.41509433962264
        # }
        return CPU(
                key,
                value["vendor"],
                value["corecount"],
                value["corespeed"],
                value["score"],
            )


class SystemSetup:
    """
    A whole system configuration, used to compare full setups. Includes CPU,
    GPU and RAM. Intended to be used like

        actualsetup > requiredsetup

    RAM is always thought in bytes.

    When using < or >, you are comparing the whole setup. That means, if any of
    the contained components has a bigger/smaller score than the other setup, it
    automatically returns False. This is done in thought of games, where having
    a good GPU does not compensate a bad CPU, or vice versa.

    Note that you might want to manually compare the components instead, because
    then you can depending on the circumstances say the user more exact where
    their setup is not sufficent enough.
    """
    def __init__(self,
            cpu: CPU,
            gpu: GPU,
            ram: int):
        self.cpu = cpu
        self.gpu = gpu
        self.ram = ram

    def __repr__(self):
        # just a container, so use __repr__ on the GPU and the CPU
        return f'''SystemSetup(
{repr(self.cpu)},
{repr(self.gpu)},
\t{self.ram / (1024 ** 3)} GiB RAM,
)'''

    def __str__(self):
        # delegates to __repr__
        return self.__repr__()
    def __lt__(self, other):
        return all([
                (self.cpu or 0.0) < (other.cpu or 0.0),
                (self.gpu or 0.0) < (other.gpu or 0.0),
                (self.ram or 0.0) < (other.ram or 0.0),
            ])

    def __gt__(self, other):
        return all([
                (self.cpu or 0.0) > (other.cpu or 0.0),
                (self.gpu or 0.0) > (other.gpu or 0.0),
                (self.ram or 0.0) > (other.ram or 0.0),
            ])


# vim:textwidth=80:
