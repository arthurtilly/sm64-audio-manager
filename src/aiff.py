import os
import soundfile as sf
import struct

from misc import *


# Add loop points to an AIFF file
def add_loop_to_aiff(aiffPath, loopBegin, loopEnd):
    # Defines the looping
    instChunk = struct.pack(
        ">4slbbbbbbhhhhhhh",
        b"INST", # ckID
        20, # ckSize
        0, 0, 0, 0, 0, 0, 0, # baseNote, detune, lowNote, highNote, lowVelocity, highVelocity, gain
        1, 1, 2, # sustainLoop - playMode, beginLoop, endLoop
        0, 0, 0) # releaseLoop - playMode, beginLoop, endLoop
    
    markChunk = struct.pack(
        ">4slHHL6sHL4s",
        b"MARK", # ckID
        26, # ckSize
        2, # numMarkers
        1, loopBegin, b"\x05start", # marker1 - id, position, name
        2, loopEnd, b"\x03end") # marker2 - id, position, name
    
    f = open(aiffPath, "ab+")
    f.write(instChunk)
    f.write(markChunk)
    f.close() 


def process_aiff_file(input, outputFolder, outputName=None, loop=True, loopBegin=None, loopEnd=None):
    # Read the AIFF file
    data, samplerate = sf.read(input, always_2d=True)  # shape: (frames, channels)
    numFrames, numChannels = data.shape

    # Process given loop points
    if loopBegin is None:
        loopBegin = 0
    if loopEnd is None:
        loopEnd = numFrames

    if loopBegin < 0 or loopBegin > numFrames:
        raise AudioManagerException(f"Loop beginning out of range: '{loopBegin}' (must be between 0 and {numFrames})")
    if loopEnd < 0 or loopEnd > numFrames:
        raise AudioManagerException(f"Loop end out of range: '{loopEnd}' (must be between 0 and {numFrames})")
    if loopBegin >= loopEnd:
        raise AudioManagerException("Loop beginning must be before loop end")

    # Process output name
    if outputName is None:
        outputName = os.path.splitext(os.path.basename(input))[0]
    if numChannels > 1:
        outputName = outputName + "_%d"

    os.makedirs(outputFolder, exist_ok=True)

    outputtedFiles = []

    # Split up the channels into seperate AIFF files
    for i in range(numChannels):
        if numChannels > 1:
            filename = (outputName % (i+1))
        else:
            filename = outputName
        output = os.path.join(outputFolder, filename + ".aiff")

        # Extract channel i and write as mono AIFF
        channel_data = data[:, i]
        sf.write(output, channel_data, samplerate, format='AIFF')

        # Add loop points
        if loop:
            add_loop_to_aiff(output, loopBegin, loopEnd)

        outputtedFiles.append(output)

    return outputtedFiles

def get_aiff_duration(path):
    try:
        with sf.SoundFile(path) as snd:
            nframes = len(snd)
            samplerate = snd.samplerate
            duration = nframes / samplerate
            return duration
    except sf.SoundFileError:
        raise AudioManagerException("Invalid AIFF file")
