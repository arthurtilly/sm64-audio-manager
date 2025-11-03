import os
import datetime
import json
import math

from misc import *
import soundfile as sf

def tuning_float_to_semitones(tuning, samplePath):
    sampleRate = sf.info(samplePath).samplerate
    tuning *= (32000 / sampleRate)
    return int(round(math.log2(tuning) * 12))

def tuning_semitones_to_float(tuning, samplePath):
    sampleRate = sf.info(samplePath).samplerate
    tuning = 2 ** (tuning / 12)
    tuning *= (sampleRate / 32000)
    return tuning

def resolve_ifdef(data):
    if type(data) is dict and "ifdef" in data:
        if "VERSION_US" in data["ifdef"]:
            return data["then"]
        else:
            return data["else"]
    return data

# Sample data for json with optional tuning
class Sample:
    def __init__(self, data, bank):
        self.bank = bank
        if data is None: return
        data = resolve_ifdef(data)

        if type(data) is dict:
            self.name = data["sample"]
            self.tuning = tuning_float_to_semitones(data["tuning"], os.path.join(self.bank, self.name+".aiff"))
        else:
            self.name = data
            self.tuning = 0

    def to_data(self):
        if self.tuning != 0:
            return {"sample":self.name, "tuning":tuning_semitones_to_float(self.tuning, os.path.join(self.bank, self.name+".aiff"))}
        return self.name
    
class Instrument:
    def __init__(self, data, bank):
        self.sound = self.sound_lo = self.sound_hi = self.normal_range_hi = self.normal_range_lo = self.envelope = None
        self.release_rate = 208
        if data is None: return
        self.release_rate = data["release_rate"]
        self.sound = Sample(data["sound"], bank)
        self.envelope = data["envelope"]
        if "sound_lo" in data:
            self.sound_lo = Sample(data["sound_lo"], bank)
            self.normal_range_lo = data["normal_range_lo"]
        else:
            self.sound_lo = None
            self.normal_range_lo = None
        if "sound_hi" in data:
            self.sound_hi = Sample(data["sound_hi"], bank)
            self.normal_range_hi = data["normal_range_hi"]
        else:
            self.sound_hi = None
            self.normal_range_hi = None

    def to_data(self):
        # Add in a specific order to match order of vanilla
        data = {}
        data["release_rate"] = self.release_rate
        if self.normal_range_lo is not None:
            data["normal_range_lo"] = self.normal_range_lo
        if self.normal_range_hi is not None:
            data["normal_range_hi"] = self.normal_range_hi
        data["envelope"] = self.envelope
        if self.sound_lo is not None:
            data["sound_lo"] = self.sound_lo.to_data()
        data["sound"] = self.sound.to_data()
        if self.sound_hi is not None:
            data["sound_hi"] = self.sound_hi.to_data()
        return data
    
    def uses_advanced_options(self):
        if self.sound_lo is not None or self.sound_hi is not None:
            return True
        if self.sound.tuning != 0:
            return True
        return False

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

def get_sfx_banks(decomp):
    sequencesData = load_json(os.path.join(decomp, "sound", "sequences.json"))
    return sequencesData["00_sound_player"]

def soundbank_get_sfx_index(decomp, soundbankName):
    sfxBanks = get_sfx_banks(decomp)
    if not soundbankName in sfxBanks:
        return -1
    return sfxBanks.index(soundbankName)

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

def rename_instrument(decomp, soundbank, index, newInstrument):
    validate_name(newInstrument, "instrument name")
    jsonData = open_soundbank(decomp, soundbank)

    if newInstrument in jsonData["instrument_list"]:
        raise AudioManagerException(f"Instrument {newInstrument} already exists in soundbank {soundbank}")

    oldInstrument = jsonData["instrument_list"][index]
    jsonData["instrument_list"][index] = newInstrument

    # Rename instrument in instruments
    if "instruments" in jsonData:
        if oldInstrument in jsonData["instruments"]:
            jsonData["instruments"][newInstrument] = jsonData["instruments"].pop(oldInstrument)

    save_soundbank(decomp, soundbank, jsonData)

def delete_instrument(decomp, soundbank, instID):
    jsonData = open_soundbank(decomp, soundbank)
    instrument = jsonData["instrument_list"][instID]

    oldSamples = set()
    if instrument is not None:
        oldSamples = get_instrument_samples(decomp, soundbank, instrument)
        del jsonData["instruments"][instrument]

    del jsonData["instrument_list"][instID]
    save_soundbank(decomp, soundbank, jsonData)

    for sample in oldSamples:
        check_if_sample_unused(decomp, jsonData, sample)

# insert new empty instrument
def add_instrument(decomp, soundbank, index):
    jsonData = open_soundbank(decomp, soundbank)
    jsonData["instrument_list"].insert(index, None)
    save_soundbank(decomp, soundbank, jsonData)

def get_sample_bank(decomp, soundbank):
    jsonData = open_soundbank(decomp, soundbank)
    return resolve_ifdef(jsonData["sample_bank"])

def get_sample_bank_path(decomp, soundbank):
    return os.path.join(decomp, "sound", "samples", get_sample_bank(decomp, soundbank))

def get_all_samples_in_bank(decomp, samplebank):
    sampleFolder = os.path.join(decomp, "sound", "samples", samplebank)
    return sort_with_hex_prefix([f for f in os.listdir(sampleFolder) if f.endswith(".aiff")])

# Fetch data of given instrument
def get_instrument_data(decomp, soundbank, inst):
    jsonData = open_soundbank(decomp, soundbank)
    if not inst in jsonData["instruments"]:
        return Instrument(None, None)
    return Instrument(jsonData["instruments"][inst], get_sample_bank_path(decomp, soundbank))

def get_percussion_samples(decomp, soundbank):
    jsonData = open_soundbank(decomp, soundbank)
    samples = set()
    for percussionData in jsonData["instruments"]["percussion"]:
        sample = percussionData["sound"]
        if type(sample) is dict:
            samples.add(sample["sample"])
        else:
            samples.add(sample)
    return samples

def get_instrument_samples(decomp, soundbank, inst):
    if inst == "percussion":
        return get_percussion_samples(decomp, soundbank)
    data = get_instrument_data(decomp, soundbank, inst)
    samples = set()
    if data.sound is not None:
        samples.add(data.sound.name)
    if data.sound_lo is not None:
        samples.add(data.sound_lo.name)
    if data.sound_hi is not None:
        samples.add(data.sound_hi.name)
    return samples

def check_if_sample_unused(decomp, jsonData, sampleName):
    sampleBank = resolve_ifdef(jsonData["sample_bank"])
    # Check all soundbanks to see if the sample is used
    # If not, delete it
    for soundbank in scan_all_soundbanks(decomp):
        curJsonData = open_soundbank(decomp, soundbank)
        if resolve_ifdef(curJsonData["sample_bank"]) != sampleBank:
            continue
        for instName in curJsonData["instruments"].keys():
            if sampleName in get_instrument_samples(decomp, soundbank, instName):
                return
            
    samplePath = os.path.join(decomp, "sound", "samples", sampleBank, sampleName + ".aiff")
    if os.path.exists(samplePath):
        os.remove(samplePath)
           
# Overwrite and save data of given instrument
def save_instrument_data(decomp, soundbank, inst, data):
    # Get samples used by old instrument
    oldSamples = get_instrument_samples(decomp, soundbank, inst)

    # Save new data
    jsonData = open_soundbank(decomp, soundbank)

    jsonData["instruments"][inst] = data.to_data()
    cleanup_unused_envelopes(jsonData)
    save_soundbank(decomp, soundbank, jsonData)

    # If any old samples are no longer used, delete them
    for sample in oldSamples:
        check_if_sample_unused(decomp, jsonData, sample)

def get_envelope(decomp, soundbank, envelope):
    jsonData = open_soundbank(decomp, soundbank)
    return jsonData["envelopes"][envelope]

def add_envelope(decomp, soundbank, envelope):
    jsonData = open_soundbank(decomp, soundbank)
    for name, env in jsonData["envelopes"].items():
        # Test if envelopes are equal
        if env == envelope:
            return name
    # Add envelope
    def envelopeNameUsed(name):
        return name in jsonData["envelopes"]
    name = get_new_name("envelope0", envelopeNameUsed)
    jsonData["envelopes"][name] = envelope
    save_soundbank(decomp, soundbank, jsonData)
    return name

def cleanup_unused_envelopes(jsonData):
    usedEnvelopes = set()
    for name, inst in jsonData["instruments"].items():
        if name == "percussion":
            for perc in inst:
                usedEnvelopes.add(perc["envelope"])
        else:
            usedEnvelopes.add(inst["envelope"])
    jsonData["envelopes"] = {name: env for name, env in jsonData["envelopes"].items() if name in usedEnvelopes}
