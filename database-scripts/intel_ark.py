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
A module which parses Intel's archive for CPU information. 
"""
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

from helpers import CPU, save_cpus, human_readable_to_hertz
import dogelog


# product IDs, can't think of anything better than "bruteforcing"
STARTID = 27994
ENDID = 215570
RATE_LIMIT_DELAY=55


TARGETURL = "https://ark.intel.com/content/www/us/en/ark/products/{0}/i-am-a-dolphin.html"


def parse_cpu(website: BeautifulSoup, product_id: int) -> Optional[CPU]:
    """Parses the given Intel ARK website for a CPU."""
    # thanks for making accessing so easy btw.

    # a simple string used for identification of the CPU
    raw = website.find(attrs={"data-key": "ProcessorNumber"})
    if raw is None:
        # too old CPU, got no processor ID, I have no other idea how I could
        # identify it - just skip it
        return None
    model = raw.string.strip().casefold()

    # just a number like 42 or 0 or... 8
    raw = website.find(attrs={"data-key": "CoreCount"}).string
    corecount = int(raw)

    # a bit more complicated, could be "4.2 GHz" but also "   1337.42 MHz"
    raw = website.find(attrs={"data-key": "ClockSpeed"}).string.strip().split()
    value = float(raw[0])
    unit = raw[1]
    corespeed = human_readable_to_hertz(value, unit)

    return CPU(
            model,
            product_id,
            "intel",
            corecount,
            corespeed
        )


def parse(old_cpus: list[CPU]) -> list[CPU]:
    """
    Parses the Intel archive for CPUs. Ignores already present CPUs by comparing
    the product ID.
    """
    old_cpus = [cpu.product_id for cpu in old_cpus]
    cpus = []
    progress = dogelog.Progress("Extracting Intel CPUs", ENDID - STARTID)

    # just checking every possible product ID
    # (not using `id` as name because that would conflict with the builtin `id`
    # function
    for product_id in range(STARTID, ENDID + 1):
        if product_id in old_cpus:
            # we already know about this one, no need for stressing the server
            # unneededly
            dogelog.info(f"Skipping CPU {product_id}")
            continue
        progress.stack()

        try:
            response = requests.get(TARGETURL.format(product_id), timeout=10)
        except requests.Timeout:
            dogelog.error(f"Request for product ID {product_id} timed out")
            continue
        except requests.exceptions.ConnectionError:
            dogelog.error(f"Connection error for ID {product_id}")
            continue
        except KeyboardInterrupt:
            break

        if response.status_code == 404:
            continue
        elif response.status_code != 200:
            dogelog.error(f"Hitted the ratelimit, delaying next check for"\
                    "{RATE_LIMIT_DELAY} seconds. ID: {product_id}")
            time.sleep(RATE_LIMIT_DELAY)
        # else, website is okay

        website = BeautifulSoup(response.text, features="lxml")

        try:
            if "Processor" not in website.head.title.string:
                # not a CPU
                continue
        except:
            continue

        # well, it's a CPU then - let's parse it
        cpu = parse_cpu(website, product_id)

        if cpu is None:
            continue

        cpus.append(cpu)

    progress.finish()

    return cpus



# vim:textwidth=80:
