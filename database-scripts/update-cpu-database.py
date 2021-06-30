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
Creates a CPU database for CPUs by intel and amd. They might not be exhaustive.
"""
import intel_ark
import helpers
import dogelog


if __name__ == "__main__":
    dogelog.init()

    # the old CPUs, using the product ID to avoid asking the server for an
    # already known CPU
    old_cpus = helpers.load_cpus()
    old_cpus.sort(key=lambda cpu: cpu.product_id)

    # parsing all needed CPUs... AAAAAAAA
    cpus = intel_ark.parse(old_cpus)

    # done, let's clean up and save
    cpus.extend(old_cpus)
    cpus.sort(key=lambda cpu: cpu.model)
    helpers.save_cpus(cpus)
    dogelog.info(f"Done with CPUs, saved to:\n{helpers.CPU_DATABASE}")


# vim:textwidth=80:
