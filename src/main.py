import os, sys
import json

import m64, aiff, soundbank
from misc import *


# Import an audio file as streamed audio into a decomp folder
def import_audio(decomp, inputAiff, replace=None,
    seqName=None, seqFilename=None, soundbankName=None, sampleName=None,
    loop=False, loopBegin=None, loopEnd=None,
    panning=None):

    validate_decomp(decomp)

    seqJsonData = load_json(os.path.join(decomp, "sound", "sequences.json"))
    
    # Generate names if required
    if seqName is None:
        seqName = "SEQ_" + os.path.splitext(os.path.basename(inputAiff))[0].upper().replace(' ', '_')
    if seqFilename is None:
        seqFilename = os.path.splitext(os.path.basename(inputAiff))[0].lower().replace(' ', '_')
    if soundbankName is None:
        soundbankName = os.path.splitext(os.path.basename(inputAiff))[0].lower().replace(' ', '_')
    if sampleName is None:
        sampleName = os.path.splitext(os.path.basename(inputAiff))[0].lower().replace(' ', '_')

    # Validate all names
    validate_name(seqName, "sequence name")
    validate_name(soundbankName, "soundbank name")
    validate_name(sampleName, "sample name")
    validate_name(seqFilename, "sequence filename")

    if replace is None:
        # Get sequence ID of new sequence
        seqId = find_new_seq_id(seqJsonData)
    else:
        # Remove old data before importing sequence
        # Check given sequence ID is valid
        try:
            if replace[:2].lower() == "0x":
                seqId = int(replace[2:], 16)
            else:
                seqId = int(replace)
        except ValueError:
            raise AudioManagerException("Invalid sequence ID '%s'" % replace)
        # Remove sequence entry from sequences.json and find corresponding soundbank
        oldSoundbank = None
        for name in seqJsonData.keys():
            try:
                if int(name[:2], 16) == seqId:
                    if isinstance(seqJsonData[name], dict): # Used for lakitu cutscene
                        oldSoundbank = seqJsonData[name]["banks"][0]
                    else:
                        oldSoundbank = seqJsonData[name][0]
                    seqJsonData.pop(name)
                    # Remove m64 file
                    delete_file(os.path.join(decomp, "sound", "sequences", "us", name+".m64"))
                    break
            except ValueError:
                continue

        if oldSoundbank is None:
            raise AudioManagerException("Sequence ID '%s' is out of range" % replace)

        soundbankPath = os.path.join(decomp, "sound", "sound_banks", oldSoundbank + ".json")
        if os.path.exists(soundbankPath):
            with open(soundbankPath, "r") as soundbankJson:
                soundbankJsonData = json.load(soundbankJson)

            # Check that the soundbank is a streamed audio soundbank and not a vanilla one
            if soundbankJsonData["sample_bank"] == "streamed_audio":
                # Remove referenced samples
                for inst in soundbankJsonData["instruments"].values():
                    delete_file(os.path.join(decomp, "sound", "samples", "streamed_audio", inst["sound"] + ".aiff"))
                # Remove soundbank file
                delete_file(soundbankPath)
    
    # Check that no names are duplicates
    check_names_for_duplicates(decomp, seqId, seqName, soundbankName, sampleName)

    # Split channels of the aiff file and move all the samples to the sample folder.
    # Also add loop points to the samples if required.
    splitFiles = aiff.process_aiff_file(inputAiff,
        os.path.join(decomp, "sound", "samples", "streamed_audio"),
        outputName=sampleName, loop=loop, loopBegin=loopBegin, loopEnd=loopEnd)
    
    # Create the m64 for the sequence.
    m64.create_m64(os.path.join(decomp, "sound", "sequences", "us", ("%02X_" % seqId) + seqFilename + ".m64"), numChannels=len(splitFiles), loop=loop, panning=panning)

    # Create the soundbank.
    soundbank.create_soundbank(decomp, soundbankName, splitFiles)

    # Begin reading the sequence id table.
    seqIdsPath = os.path.join(decomp, "include", "seq_ids.h")
    seqTable = load_table(seqIdsPath, "enum SeqId")

    if replace is not None:
        seqTable[seqId] = (seqName, "0x%02X" % seqId)
    else:
        seqTable.insert(-1, (seqName, "0x%02X" % seqId))

    # Save table
    save_table(seqIdsPath, "enum SeqId", seqTable)

    # Add entry of new sequence to sequences.json
    seqJsonData[("%02X_" % seqId) + seqFilename] = [soundbankName]

    with open(os.path.join(decomp, "sound", "sequences.json"), "w") as seqJson:
        json.dump(seqJsonData, seqJson, indent=4)
