import os
import aifc
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
        24, # ckSize
        2, # numMarkers
        1, loopBegin, b"\x05start", # marker1 - id, position, name
        2, loopEnd, b"\x03end") # marker2 - id, position, name
    
    f = open(aiffPath, "ab+")
    f.write(instChunk)
    f.write(markChunk)
    f.close() 


# Takes an AIFF file, splits up every channel into a separate file, and adds a loop
def process_aiff_file(input, outputFolder, outputName=None, loop=True, loopBegin=None, loopEnd=None):
    # Open the AIFF file
    aiffIn = aifc.open(input, "r")
    numChannels = aiffIn.getnchannels()
    numFrames = aiffIn.getnframes()

    # Process given loop points
    if loopBegin is None:
        loopBegin = 0
    if loopEnd is None:
        loopEnd = numFrames

    if loopBegin < 0 or loopBegin > numFrames:
        raise AudioManagerException("Loop beginning out of range: '%d' (must be between 0 and %d)" % (loopBegin, numFrames))
    if loopEnd < 0 or loopEnd > numFrames:
        raise AudioManagerException("Loop end out of range: '%d' (must be between 0 and %d)" % (loopEnd, numFrames))
    if loopBegin >= loopEnd:
        raise AudioManagerException("Loop beginning must be before loop end")

    # Process output name
    if outputName is None:
        outputName = os.path.splitext(os.path.basename(input))[0]
    if numChannels > 1:
        outputName = outputName + "_%d"

    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)

    soundData = aiffIn.readframes(numFrames)
    outputtedFiles = []

    # Split up the channels into seperate AIFF files
    for i in range(numChannels):
        # Create a new AIFF file
        if numChannels > 1:
            filename = (outputName % (i+1))
        else:
            filename = outputName
        output = os.path.join(outputFolder, filename + ".aiff")
        aiffOut = aifc.open(output, "w")
        aiffOut.setparams(aiffIn.getparams())
        aiffOut.setnchannels(1)

        # Write only the data from channel i
        channelData = (soundData[j+2*i:j+2*i+2] for j in range(0, numFrames*2*numChannels, 2*numChannels))
        aiffOut.writeframes(b"".join(channelData))

        aiffOut.close()

        # Add loop points
        if loop:
            add_loop_to_aiff(output, loopBegin, loopEnd)

        outputtedFiles.append(output)

    aiffIn.close()
    return outputtedFiles
