from misc import *
from seq00 import *
from dataclasses import dataclass

soundBanks = None

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

def init_sound_banks(decomp):
    global soundBanks
    soundBanks = [bank for bank, _ in load_table(os.path.join(decomp, "include", "sounds.h"), "enum SoundBank")]

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
    global soundBanks
    val = (sfx.bank << 28) | (sfx.id << 16) | (sfx.priority << 8) | evaluate_sound_flags(sfx.flags)
    return f"#define {sfx.define:<40} /* 0x{val:08X} */ SOUND_ARG_LOAD({soundBanks[sfx.bank]+',':<20} 0x{sfx.id:02X}, 0x{sfx.priority:02X}, {sfx.flags})"

# Get full list of defines
def get_all_sfx_defines(lines):
    global soundBanks
    for line in lines:
        if sounds_h_line_is_define(line):
            params = get_params_from_sounds_h_define(line)
            yield Sfx(line.split(" ")[1], soundBanks.index(params[0]), params[1], params[2], params[3])

# Get just the names of defines
def get_all_sfx_define_names(lines):
    for sfx in get_all_sfx_defines(lines):
        yield sfx.define

# Gets all sound effects with the given bank number and ID
def get_sfx_defines_from_id(lines, bankNo, id):
    global soundBanks
    for sfx in get_all_sfx_defines(lines):
        if sfx.bank == bankNo and sfx.id == id:
            yield sfx


# Deletes all sound effects with the given bank number and ID. Returns number of entries deleted.
def delete_sfx_defines_with_id(lines, bankNo, id):
    global soundBanks
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
    global soundBanks
    # Find nearest define
    # Line number, (Bank * 1000 + ID)
    nearestDefinePrev = [None, -999999999]
    nearestDefineNext = [None, 999999999]

    targetVal = sfx.bank * 1000 + sfx.id

    # This algorithm is not the best
    for i, line in enumerate(lines):
        if sounds_h_line_is_define(line):
            params = get_params_from_sounds_h_define(line)
            curVal = soundBanks.index(params[0]) * 1000 + params[1]

            if curVal <= targetVal and curVal >= nearestDefinePrev[1]:
                nearestDefinePrev = [i, curVal]
            elif curVal > targetVal and curVal < nearestDefineNext[1]:
                nearestDefineNext = [i, curVal]

    # Find which line to insert the new define at by which one is closer
    lineNo = None
    prevDist = targetVal - nearestDefinePrev[1]
    nextDist = nearestDefineNext[1] - targetVal

    if prevDist < nextDist or nearestDefineNext[0] is None:
        lineNo = nearestDefinePrev[0] + 1
    elif nearestDefineNext[0] is not None:
        lineNo = nearestDefineNext[0]

    # Insert define
    lines.insert(lineNo, get_define_string(sfx))

def shift_sfx_ids(lines, banks, id, shift):
    global soundBanks
    for i, line in enumerate(lines):
        if sounds_h_line_is_define(line):
            params = get_params_from_sounds_h_define(line)
            if params[1] >= id:
                for bank in banks:
                    if params[0] == soundBanks[bank]:
                        defineName = line.split(" ")[1]
                        lines[i] = get_define_string(Sfx(defineName, bank, params[1] + shift, params[2], params[3]))
                        break

# Deletes defines in given banks with ID, and moves the ID of define after it down by one
def fully_delete_sfx_define(lines, banks, id):
    for bank in banks:
        delete_sfx_defines_with_id(lines, bank, id)
    shift_sfx_ids(lines, banks, id, -1)

# Deletes sound effects and re-adds the ones in the given list
def modify_sfx_defines(decomp, banks, id, newSfxs):
    sounds_h = read_sfx_file(decomp)
    for bank in banks:
        delete_sfx_defines_with_id(sounds_h, bank, id)

    existingDefines = get_all_sfx_define_names(sounds_h)
    for sfx in newSfxs:
        if sfx.define in existingDefines:
            raise AudioManagerException(f"Define name '{sfx.define}' already in use!")
        add_sfx_define(sounds_h, sfx)

    write_sfx_file(decomp, sounds_h)

# Delete specific sound effect using ID
# Also deletes and shifts sfx defines
def delete_sfx(decomp, chunkDict, banks, id):
    sounds_h = read_sfx_file(decomp)

    fully_delete_sfx_define(sounds_h, banks, id)
    chunkDict.delete_sound_ref(banks[0], id)

    write_sfx_file(decomp, sounds_h)

# Insert a new empty sound effect
# Does not create new defines, but shifts existing ones forward
def insert_sfx(decomp, chunkDict, banks, id, name):
    sounds_h = read_sfx_file(decomp)
    shift_sfx_ids(sounds_h, banks, id, 1)
    newChunk = chunkDict.insert_sound_ref(banks[0], id, name)

    write_sfx_file(decomp, sounds_h)
    return newChunk
