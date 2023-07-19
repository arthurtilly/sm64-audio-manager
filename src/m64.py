import struct

from misc import *


# Create an m64
def create_m64(outputPath, numChannels=1, loop=False, panning=None):
    channelBits = 2**numChannels - 1

    panning = calculate_panning(panning, numChannels)

    mainHeaderLength = 23 + 3 * numChannels + (3 if loop else 0)
    # M64 Header
    m64 = struct.pack(
        ">BBBBBHBB",
        0xD3, 0x20, # SEQ_MUTE_BEHAVIOR
        0xD5, 0x3F, # SEQ_MUTE_SCALE
        0xD7, channelBits, # SEQ_CHANNEL_ENABLE
        0xDB, 127) # SEQ_VOLUME
    
    for channel in range(numChannels):
        m64 += struct.pack(
            ">BH",
            0x90 + channel, mainHeaderLength + 19 * channel) # SEQ_CHANNEL_POINTER

    m64 += struct.pack(
        ">BBBHBBBH",
        0xDD, 0x30, # SEQ_TEMPO
        0xFD, 0x8000 | 6, # SEQ_TIMESTAMP
        0xDD, 1, # SEQ_TEMPO
        0xFD, 0xFFFF) # SEQ_TIMESTAMP

    if loop:
        m64 += struct.pack(
            ">BH",
            0xFB, 9) # SEQ_BRANCH_ABS_ALWAYS
        
    m64 += struct.pack(
        ">BHB",
        0xD6, channelBits, # SEQ_CHANNEL_DISABLE
        0xFF) # SEQ_END_OF_DATA
    
    # Channel Header - Length = 19
    for channel in range(numChannels):
        m64 += struct.pack(
            ">BBHBBBBBBBBBBBBHB",
            0xC4, # CHN_START
            0x90, mainHeaderLength + 19 * numChannels, # CHN_TRACK_POINTER
            0xDD, panning[channel] + 0x3F, # CHN_PAN
            0xDF, 127, # CHN_VOLUME
            0xD3, 0, # CHN_PITCH_BEND
            0xD4, 0, # CHN_EFFECT
            0x6F, # CHN_PRIORITY_US_MAX
            0xC1, channel, # CHN_INSTRUMENT
            0xFD, 0xFFFF, # CHN_TIMESTAMP
            0xFF) # CHN_END_OF_DATA
        
    m64 += struct.pack(
        ">BBBHBHBB",
        0xC2, 0, # TRK_TRANSPOSE
        0xC0, 0x8000 | 5, # TRK_TIMESTAMP
        0x40 + 0x27, 0xFFFF, 127, # TRK_NOTE_TV - pitch, timestamp, velocity
        0xFF) # TRK_END_OF_DATA

    with open(outputPath, "wb") as f:
        f.write(m64)
