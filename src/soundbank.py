import os
import datetime
import json

from misc import *


# Create a soundbank for decomp using the given sample names
def create_soundbank(decomp, name, samples):
    numInsts = len(samples)

    validate_decomp(decomp)

    # Initialise JSON data
    jsonData = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "sample_bank": "streamed_audio",
        "envelopes": {
            "envelope": [
                [1, 32700],
                "hang"
            ]            
        },
        "instruments": {},
    }

    # Add each sample as an instrument
    for i, sample in enumerate(samples):
        sampleName = os.path.splitext(os.path.basename(sample))[0]

        jsonData["instruments"]["channel_%d" % (i + 1)] = {
            "release_rate": 10,
            "envelope": "envelope",
            "sound": sampleName
        }

    # Create the instrument list
    jsonData["instrument_list"] = ["channel_%d" % (i + 1) for i in range(numInsts)]

    with open(os.path.join(decomp, "sound", "sound_banks", "%s.json" % name), "w") as jsonFile:
        json.dump(jsonData, jsonFile, indent=4)
