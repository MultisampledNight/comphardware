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
A helpers module for hardware parsing and comparing, containing common
constructs and helper functions.
"""
import json
import os


def resource_path(resource_name: str, subfolder: str = "resources") -> str:
    """
    Returns the path for the given resource. A resource is a file that has to do
    with the package, but is only a data source or similar, not a Python script.
    """
    return os.path.abspath(
            os.path.join(
                os.path.dirname(
                    os.path.realpath(
                        os.path.abspath(__file__)
                    )
                ),                # /database-scripts
                "..",             # /
                "comphardware",   # /comphardware
                subfolder,        # /comphardware/resources
                resource_name,    # /comphardware/resources/stonks.json
            )
        )


CPU_DATABASE = resource_path("cpu-database.json")
GPU_DATABASE = resource_path("gpu-database.json")


class CPU:
    """
    A data model of a CPU. (Clock) Speed is always thought in hertz. The product
    ID is stored in case of a re-retrieval of the database later on.
    """
    def __init__(self,
            model: str,
            product_id: int,
            vendor: str,
            corecount: int,
            corespeed: int):
        self.model = model
        self.product_id = product_id
        self.vendor = vendor
        self.corecount = corecount
        self.corespeed = corespeed

        # calculate the score of the CPU
        # quite similar to the GPU, except that the upper bound is a i9-11900K,
        # which won't change as well
        corescore = float(corecount) / 8.0
        speedscore = corespeed / (5.30 * (10 ** 9))

        self.score = (corescore + speedscore) * 100.0 / 2.0


class GPU:
    """
    A data model of a GPU. Memory is always thought in bytes, (clock) speed always
    in hertz.
    """
    def __init__(self,
            model: str,
            vendor: str,
            vram: int,
            corespeed: int,
            codename: str):
        self.model = model
        self.vendor = vendor
        self.vram = vram
        self.corespeed = corespeed
        self.codename = codename

        # calculate the score of the GPU
        # the idea is that a score of 0.0 would be a Riva 128, while a score of
        # 100.0 would be a GeForce RTX 3080
        # there is no upper bound, 100.0 should always, really always represent
        # the power of an RTX 3080, if a newer generation with more power comes
        # out, it might have a score over 100
        vramscore = float(vram) / (10.0 * (1024 ** 3))
        corespeedscore = float(corespeed) / (1440.0 * (10 ** 6))

        self.score = (vramscore + corespeedscore) * 100.0 / 2.0


def load_cpus(targetfile: str = CPU_DATABASE):
    try:
        with open(targetfile) as fh:
            raw_cpus = json.load(fh)
        cpus = []
        for (model, specs) in raw_cpus.items():
            cpus.append(CPU(
                model,
                specs["product_id"],
                specs["vendor"],
                specs["corecount"],
                specs["corespeed"],
            ))
        return cpus
    except FileNotFoundError:
        return []


def save_cpus(cpus: list[CPU], targetfile: str = CPU_DATABASE):
    """Saves the CPUs into a JSON file."""
    conv_cpus = {
        cpu.model: {
            "product_id": cpu.product_id,
            "vendor": cpu.vendor,
            "corecount": cpu.corecount,
            "corespeed": cpu.corespeed,
            "score": cpu.score,
        } for cpu in cpus
    }
    with open(targetfile, "w") as fh:
        json.dump(conv_cpus, fh)


def load_gpus(targetfile: str = GPU_DATABASE):
    try:
        with open(targetfile) as fh:
            raw_gpus = json.load(fh)
        gpus = []
        for (model, specs) in raw_gpus.items():
            gpus.append(GPU(
                model,
                specs["vendor"],
                specs["vram"],
                specs["corespeed"],
                specs["codename"],
            ))
        return gpus
    except FileNotFoundError:
        # database doesn't exist yet uwu
        return []


def save_gpus(gpus: list[GPU], targetfile: str = GPU_DATABASE):
    """Saves the GPUs into a JSON file."""
    # convert them into a nicer dict first
    conv_gpus = {
            gpu.model: {
                "vendor": gpu.vendor,
                "vram": gpu.vram,
                "corespeed": gpu.corespeed,
                "codename": gpu.codename,
                "score": gpu.score,
            } for gpu in gpus
        }
    with open(targetfile, "w") as fh:
        json.dump(conv_gpus, fh)


def human_readable_to_bytes(value: int, unit: str) -> int:
    """
    Converts the given value and unit to bytes.

    As an example, it should convert (8, GB) to 8388608.
    Even though technically MB means 1000 * 1000, many producers actually mean
    MiB, which is 1024 * 1024. Even Windows displays as unit GB, even though
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


# vim:textwidth=80:
