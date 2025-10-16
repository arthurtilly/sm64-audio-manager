from misc import *
from dataclasses import dataclass

CHUNK_TYPE_UNKNOWN = -1
CHUNK_TYPE_SEQUENCE = 0 # The main sequence
CHUNK_TYPE_CHANNEL = 1 # Individual channels
CHUNK_TYPE_CHANNEL_TABLE = 2 # Lookup table for the channels
CHUNK_TYPE_LAYER = 3
CHUNK_TYPE_ENVELOPE = 4

ENTRY_CHUNK = "sequence_start"

referenceCommands = (
    # Command            Has params    Has return   Expected type         Target type (None for end)
    ("seq_jump",         0,        False,       CHUNK_TYPE_SEQUENCE,      CHUNK_TYPE_SEQUENCE),
    ("seq_startchannel", 1,        True,        CHUNK_TYPE_SEQUENCE,      CHUNK_TYPE_CHANNEL),

    ("chan_jump",        0,        False,       CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_CHANNEL),
    ("chan_call",        0,        True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_CHANNEL),
    ("chan_bltz",        0,        True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_CHANNEL),
    ("chan_beqz",        0,        True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_CHANNEL),
    ("chan_bgez",        0,        True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_CHANNEL),
    ("chan_setdyntable", 0,        True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_CHANNEL_TABLE),
    ("chan_setlayer",    1,        True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_LAYER),
    ("chan_setenvelope", 0,        True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_ENVELOPE),
    ("chan_end",         0,        False,       CHUNK_TYPE_CHANNEL,       None),
    ("chan_readseq",     0,        True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_LAYER), # not quite a layer but close enough
    ("chan_writeseq",    2,        True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_LAYER),

    ("sound_ref",        0,        True,        CHUNK_TYPE_CHANNEL_TABLE, CHUNK_TYPE_CHANNEL),

    ("layer_call",       0,        True,        CHUNK_TYPE_LAYER,         CHUNK_TYPE_LAYER),
    ("layer_end",        0,        False,       CHUNK_TYPE_LAYER,         None),
    ("layer_jump",       0,        False,       CHUNK_TYPE_LAYER,         CHUNK_TYPE_LAYER),

    ("envelope_goto",    1,        False,       CHUNK_TYPE_ENVELOPE,      None),
    ("envelope_hang",    0,        False,       CHUNK_TYPE_ENVELOPE,      None),
)

class ReferenceCommand:
    def __init__(self, commandID, param=None, reference=None):
        self.commandID = commandID
        self.param = param
        self.reference = reference

        # Reference will either be None (no reference), a string (unresolved reference), or a Chunk (resolved reference)
        if type(reference) == str:
            self.resolved = False
        else:
            self.resolved = True


    # Get the string representation of the command
    def get_str(self):
        params = [referenceCommands[self.commandID][0]]

        if self.param is not None:
            if type(self.param) == tuple:
                params.append(self.param[0])
            else:
                params.append(self.param)

        if self.reference is not None:
            if not self.resolved:
                params.append(self.reference + ",")
            else:
                params.append(self.reference.name + ",")

        if type(self.param) == tuple:
            params.append(self.param[1])

        return " ".join(params).strip(",")
    

    # Resolve command using chunk dictionary
    def resolve_command(self, chunkDict):
        if not self.resolved:
            if self.reference in chunkDict.dictionary:
                self.reference = chunkDict.dictionary[self.reference]
                self.resolved = True
            else:
                raise ValueError("Error: Could not find chunk " + self.reference)

class InstrCommand:
    def __init__(self, isLayer, instrument):
        self.isLayer = isLayer
        self.bank = None
        self.instrument = instrument

    def __repr__(self):
        return self.get_str()

    def get_str(self):
        if (self.isLayer):
            return "layer_setinstr %d" % self.instrument
        else:
            return "chan_setinstr %d" % self.instrument


class SequencePlayerChunk:
    def __init__(self, name, type):
        self.name = name # Label
        self.type = type # Data type
        self.children = [] # All chunks referenced by this chunk
        self.parents = [] # All chunks that reference this chunk
        self.lines = [] # Lines of commands, either strings or reference commands
        self.followingChunk = None

    def __repr__(self):
        return "Chunk " + self.name

    def add_child(self, child):
        if child is self: return
        self.children.append(child)
        child.parents.append(self)

    def get_children_recursive(self):
        children = []
        for child in self.children:
            children.append(child)
            children.extend(child.get_children_recursive())
        return children

    # Add line, return if it means the end of the chunk
    def add_line(self, line):
        # Check if line contains a reference command
        lineSplit = line.split(" ")
        for i, (cmd, params, hasReturn, expectedType, targetType) in enumerate(referenceCommands):
            if lineSplit[0] == cmd:
                self.type = expectedType
                j = 1
                param = None
                reference = None

                if params:
                    param = lineSplit[j]
                    j += 1
                if targetType is not None:
                    reference = lineSplit[j].strip(",")
                    j += 1
                if params == 2:
                    param = (param, lineSplit[j])

                ref = ReferenceCommand(i, param, reference)
                self.lines.append(ref)
                return not hasReturn
        # Check if line is an instrument command
        if lineSplit[0] == "layer_setinstr" or lineSplit[0] == "chan_setinstr":
            self.lines.append(InstrCommand(lineSplit[0] == "layer_setinstr", int(lineSplit[1], 0)))
            return False
        # If not, just add the line as a string
        self.lines.append(line)
        return False

    # Resolve references for all lines
    def resolve_references(self, chunkDict):
        for line in self.lines:
            if type(line) == ReferenceCommand:
                if not line.resolved:
                    line.resolve_command(chunkDict)
                    self.add_child(line.reference)
                if line.reference is not None and line.reference.type == CHUNK_TYPE_UNKNOWN:
                    line.reference.type = referenceCommands[line.commandID][4]

    # Resolve instrument commands
    def resolve_instruments(self, bank=None, checked=None):
        # Recursion guard
        if checked is None: checked = []
        if self in checked: return set()
        checked.append(self)

        checkedChildren = set()
        for line in self.lines:
            if type(line) == ReferenceCommand:
                # Check for any reference commands that point to layers
                if line.reference is not None and line.reference is not self and referenceCommands[line.commandID][4] == CHUNK_TYPE_LAYER:
                    line.reference.resolve_instruments(bank, checked)
                    checkedChildren.add(line.reference)
            elif type(line) == InstrCommand:
                if bank is not None:
                    line.bank = bank
            else:
                lineSplit = line.split(" ")
                # Check for bank command
                if lineSplit[0] == "chan_setbank":
                    bank = int(lineSplit[1], 0)

        # Children that do not have reference commands are fallthrough
        # so resolve at the end
        if self.type != CHUNK_TYPE_LAYER:
            return
        for child in self.children:
            if child not in checkedChildren:
                child.resolve_instruments(bank, checked)
        
    def get_instrument_commands(self, checked=None):
        # Recursion guard
        if checked is None: checked = []
        if self in checked: return set()
        checked.append(self)

        commands = set()
        if self.type != CHUNK_TYPE_CHANNEL and self.type != CHUNK_TYPE_LAYER:
            return commands
        for line in self.lines:
            if type(line) == InstrCommand:
                commands.add(line)
        for child in self.children:
            commands.update(child.get_instrument_commands(checked))
        return list(commands)
        
    def get_instrument_references(self):
        return [(instCommand.bank, instCommand.instrument) for instCommand in self.get_instrument_commands()]

@dataclass
class ChannelEntry:
    table: SequencePlayerChunk    # Table chunk
    banks: list                   # List of sound banks that use this channel


class ChunkDictionary:
    def __init__(self, decomp):
        self.dictionary = {}
        self.path = os.path.join(decomp, "sound", "sequences", "00_sound_player.s")
        self.parse_sequence_player()
        self.build_bank_table()


    # Load the chunk dictionary from seq00
    def parse_sequence_player(self):
        # Step 1: Parse file into chunks
        with open(self.path, "r") as f:
            line = None
            while line != ("%s:\n" % ENTRY_CHUNK):
                line = f.readline()

            currentChunk = SequencePlayerChunk(ENTRY_CHUNK, CHUNK_TYPE_SEQUENCE)
            self.dictionary[ENTRY_CHUNK] = currentChunk
            chunkHasEnded = False

            inIfdef = False
            waitingForIfdef = False

            while True:
                line = f.readline()
                if not line: break
                line = line.strip()
                if len(line) == 0: continue

                # Check if line is a label
                if line[0] == ".":
                    if not line.split(" ")[0] in (".set", ".align", ".byte"):
                        chunkName = line.split(":")[0]
                        newChunk = SequencePlayerChunk(chunkName, CHUNK_TYPE_UNKNOWN)
                        self.dictionary[chunkName] = newChunk

                        if not chunkHasEnded and currentChunk.type != CHUNK_TYPE_CHANNEL_TABLE:
                            # Old chunk can carry over into this chunk
                            currentChunk.add_child(newChunk)
                            currentChunk.followingChunk = newChunk

                        chunkHasEnded = False
                        currentChunk = newChunk
                        inIfdef = False
                        waitingForIfdef = False
                        continue

                if not chunkHasEnded:
                    if line.startswith("#if"):
                        inIfdef = True
                    elif line.startswith("#endif"):
                        inIfdef = False
                        if waitingForIfdef:
                            # Chunk had ended and was waiting for #ifdef to be closed
                            chunkHasEnded = True
                    if currentChunk.add_line(line):
                        # End command found
                        if inIfdef:
                            # Currently waiting on #ifdef to be resolved
                            # Terminate chunk when resolved
                            waitingForIfdef = True
                        else:
                            chunkHasEnded = True

        # Step 2: Iterate over all chunks and resolve references
        for chunk in self.dictionary.values():
            chunk.resolve_references(self)
        for chunk in self.dictionary.values():
            chunk.resolve_instruments()


    # Copy an individual chunk to the file
    def write_chunk_to_file(self, chunk, f):
        f.write("\n" + chunk.name + ":\n")
        for line in chunk.lines:
            if type(line) == ReferenceCommand or type(line) == InstrCommand:
                f.write(line.get_str() + "\n")
            else:
                f.write(line + "\n")


    # Reconstruct a full seq00 file from the chunk dictionary
    def reconstruct_sequence_player(self):
        with open(self.path, "w") as f:
            f.write(
'#include "seq_macros.inc"\n\
\n\
.section .rodata\n\
.align 0\n')
            copiedDict = self.dictionary.copy()
            currentChunk = copiedDict[ENTRY_CHUNK]
            while True:
                self.write_chunk_to_file(currentChunk, f)
                del copiedDict[currentChunk.name]
                if currentChunk.followingChunk is not None:
                    currentChunk = currentChunk.followingChunk
                else:
                    if len(copiedDict) == 0: break
                    currentChunk = next(iter(copiedDict.values()))


    # Recursively delete a chunk and any children that have no other parents
    def delete_chunk(self, chunk):
        assert len(chunk.parents) == 0
        for child in chunk.children:
            child.parents.remove(chunk)
            if len(child.parents) == 0:
                self.delete_chunk(child)
        del self.dictionary[chunk.name]


    # Trim all unreferenced chunks
    def trim_chunks(self):
        # Iterate over chunks and find any with no parents
        for chunk in tuple(self.dictionary.values()):
            if len(chunk.parents) == 0 and chunk.name in self.dictionary:
                if chunk.name == ENTRY_CHUNK: continue
                self.delete_chunk(chunk)
    

    def build_bank_table(self):
        self.bankTable = []
        mainChunk = self.dictionary[ENTRY_CHUNK]
        for line in mainChunk.lines:
            if line_is_command(line, "seq_startchannel"):
                # Find channel table
                for chnlLine in line.reference.lines:
                    if line_is_command(chnlLine, "chan_setdyntable"):
                        tableChunk = chnlLine.reference
                        break
                else:
                    raise AudioManagerException("Error: Could not find channel table for channel %s" % line.reference.name)

                # Check if table chunk is already in the bank table
                for entry in self.bankTable:
                    if entry.table is tableChunk:
                        entry.banks.append(len(self.bankTable))
                        self.bankTable.append(entry)
                        break
                else:
                    self.bankTable.append(ChannelEntry(tableChunk, [len(self.bankTable)]))


    # Get the reference to a specific sound in a channel table from its ID
    def get_sound_ref_from_channel(self, tableChunk, soundID, replaceChunk=None):
        i = 0
        for line in tableChunk.lines:
            if line_is_command(line, "sound_ref"):
                if i == soundID:
                    oldChunk = line.reference
                    if replaceChunk is not None:
                        line.reference = replaceChunk
                    return oldChunk
                i += 1


    # Get all sound references in a channel table
    def get_all_sound_refs_from_channel(self, tableChunk):
        soundRefs = []
        for line in tableChunk.lines:
            if line_is_command(line, "sound_ref"):
                soundRefs.append(line.reference)
        return soundRefs


    # Replace an existing sound reference with a new chunk
    def replace_sound_ref(self, channelID, soundID, newChunk):
        tableChunk = self.bankTable[channelID].table
        oldChunk = self.get_sound_ref_from_channel(tableChunk, soundID, replaceChunk=newChunk)

        oldChunk.parents.remove(tableChunk)
        tableChunk.children.remove(oldChunk)

        tableChunk.add_child(newChunk)
        self.dictionary[newChunk.name] = newChunk

        # If chunk has no references left, delete it
        if len(oldChunk.parents) == 0:
            self.delete_chunk(oldChunk)


    # Red coin and secret miniseqs have hardcoded IDs to determine the pitch to play at
    def shift_hardcoded_ids_of_chunk(self, chunk, shift):
        # Scan the chunk until a chan_subtract is found
        for i, line in enumerate(chunk.lines):
            if type(line) == str and line.startswith("chan_subtract"):
                # Get the subtracted value
                subtractedValue = int(line.split(" ")[1].strip(), 0)
                chunk.lines[i] = f"chan_subtract 0x{subtractedValue + shift:02X}"

    def fix_hardcoded_ids(self, tableChunk, soundID, shift):
        i = 0
        redcoins = False
        secrets = False
        for line in tableChunk.lines:
            if line_is_command(line, "sound_ref"):
                i += 1
                if i > soundID:
                    if not redcoins and line.reference.name == ".sound_menu_collect_red_coin":
                        redcoins = True
                        self.shift_hardcoded_ids_of_chunk(line.reference, shift)
                    elif not secrets and line.reference.name == ".sound_menu_collect_secret":
                        secrets = True
                        self.shift_hardcoded_ids_of_chunk(line.reference, shift)

    # Delete a sound reference from a channel table
    def delete_sound_ref(self, channelID, soundID):
        tableChunk = self.bankTable[channelID].table
        oldChunk = self.get_sound_ref_from_channel(tableChunk, soundID)

        oldChunk.parents.remove(tableChunk)
        tableChunk.children.remove(oldChunk)

        # Delete line of channel table that contained the sound reference
        i = 0
        for line in tableChunk.lines:
            if line_is_command(line, "sound_ref"):
                if i == soundID:
                    tableChunk.lines.remove(line)
                i += 1

        self.fix_hardcoded_ids(tableChunk, soundID, -1)
        # If chunk has no references left, delete it
        if len(oldChunk.parents) == 0:
            self.delete_chunk(oldChunk)

    def insert_sound_ref(self, channelID, soundID, chunkName):
        tableChunk = self.bankTable[channelID].table

        newChunk = SequencePlayerChunk(chunkName, CHUNK_TYPE_CHANNEL)
        newChunk.add_line("chan_end")
        self.dictionary[chunkName] = newChunk

        # Insert new sound_ref line into channel table
        newLine = ReferenceCommand(get_command_id("sound_ref"), None, newChunk)
        tableChunk.lines.insert(soundID, newLine)

        self.fix_hardcoded_ids(tableChunk, soundID, 1)
        return newChunk

    def change_sound_name(self, oldName, newName):
        if newName in self.dictionary:
            raise AudioManagerException(f"Sound with the name '{newName}' already exists!")
        selectedChunk = self.dictionary[oldName]
        selectedChunk.name = newName

        keyOrder = list(self.dictionary.keys())
        del self.dictionary[oldName]
        self.dictionary[newName] = selectedChunk
        keyOrder[keyOrder.index(oldName)] = newName
        self.dictionary = {key: self.dictionary[key] for key in keyOrder}

    # Shift all instruments with an ID greater than inst
    def update_instruments(self, bank, inst, shift):
        for _, chunk in self.dictionary.items():
            if chunk.type != CHUNK_TYPE_CHANNEL and chunk.type != CHUNK_TYPE_LAYER:
                continue
            for line in chunk.lines:
                if type(line) == InstrCommand:
                    if line.bank == bank and line.instrument >= inst:
                        line.instrument += shift

    def delete_instrument(self, bank, inst):
        self.update_instruments(bank, inst, -1)

    def insert_instrument(self, bank, newInst):
        self.update_instruments(bank, newInst, 1)

def line_is_command(line, cmd):
    return type(line) == ReferenceCommand and referenceCommands[line.commandID][0] == cmd

def get_command_id(cmd):
    for i in range(len(referenceCommands)):
        if referenceCommands[i][0] == cmd:
            return i
    return None


# chunkDict = ChunkDictionary("U:/home/arthur/HackerSM64")
# sound = ".sound_menu_coin_its_a_me_mario"

# print(chunkDict.dictionary[sound].get_instrument_references())