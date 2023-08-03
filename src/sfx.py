from misc import *

CHUNK_TYPE_UNKNOWN = -1
CHUNK_TYPE_SEQUENCE = 0 # The main sequence
CHUNK_TYPE_CHANNEL = 1 # Individual channels
CHUNK_TYPE_CHANNEL_TABLE = 2 # Lookup table for the channels
CHUNK_TYPE_LAYER = 3
CHUNK_TYPE_ENVELOPE = 4

referenceCommands = (
    # Command            Has params    Has return   Expected type         Target type (None for end)
    ("seq_jump",         False,        False,       CHUNK_TYPE_SEQUENCE,      CHUNK_TYPE_SEQUENCE),
    ("seq_startchannel", True,         True,        CHUNK_TYPE_SEQUENCE,      CHUNK_TYPE_CHANNEL),

    ("chan_jump",        False,        False,       CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_CHANNEL),
    ("chan_bltz",        False,        True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_CHANNEL),
    ("chan_beqz",        False,        True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_CHANNEL),
    ("chan_bgez",        False,        True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_CHANNEL),
    ("chan_setdyntable", False,        True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_CHANNEL_TABLE),
    ("chan_setlayer",    True,         True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_LAYER),
    ("chan_setenvelope", False,        True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_ENVELOPE),
    ("chan_end",         False,        False,       CHUNK_TYPE_CHANNEL,       None),
    ("chan_readseq",     False,        True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_LAYER), # not quite a layer but close enough
    ("chan_writeseq",    True,         True,        CHUNK_TYPE_CHANNEL,       CHUNK_TYPE_LAYER), # figure out extra param

    ("sound_ref",        False,        True,        CHUNK_TYPE_CHANNEL_TABLE, CHUNK_TYPE_CHANNEL),

    ("layer_call",       False,        True,        CHUNK_TYPE_LAYER,         CHUNK_TYPE_LAYER),
    ("layer_end",        False,        False,       CHUNK_TYPE_LAYER,         None),

    ("envelope_goto",    True,         False,       CHUNK_TYPE_ENVELOPE,      None),
    ("envelope_hang",    False,        False,       CHUNK_TYPE_ENVELOPE,      None),
)

chunkDictionary = {}

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
        stringRep = referenceCommands[self.commandID][0]

        if self.param is not None:
            stringRep += " " + self.param

        if self.reference is not None:
            if not self.resolved:
                stringRep += " " + self.reference
            else:
                stringRep += " " + self.reference.name

        return stringRep
    

    # Resolve command using chunk dictionary
    def resolve_command(self):
        if not self.resolved:
            if self.reference in chunkDictionary:
                self.reference = chunkDictionary[self.reference]
                self.resolved = True
            else:
                raise ValueError("Error: Could not find chunk " + self.reference)


class SequencePlayerChunk:
    def __init__(self, name, type):
        self.name = name # Label
        self.type = type # Data type
        self.children = [] # All chunks referenced by this chunk
        self.parents = [] # All chunks that reference this chunk
        self.lines = [] # Lines of commands, either strings or reference commands

    def __repr__(self):
        return "Chunk " + self.name

    def add_child(self, child):
        if child is self: return
        self.children.append(child)
        child.parents.append(self)

    # Add line, return if it means the end of the chunk
    def add_line(self, line):
        # Check if line contains a reference command
        lineSplit = line.split(" ")
        for i, (cmd, params, hasReturn, expectedType, targetType) in enumerate(referenceCommands):
            if lineSplit[0] == cmd:
                j = 1
                param = None
                reference = None

                if params:
                    param = lineSplit[j]
                    j += 1
                if targetType is not None:
                    reference = lineSplit[j]

                ref = ReferenceCommand(i, param, reference)
                self.lines.append(ref)
                return not hasReturn

        # If not, just add the line as a string
        self.lines.append(line)
        return False

    # Resolve references for all lines
    def resolve_references(self):
        for line in self.lines:
            if type(line) == ReferenceCommand and not line.resolved:
                line.resolve_command()
                self.add_child(line.reference)



def parse_sequence_player(path):
    # Open file
    with open(path, "r") as f:
        line = None
        while line != "sequence_start:\n":
            line = f.readline()

        currentChunk = SequencePlayerChunk("sequence_start", CHUNK_TYPE_SEQUENCE)
        chunkDictionary["sequence_start"] = currentChunk
        chunkHasEnded = False
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
                    chunkDictionary[chunkName] = newChunk

                    if not chunkHasEnded:
                        # Old chunk can carry over into this chunk
                        currentChunk.add_child(newChunk)

                    chunkHasEnded = False
                    currentChunk = newChunk

            if not chunkHasEnded:
                if currentChunk.add_line(line):
                    # Chunk has ended
                    chunkHasEnded = True

    print(chunkDictionary)
    for chunk in chunkDictionary.values():
        chunk.resolve_references()

                    

parse_sequence_player("U:/home/arthur/HackerSM64/sound/sequences/00_sound_player.s")
print(chunkDictionary["sequence_start"].children)