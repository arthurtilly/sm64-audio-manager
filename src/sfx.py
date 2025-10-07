from misc import *
from seq00 import *
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

soundFlags = (
    (0x1000000, "SOUND_NO_VOLUME_LOSS"),
    (0x2000000, "SOUND_VIBRATO"),
    (0x4000000, "SOUND_NO_PRIORITY_LOSS"),
    (0x8000000, "SOUND_CONSTANT_FREQUENCY"),
    (0x10, "SOUND_LOWER_BACKGROUND_MUSIC"),
    (0x20, "SOUND_NO_ECHO"),
    (0x80, "SOUND_DISCRETE"),
)

@dataclass
class Sfx:
    define: str
    bank: int
    id: int
    priority: int
    flags: str


# Read sounds.h file into a list of lines
def read_sfx_file(decomp):
    with open(os.path.join(decomp, "include", "sounds.h"), "r") as soundDefines:
        return [line.rstrip() for line in soundDefines.readlines()]


# Write lines back to sounds.h
def write_sfx_file(decomp, lines):
    with open(os.path.join(decomp, "include", "sounds.h"), "w") as soundDefines:
        soundDefines.write("\n".join(lines) + "\n")


# Check if a given line in the file is a sound define
def sounds_h_line_is_define(line):
    return line.startswith("#define SOUND_") and "SOUND_ARG_LOAD" in line and not line.startswith("#define SOUND_ARG_LOAD")


# Split a sound define into its parameters
def get_params_from_sounds_h_define(line):
    params = line.split("(")[1].split(")")[0] # Get only stuff inside the brackets
    params = [param.strip() for param in params.split(",")] # Split by comma, strip whitespace
    params[1] = int(params[1], 0)
    params[2] = int(params[2], 0)
    return params


# Get the integer value of the sound flags
def evaluate_sound_flags(flags):
    if flags == "0": return 0
    val = 1
    for flag in flags.split("|"):
        for soundFlag in soundFlags:
            if soundFlag[1] == flag.strip():
                val |= soundFlag[0]
                break
        else:
            try:
                val |= int(flag, 0)
            except ValueError:
                continue
    return val


# Turn a Sfx object into a sound define string
def get_define_string(sfx):
    val = (sfx.bank << 28) | (sfx.id << 16) | (sfx.priority << 8) | evaluate_sound_flags(sfx.flags)
    return f"#define {sfx.define:<40} /* 0x{val:08X} */ SOUND_ARG_LOAD({soundBanks[sfx.bank]+',':<20} 0x{sfx.id:02X}, 0x{sfx.priority:02X}, {sfx.flags})"


# Gets all sound effects with the given bank number and ID
def get_sfx_defines_from_id(lines, bankNo, id):
    defines = []

    for line in lines:
        if sounds_h_line_is_define(line):
            params = get_params_from_sounds_h_define(line)
            if params[1] == id and params[0] == soundBanks[bankNo]:
                defineName = line.split(" ")[1]
                defines.append(Sfx(defineName, bankNo, id, params[2], params[3]))

    return defines


# Deletes all sound effects with the given bank number and ID. Returns number of entries deleted.
def delete_sfx_defines_with_id(lines, bankNo, id):
    count = 0
    for line in reversed(lines):
        if sounds_h_line_is_define(line):
            params = get_params_from_sounds_h_define(line)
            if params[1] == id and params[0] == soundBanks[bankNo]:
                count += 1
                lines.remove(line)
                continue

    return count


# Adds a new sound define and attempts to find the most appropriate place to put it
def add_sfx_define(lines, sfx):
    # Find nearest define in the same bank
    # Line number, ID
    nearestDefinePrev = [None, -1]
    nearestDefineNext = [None, 256]

    # This algorithm is not the best
    for i, line in enumerate(lines):
        if sounds_h_line_is_define(line):
            params = get_params_from_sounds_h_define(line)
            if params[0] == soundBanks[sfx.bank]:
                if params[1] <= sfx.id and params[1] >= nearestDefinePrev[1]:
                    nearestDefinePrev = [i, params[1]]
                elif params[1] > sfx.id and params[1] < nearestDefineNext[1]:
                    nearestDefineNext = [i, params[1]]
    
    # Find which line to insert the new define at by which one is closer
    lineNo = None
    prevDist = sfx.id - nearestDefinePrev[1]
    nextDist = nearestDefineNext[1] - sfx.id

    if prevDist < nextDist and nearestDefinePrev[0] != None:
        lineNo = nearestDefinePrev[0] + 1
    elif nearestDefineNext[0] != None:
        lineNo = nearestDefineNext[0]

    if lineNo is None:
        raise AudioManagerException(f"Error: No defines found in bank {sfx.bank:d}")


    # Insert define
    
    lines.insert(lineNo, get_define_string(sfx))


# Deletes defines in given banks with ID, and moves the ID of define after it down by one
def fully_delete_sfx_define(lines, banks, id):
    for bank in banks:
        delete_sfx_defines_with_id(lines, bank, id)

    for i, line in enumerate(lines):
        if sounds_h_line_is_define(line):
            params = get_params_from_sounds_h_define(line)
            if params[1] > id:
                for bank in banks:
                    if params[0] == soundBanks[bank]:
                        defineName = line.split(" ")[1]
                        lines[i] = get_define_string(Sfx(defineName, bank, params[1] - 1, params[2], params[3]))
                        break

# Deletes sound effects and re-adds the ones in the given list
def modify_sfx_defines(decomp, banks, id, newSfxs):
    sounds_h = read_sfx_file(decomp)
    for bank in banks:
        delete_sfx_defines_with_id(sounds_h, bank, id)

    for sfx in newSfxs:
        add_sfx_define(sounds_h, sfx)

    write_sfx_file(decomp, sounds_h)


def delete_sfx(decomp, chunkDict, bankNo, id):
    sounds_h = read_sfx_file(decomp)
    banks = chunkDict.bankTable[bankNo].banks

    fully_delete_sfx_define(sounds_h, banks, id)
    chunkDict.delete_sound_ref(bankNo, id)

    write_sfx_file(decomp, sounds_h)


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
