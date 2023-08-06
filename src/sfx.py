from misc import *
from dataclasses import dataclass

soundBanks = (
    "SOUND_BANK_ACTION",
    "SOUND_BANK_MOVING",
    "SOUND_BANK_VOICE",
    "SOUND_BANK_GENERAL",
    "SOUND_BANK_ENV",
    "SOUND_BANK_OBJ",
    "SOUND_BANK_AIR",
    "SOUND_BANK_MENU",
    "SOUND_BANK_GENERAL2",
    "SOUND_BANK_OBJ2",
)

@dataclass
class Sfx:
    define: str
    bank: int
    id: int
    priority: int
    flags: str

def sounds_h_line_is_define(line):
    return line.startswith("#define SOUND_") and "SOUND_ARG_LOAD" in line and not line.startswith("#define SOUND_ARG_LOAD")

def get_params_from_sounds_h_define(line):
    params = line.split("(")[1].split(")")[0] # Get only stuff inside the brackets
    params = [param.strip() for param in params.split(",")] # Split by comma, strip whitespace
    params[1] = int(params[1][2:], 16)
    params[2] = int(params[2][2:], 16)
    return params

# Gets all sound effects with the given bank number and ID
def get_sfx_defines_from_id(decomp, bankNo, id):
    defines = []
    with open(os.path.join(decomp, "include", "sounds.h"), "r") as soundDefines:
        for line in soundDefines.readlines():
            if sounds_h_line_is_define(line):
                params = get_params_from_sounds_h_define(line)
                if params[1] == id and params[0] == soundBanks[bankNo]:
                    defineName = line.split(" ")[1]
                    defines.append(Sfx(defineName, bankNo, id, params[2], params[3]))
    return defines

# Deletes all sound effects with the given bank number and ID. Returns number of entries deleted.
def delete_sfx_defines_with_id(decomp, bankNo, id):
    count = 0
    with open(os.path.join(decomp, "include", "sounds.h"), "r") as soundDefines:
        lines = soundDefines.readlines()
    with open(os.path.join(decomp, "include", "sounds.h"), "w") as soundDefines:
        # Write all lines except the ones we want to delete
        for line in lines:
            if sounds_h_line_is_define(line):
                params = get_params_from_sounds_h_define(line)
                if params[1] == id and params[0] == soundBanks[bankNo]:
                    count += 1
                    continue
            soundDefines.write(line)
    return count

#delete_sfx_defines_with_id("U:/home/arthur/HackerSM64", 3, 0x40)

"""
Sound file selected:   Browse...

Loop:   Loop begin:   Loop end:


- - - - 

Name: <SOUND_GENERAL_X>  Priority: X   Set flags...
Name: <SOUND_GENERAL_X>  Priority: X   Set flags...
Add...

- - - -

Sample name:
Sound name:

- - - -

Replacing sound X in bank X... / Adding new sound to bank X
"""


def add_sfx_define_with_id(decomp, bankNo, id, sfx):
    pass

def modify_sfx_defines(newSfxs):
    # Step 1: Delete old sound defines
    # Step 2: Add new sound defines
    pass

def add_sfx_from_instrument(
    decomp, # Path to decomp folder
    replace, # Whether to replace existing sfx
    instBankNo, instNo, # Inst bank and number of sample to use
    sfxs): # List of new Sfx objects - must have same bank and ID; define, priority, and flags can differ
                                       # if replace is False, ID can be missing and will be auto-assigned
    # If replace:
    #   Add new chunk and layer
    #   Delete existing chunk recursively
    #   Delete old sound define(s)

    #   Modify channel table
    #   Add new sound define(s)

    # If not replace:
    #   Determine new free ID
    #   Add new chunk and layer

    #   Append channel table
    #   Add new sound define(s)
    pass


def add_sfx(
    decomp, # Path to decomp folder
    replace, # Whether to replace existing sfx - if yes, bank ID of sequence to replace
    inputAiff, # Path of input AIFF file
    loop, loopBegin, loopEnd, # Loop data
    sampleName, # Name of sample to use
    instBankNo, # Which instrument bank to put the sample in
    soundDefine, # Name of sound define
    soundBank, # Sound bank / channel to use
    flags):
    # Step 1: Import sample

    # Step 2: Add sample to instrument bank

    # Step 3: Add sfx
    add_sfx_from_instrument(decomp, replace, instBankNo, 0, soundBank, flags)
    pass
