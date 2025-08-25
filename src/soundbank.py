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
            "envelope0": [
                [6, 32700],
                [6, 32700],
                [32700, 29430],
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
            "envelope": "envelope0",
            "sound": sampleName
        }

    # Create the instrument list
    jsonData["instrument_list"] = ["channel_%d" % (i + 1) for i in range(numInsts)]

    with open(os.path.join(decomp, "sound", "sound_banks", "%s.json" % name), "w") as jsonFile:
        json.dump(jsonData, jsonFile, indent=4)

def open_soundbank(decomp, soundbank):
    soundbankPath = os.path.join(decomp, "sound", "sound_banks", "%s.json" % soundbank)
    return load_json(soundbankPath)

def save_soundbank(decomp, soundbank, jsonData):
    soundbankPath = os.path.join(decomp, "sound", "sound_banks", "%s.json" % soundbank)
    with open(soundbankPath, "w") as jsonFile:
        json.dump(jsonData, jsonFile, indent=4)

def sort_with_hex_prefix(array):
    def sort_key(item):
        try:
            return (0, int(item[:2], 16), item[2:])
        except ValueError:
            return (1, item)

    return sorted(array, key=sort_key)

# Scan soundbank folder and return sorted list
def scan_all_soundbanks(decomp):
    soundbankPath = os.path.join(decomp, "sound", "sound_banks")
    soundbankFiles = [os.path.splitext(f)[0] for f in os.listdir(soundbankPath) if f.endswith(".json")]
    return sort_with_hex_prefix(soundbankFiles)

def get_instruments(decomp, soundbankName):
    return open_soundbank(decomp, soundbankName).get("instrument_list", [])

def soundbank_get_sfx_index(decomp, soundbankName):
    sequencesData = load_json(os.path.join(decomp, "sound", "sequences.json"))
    if not soundbankName in sequencesData["00_sound_player"]:
        return -1
    return sequencesData["00_sound_player"].index(soundbankName)

def rename_soundbank(decomp, oldSoundbank, newSoundbank):
    validate_name(newSoundbank, "soundbank name")
    if os.path.exists(os.path.join(decomp, "sound", "sound_banks", f"{newSoundbank}.json")):
        raise AudioManagerException(f"Soundbank {newSoundbank} already exists")
    # Rename soundbank file
    os.rename(
        os.path.join(decomp, "sound", "sound_banks", f"{oldSoundbank}.json"),
        os.path.join(decomp, "sound", "sound_banks", f"{newSoundbank}.json")
    )
    # Load sequences.json
    sequencesJson = os.path.join(decomp, "sound", "sequences.json")
    jsonData = load_json(sequencesJson)
    for name, element in jsonData.items():
        bankList = None
        if isinstance(element, list):
            bankList = element
        elif isinstance(element, dict):
            bankList = element.get("banks")
        else:
            continue
        # Update any instances of old bank
        if bankList is not None:
            for i, item in enumerate(bankList):
                if item == oldSoundbank:
                    bankList[i] = newSoundbank
    with open(sequencesJson, "w") as jsonFile:
        json.dump(jsonData, jsonFile, indent=4)

def rename_instrument(decomp, soundbank, oldInstrument, newInstrument):
    validate_name(newInstrument, "instrument name")
    jsonData = open_soundbank(decomp, soundbank)

    if not oldInstrument in jsonData["instrument_list"]:
        raise AudioManagerException(f"Instrument {oldInstrument} does not exist in soundbank {soundbank}")
    if newInstrument in jsonData["instrument_list"]:
        raise AudioManagerException(f"Instrument {newInstrument} already exists in soundbank {soundbank}")

    jsonData["instrument_list"][jsonData["instrument_list"].index(oldInstrument)] = newInstrument

    # Rename instrument in instruments
    if "instruments" in jsonData:
        if oldInstrument in jsonData["instruments"]:
            jsonData["instruments"][newInstrument] = jsonData["instruments"].pop(oldInstrument)

    save_soundbank(decomp, soundbank, jsonData)

def delete_instrument(decomp, soundbank, instID):
    jsonData = open_soundbank(decomp, soundbank)
    instrument = jsonData["instrument_list"][instID]
    if instrument is not None:
        del jsonData["instruments"][instrument]
    del jsonData["instrument_list"][instID]
    save_soundbank(decomp, soundbank, jsonData)

# insert new empty instrument
def add_instrument(decomp, soundbank, index):
    jsonData = open_soundbank(decomp, soundbank)
    jsonData["instrument_list"].insert(index, None)
    save_soundbank(decomp, soundbank, jsonData)

def get_sample_bank(decomp, soundbank):
    jsonData = open_soundbank(decomp, soundbank)
    return jsonData["sample_bank"]

def get_all_samples_in_bank(decomp, samplebank):
    sampleFolder = os.path.join(decomp, "sound", "samples", samplebank)
    return sort_with_hex_prefix([f for f in os.listdir(sampleFolder) if f.endswith(".aiff")])

def get_instrument_data(decomp, soundbank, inst):
    jsonData = open_soundbank(decomp, soundbank)
    return jsonData["instruments"][inst]

def change_instrument_data(decomp, soundbank, inst, newData):
    jsonData = open_soundbank(decomp, soundbank)
    if inst not in jsonData["instruments"]:
        raise AudioManagerException(f"Instrument {inst} does not exist in soundbank {soundbank}")
    jsonData["instruments"][inst] = newData
    save_soundbank(decomp, soundbank, jsonData)

def save_instrument(decomp, soundbank, inst,
                    sample, releaseRate,
                    sampleLo, rangeLo,
                    sampleHi, rangeHi):
    # Get envelope
    jsonData = open_soundbank(decomp, soundbank)
    if inst in jsonData["instruments"]:
        envelope = jsonData["instruments"][inst]["envelope"]
    else:
        envelope = "envelope0"
    
    newData = {
        "release_rate": releaseRate,
        "envelope": envelope,
        "sound": sample,
    }
    if sampleLo is not None:
        newData["sound_lo"] = sampleLo
        newData["normal_range_lo"] = rangeLo
    if sampleHi is not None:
        newData["sound_hi"] = sampleHi
        newData["normal_range_hi"] = rangeHi

    change_instrument_data(decomp, soundbank, inst, newData)
