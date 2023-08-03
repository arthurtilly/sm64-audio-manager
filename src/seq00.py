from misc import *

CHUNK_TYPE_UNKNOWN = -1
CHUNK_TYPE_SEQUENCE = 0 # The main sequence
CHUNK_TYPE_CHANNEL = 1 # Individual channels
CHUNK_TYPE_CHANNEL_TABLE = 2 # Lookup table for the channels
CHUNK_TYPE_LAYER = 3
CHUNK_TYPE_ENVELOPE = 4

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

    ("envelope_goto",    1,         False,       CHUNK_TYPE_ENVELOPE,      None),
    ("envelope_hang",    0,        False,       CHUNK_TYPE_ENVELOPE,      None),
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
        self.followingChunk = None

    def __repr__(self):
        return "Chunk " + self.name

    def add_child(self, child):
        if child is self: return
        if child in self.children: return
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
    # Step 1: Parse file into chunks
    with open(path, "r") as f:
        line = None
        while line != "sequence_start:\n":
            line = f.readline()

        currentChunk = SequencePlayerChunk("sequence_start", CHUNK_TYPE_SEQUENCE)
        chunkDictionary["sequence_start"] = currentChunk
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
                    chunkDictionary[chunkName] = newChunk

                    if not chunkHasEnded:
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
    for chunk in chunkDictionary.values():
        chunk.resolve_references()

def write_chunk_to_file(chunk, f):
    f.write("\n" + chunk.name + ":\n")
    for line in chunk.lines:
        if type(line) == ReferenceCommand:
            f.write(line.get_str() + "\n")
        else:
            f.write(line + "\n")

def reconstruct_sequence_player(output):
    with open(output, "w") as f:
        f.write(
'#include "seq_macros.inc"\n\
\n\
.section .rodata\n\
.align 0\n')
        currentChunk = chunkDictionary["sequence_start"]
        while True:
            write_chunk_to_file(currentChunk, f)
            del chunkDictionary[currentChunk.name]
            if currentChunk.followingChunk is not None:
                currentChunk = currentChunk.followingChunk
            else:
                if len(chunkDictionary) == 0: break
                currentChunk = next(iter(chunkDictionary.values()))


def delete_chunk(chunk):
    assert len(chunk.parents) == 0
    for child in chunk.children:
        child.parents.remove(chunk)
        if len(child.parents) == 0:
            delete_chunk(child)
    del chunkDictionary[chunk.name]
    print("Deleted chunk " + chunk.name)


def trim_chunks():
    # Iterate over chunks and find any with no parents
    for chunk in tuple(chunkDictionary.values()):
        if len(chunk.parents) == 0 and chunk.name in chunkDictionary:
            if chunk.name == "sequence_start": continue
            delete_chunk(chunk)
