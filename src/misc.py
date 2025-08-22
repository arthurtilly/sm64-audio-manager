import os
import soundfile as sf
import json

class AudioManagerException(Exception):
    pass


# Delete a file but don't error if it doesn't exist
def delete_file(path):
    try:
        os.remove(path)
    except OSError:
        pass


# Determine if a folder is a valid decomp repo
def validate_decomp(path):
    # Check if Makefile exists in the folder
    if not os.path.exists(os.path.join(path, "Makefile")):
        raise AudioManagerException("Invalid decomp folder - no Makefile")
    # Check if include/seq_ids.h exists
    if not os.path.exists(os.path.join(path, "include", "seq_ids.h")):
        raise AudioManagerException("Invalid decomp folder - no include/seq_ids.h")


# Determine if a string is a valid symbol or file name
def validate_name(name, whichName):
    allowedCharacters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    for char in name:
        if char not in allowedCharacters:
            raise AudioManagerException("Invalid character '%s' in %s" % (char, whichName))
    if len(name) == 0:
        raise AudioManagerException("%s cannot be empty" % whichName.capitalize())


def check_names_for_duplicates(decomp, seqId, seqName=None, soundbankName=None, sampleName=None):
    # Check if sequence name is a duplicate
    if seqName is not None:
        seqIdsPath = os.path.join(decomp, "include", "seq_ids.h")
        seqTable = load_table(seqIdsPath, "enum SeqId")
        for id, (seq, _) in enumerate(seqTable):
            if seqName == seq and id != seqId:
                raise AudioManagerException("Sequence '%s' already exists" % seqName)
            
    # Sequence filename cannot be a duplicate as it needs the sequence ID
        
    # Check if soundbank name is a duplicate
    if soundbankName is not None:
        filename = soundbankName + ".json"
        destPath = os.path.join(decomp, "sound", "sound_banks", filename)
        if os.path.exists(destPath):
            raise AudioManagerException("Soundbank '%s' already exists" % filename)
        
    # Check if sample name is a duplicate
    if sampleName is not None:
        filenames = (sampleName + ".aiff", sampleName + "_1.aiff")
        for filename in filenames:
            destPath = os.path.join(decomp, "sound", "samples", "streamed_audio", filename)
            if os.path.exists(destPath):
                raise AudioManagerException("Sample '%s' already exists" % filename)


# Convert loop points from milliseconds to samples if required
def calculate_loops(file, loopBeginSamples, loopBeginMilli, loopEndSamples, loopEndMilli):
    begin = loopBeginSamples
    end = loopEndSamples

    with sf.SoundFile(file) as snd:
        sampleRate = snd.samplerate

    if loopBeginMilli is not None:
        begin = int(sampleRate * loopBeginMilli / 1000)
    if loopEndMilli is not None:
        end = int(sampleRate * loopEndMilli / 1000)

    return begin, end


# Process panning input and set defaults if necessary
def calculate_panning(pan, numChannels):
    if pan is None:
        if numChannels == 2:
            return (-63, 64)
        pan = 0

    if isinstance(pan, int):
        pan = [pan]
    if len(pan) == 1 and numChannels > 1:
        pan = pan * numChannels
    
    if len(pan) != numChannels:
        raise AudioManagerException("The number of panning values must be the same as the number of channels")
    for panVal in pan:
        if panVal < -63 or panVal > 64:
            raise AudioManagerException("Invalid pan value %d (must be between -63 and 64)" % pan)
    return pan

 
# Estimate the size of an audio file
def estimate_audio_size(audioPath):
    with sf.SoundFile(audioPath) as snd:
        nframes = len(snd)  # same as snd.frames
        nchannels = snd.channels
    size = nframes * nchannels * 9 / 16
    return size / 1048576


# Scan sequences.json to find the next available sequence ID
def find_new_seq_id(seqJson):
    id = 0
    for seqName in seqJson.keys():
        try:
            seqId = int(seqName[:2], 16)
        except ValueError:
            continue
        if seqId >= id:
            id = seqId + 1
    return id


# Scan sequences.json to build an array of all sequence filenames and enums
def scan_all_sequences(decomp):
    seqIdsPath = os.path.join(decomp, "include", "seq_ids.h")
    seqTable = load_table(seqIdsPath, "enum SeqId")

    with open(os.path.join(decomp, "sound", "sequences.json"), "r") as seqJson:
        seqJsonData = json.load(seqJson)

    numSeqs = find_new_seq_id(seqJsonData) - 1
    allSeqs = [None] * numSeqs

    for seqName in seqJsonData.keys():
        try:
            seqId = int(seqName[:2], 16)
        except ValueError:
            continue
        if seqId == 0: continue
        allSeqs[seqId - 1] = (seqName[3:],seqTable[seqId][0])

    return allSeqs

# Locate and load a C table from a file
def load_table(tablePath, tableIdentifier):
    with open(tablePath, "r") as f:
        fileLines = f.readlines()

    inTable = False
    table = []

    for i in range(len(fileLines)):
        if not inTable:
            # Check for start of table
            if tableIdentifier in fileLines[i]:
                inTable = True
        else:
            # Check for end of table
            if "}" in fileLines[i]:
                break
            if fileLines[i].strip() == "" or fileLines[i].strip().startswith("//"): continue
            # Table line format: "    ENTRY, // COMMENT"
            # Extract only number and comment
            tableEntry = fileLines[i].split(",")[0].strip()

            comment = None
            if "//" in fileLines[i]: 
                comment = fileLines[i].split("//")[1].strip()

            table.append((tableEntry, comment))

    if len(table) == 0:
        return None
    return table


# Write a C table back to its file after being modified
def save_table(tablePath, tableIdentifier, table):

    with open(tablePath, "r") as f:
        fileLines = f.readlines()

    newLines = []
    i = 0
    while i < len(fileLines):
        if tableIdentifier in fileLines[i]:
            newLines.append(fileLines[i].strip())
            for j in range(len(table)):
                if table[j][1] is None:
                    newLines.append("    %s," % table[j][0])
                else:
                    newLines.append("    %s,  // %s" % (table[j][0], table[j][1]))
            while "}" not in fileLines[i]:
                i += 1
        newLines.append(fileLines[i][:-1])
        i += 1

    with open(tablePath, "w") as f:
        f.write("\n".join(newLines) + "\n")
