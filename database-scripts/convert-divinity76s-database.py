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
Downloads and converts divinity76's database at
https://github.com/divinity76/intel-cpu-database to "our" database format.
"""
import json
import requests
import helpers
import dogelog


URL = "https://raw.githubusercontent.com/divinity76/intel-cpu-database/master/databases/intel_cpu_database.json"


def download(url: str) -> dict:
    """
    Downloads the given URL and uses json.loads to convert it to a dict.
    """
    dogelog.info("Downloading raw database")

    response = requests.get(URL)
    response.raise_for_status()
    return json.loads(response.text)


def convert(source: dict) -> list[helpers.CPU]:
    """
    Converts the given dict to "our" database format consisting out of a list.
    """
    # a small excerpt out of the source database
    # "42915": {
    #     "name": "Intel Core i5-750 Processor (8M Cache, 2.66 GHz)",
    #     "Essentials": {
    #         "Product Collection": "Legacy Intel Core Processors",
    #         "Code Name": "Products formerly Lynnfield",
    #         "Vertical Segment": "Desktop",
    #         "Processor Number": "i5-750",
    #         "Status": "Discontinued",
    #         "Launch Date": "Q3'09",
    #         "Lithography": "45 nm",
    #         "Use Conditions": "Server/Enterprise"
    #     },
    #     "Performance": {
    #         "# of Cores": "4",
    #         "# of Threads": "4",
    #         "Processor Base Frequency": "2.66 GHz",
    #         "Max Turbo Frequency": "3.20 GHz",
    #         "Cache": "8 MB SmartCache",
    #         "Bus Speed": "2.5 GT/s DMI",
    #         "TDP": "95 W",
    #         "VID Voltage Range": "0.6500V-1.4000V"
    #     },
    #     ...
    # },
    dogelog.info("Converting")
    cpus = []
    for key, specs in source.items():
        try:
            product_id = int(key)
            
            model = specs["Essentials"].get("Processor Number", None)
            if model is None:
                # just... don't care... welp
                continue

            corecount = int(specs["Performance"]["# of Cores"])
            
            raw = specs["Performance"]["Processor Base Frequency"].split(" ")
            value = float(raw[0])
            unit = raw[1]
            corespeed = helpers.human_readable_to_hertz(value, unit)

            cpus.append(helpers.CPU(
                model,
                product_id,
                "intel",
                corecount,
                corespeed,
            ))
        except (ValueError, KeyError):
            # uninteresting
            # maybe I could try to get other factors for caluculating a score
            # here, but still, uninteresting
            continue
    return cpus


if __name__ == "__main__":
    dogelog.init()

    source = download(URL)
    conv = convert(source)
    helpers.save_cpus(conv)

    dogelog.info("Done")


# vim:textwidth=80:
