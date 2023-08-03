import os
import av

from misc import *

# Get executable path in the parent directory
#ffmpeg_executable = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ffmpeg.exe")

#print(ffmpeg.probe("Scattered and Lost.aiff"))

container = av.open("Scattered and Lost.aiff")

# get sample rate
print(container.streams.audio[0])

def get_audio_metadata(path):
    print(ffmpeg.probe("Scattered and Lost.aiff"))