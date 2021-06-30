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
The actual GPU and CPU databases.
"""
import json
from os.path import join

import pkg_resources

from ._models import CPU, GPU

def _resource_contents(resource: str, subfolder: str = "resources") -> dict:
    """
    Returns the JSON contents of the given resource.

    A resource is a JSON file stored in the "resources" folder. It will be
    packaged and delivered to the enduser alongside with the actual package.
    """
    subpath = join(subfolder, resource)
    content = pkg_resources.resource_string(__name__, subpath)
    return json.loads(content)


ALL_CPUS = sorted([
    CPU.from_dict_entry(key, value)
    for key, value in
    _resource_contents("cpu-database.json").items()
], key=lambda cpu: cpu.model)
ALL_GPUS = sorted([
    GPU.from_dict_entry(key, value)
    for key, value in
    _resource_contents("gpu-database.json").items()
], key=lambda gpu: gpu.model)

MODEL_TO_CPU = {
    cpu.model: cpu
    for cpu in ALL_CPUS
}
MODEL_TO_GPU = {
    gpu.model: gpu
    for gpu in ALL_GPUS
}


# vim:textwidth=80:
