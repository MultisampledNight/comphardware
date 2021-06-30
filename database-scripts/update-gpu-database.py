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
Creates a GPU database for GPUs by nvidia, amd and intel.
They might not be exhaustive nor correct.
"""
import wiki_gpu_tables
import helpers
import dogelog


GPU_NVIDIA_URL = "https://en.wikipedia.org/wiki/List_of_Nvidia_graphics_processing_units"
GPU_AMD_URL = "https://en.wikipedia.org/wiki/List_of_AMD_graphics_processing_units"
GPU_INTEL_URL = "https://en.wikipedia.org/wiki/List_of_Intel_graphics_processing_units"

gpu_vendors = [
        ("nvidia", GPU_NVIDIA_URL),
        ("amd", GPU_AMD_URL),
        ("intel", GPU_INTEL_URL),
    ]


if __name__ == "__main__":
    dogelog.init()
    dogelog.info("Beginning to parse GPUs...")

    # read in the old GPU database to avoid re-parsing already known GPUs
    old_gpus = helpers.load_gpus()
    old_gpus.sort(key=lambda gpu: gpu.model)

    # parse GPUs
    gpus = []
    for vendor, url in gpu_vendors:
        gpus.extend(wiki_gpu_tables.parse(url, old_gpus, vendor))

    # all implementations should skip already known GPUs, so we'll just add them
    # here manually
    gpus.extend(old_gpus)

    # cleaning up and saving
    gpus.sort(key=lambda gpu: gpu.model)
    helpers.save_gpus(gpus)
    dogelog.info(f"Done with GPUs, saved to:\n{helpers.GPU_DATABASE}")


# vim:textwidth=80:
