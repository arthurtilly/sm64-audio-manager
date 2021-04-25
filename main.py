import os, json, math, struct, aifc, chunk, re
import readline

# SM64 Audio Manager v0.1
# Made by Arthurtilly

# Allow tab autocompletion for inputs
readline.set_completer_delims(' \t\n=')
readline.parse_and_bind("tab: complete")

def explicit_exit(s = ''):
    if s:
        print(s)
    print('Exiting...')
    exit(0)

def prompt_yn(s):
    while True:
        res = input(f"{s}\n(y/n): ")
        if (res.upper() in ["Y", "N"]):
            return res.upper() == "Y"

def prompt_list(s, opts):
    ops_fmt = '\n'.join([f"{i}: {o}" for i, o in enumerate(opts)])
    question = f"{s}\n{opts_fmt}\nEnter option number: "
    while True:
        res = input(question)
        try:
            opt_num = int(res)
            if opt_num >= len(opts):
                print(f"{opt_num} is not a valid option, num must be less than {len(opts)}")
                if prompt_yn("Try again?"):
                    continue
                else:
                    return None
            else:
                return opts[opt_num]
        except:
            if prompt_yn('Invalid input. Try again?'):
                continue
            else:
                return None

def prompt_int_range(s, low, high):
    question = f"{s}\nEnter number between {low} and {high}: "
    while True:
        try:
            opt_num = int(input(question))
            if opt_num < low or opt_num > high:
                print(f"{opt_num} is not a valid option, num must be >= {low} and <= {high}")
                if prompt_yn("Try again?"):
                    continue
                else:
                    return None
            else:
                return opt_num
        except:
            if prompt_yn('Invalid input. Try again?'):
                continue
            else:
                return None
            

"""
Check if the streamed audio bank has been created, and create it if not.
"""
def check_if_bank_exists(decompFolder):
    if not os.path.exists(os.path.join(decompFolder, "sound/sound_banks/streamed_audio.json")):
        print("")
        print("This is the first time you have opened this decomp.\nInitializing streamed audio sound bank...")
        create_streamed_audio_bank(decompFolder)


"""
Set up the streamed audio sound bank for the first time.
"""
def create_streamed_audio_bank(decompFolder):
    # Create json file for streamed audio sound bank
    jsonBankData = {
        "date": "1996-03-19",
        "sample_bank": "streamed_audio",
        "envelopes": {
            "envelope": [
                [6, 32700],
                [6, 32700],
                [32700, 29430],
                "hang"
            ]            
        },
        "instruments": {},
        "instrument_list": []
    }
    
    j = open(os.path.join(decompFolder, "sound/sound_banks/streamed_audio.json"), "w")
    json.dump(jsonBankData, j, indent=4)
    j.close()
    print("ADDED: Created soundbank file 'sound/sound_banks/streamed_audio.json'")
    
    # Create directory for streamed audio samples
    try:
        os.mkdir(os.path.join(decompFolder, "sound/samples/streamed_audio"))
        print("ADDED: Created sample directory 'sound/samples/streamed_audio'")
    except FileExistsError:
        pass
    
    print("Finished initalizing streamed audio bank.")
    print("")


"""
Add a new instrument to the streamed audio sound bank.
"""
def add_streamed_audio_inst(soundName, decompFolder, replace):
    jsonPath = os.path.join(decompFolder, "sound/sound_banks/streamed_audio.json")
    
    j = open(jsonPath, "r")
    jsonBankData = json.load(j)
    j.close()
    
    # Get number of existing instruments
    instNo = len(jsonBankData["instruments"])

    # Check for duplicate
    found_replacement = False
    for i, inst in enumerate(jsonBankData["instruments"].values()):
        if inst["sound"] == soundName:
            if replace: # Sound is being replaced
                instNo = i
                found_replacement = True
                print(f"Replacing inst{instNo}")
                break
            else: # Sound was not intended to be a replacement
                print(f'Error: {soundName} already exists in sound/sound_banks/streamed_audio.json')
                if not prompt_yn('Continue?'):
                    explicit_exit()

    # Exit if sound should be replaced and wasn't found
    if replace and not found_replacement:
        raise ValueError(f'Error: could not find {soundName} in sound/sound_banks/streamed_audio.json')
    
    # Add new instrument
    jsonBankData["instruments"]["inst%d" % instNo] = {
        "release_rate": 10,
        "envelope": "envelope",
        "sound": "%s" % soundName
    }
    
    # If replacing, we're only here for the instNo
    if not replace:
        jsonBankData["instrument_list"].append("inst%d" % instNo)
    
        j = open(jsonPath, "w")
        json.dump(jsonBankData, j, indent=4)
        j.close()
    
        print("CHANGED: Modified 'sound/sound_banks/streamed_audio.json'")
    
    return instNo


"""
Create a new m64 file for the streamed audio.
"""
def create_m64(m64Name, instNo, volume, decompFolder): 
    volume = struct.pack(">B", volume)
    instNo = struct.pack(">B", instNo)

    m64Bytes = b"\
\xD3\x00\
\xD7\x00\x01\
\xDB%b\
\x90\x00\x16\
\xDD\x01\
\xFD\xFF\xFF\
\xFB\x00\x07\
\xD6\x00\x01\
\xFF\
\xC4\
\x90\x00\x20\
\xC1%b\
\xFD\xFF\xFF\
\xFF\
\xC2\x00\
\x67\xFF\xFF\x7F\
\xFF" % (volume, instNo)
    
    m64 = open(os.path.join(decompFolder, "sound/sequences/us/%s.m64" % m64Name), "wb")
    m64.write(m64Bytes)
    m64.close()
    
    print("ADDED: Created sequence file 'sound/sequences/us/%s.m64'" % m64Name)


"""
Add a new sequence to the sequences json.
"""
def create_new_sequence(seqName, decompFolder):
    jsonPath = os.path.join(decompFolder, "sound/sequences.json")
    
    j = open(jsonPath, "r")
    jsonSeqData = json.load(j)
    j.close()
    
    # m64s must be numbered correctly here otherwise compilation will fail
    m64Num = hex(len(jsonSeqData) - 1)[2:].upper()

    # Add "custom" so git will pick it up
    m64Name = "%s_custom_%s" % (m64Num, seqName)

    # check if name exists
    noNumName = f"_custom_{seqName}"
    replace = False

    dups = [n for n in jsonSeqData.keys() if noNumName in n]
    if len(dups):
        replace = True
        # there was one duplicate name
        if len(dups) == 1:
            if prompt_yn(f'Replace {dups[0]}?'):
                m64Name = dups[0]
                replace = True
            else:
                print('Creating new sequence')
        # there was a few duplicate names
        else:
            name = prompt_list(dups)
            if name is not None:
                replace = True
                m64Name = name
            else:
                print('Creating new sequence')

    jsonSeqData[m64Name] = ["streamed_audio"]

    if not replace:
        j = open(jsonPath, "w")
        json.dump(jsonSeqData, j, indent=4)
        j.close()
        
        print("CHANGED: Modified 'sound/sequences.json'")
    
    return m64Name, replace


"""
Add loop points to an aiff file.
"""
def add_loop_to_aiff(aiffPath, loopStart, loopEnd):
    # Defines the looping
    instChunk = b"\
INST\
\x00\x00\x00\x14\
\x3C\x00\x00\x7F\x00\x7F\x00\x00\
\x00\x01\x00\x01\x00\x02\
\x00\x00\x00\x00\x00\x00\
"
    # Defines the loop points
    markChunk = b"\
MARK\
\x00\x00\x00\x22\x00\x02\
\x00\x01%b\x08beg loop\x00\
\x00\x02%b\x08end loop\x00\
" % (loopStart, loopEnd)
    
    f = open(aiffPath, "ab+")
    f.write(instChunk)
    f.write(markChunk)
    f.close()    

def get_loop_point(string, length, framerate, default):
    while True:
        ans = input(string)
        if ans == "":
            return default
        
        try:
            ans = float(ans) * framerate
        except ValueError:
            print("Invalid input. Please enter a float.")
            continue
        
        if ans > length or ans < -length:
            print("Input out of range.")
            continue
        
        if ans < 0:
            ans += length
        return ans
    
"""
Copy over the aiff data from the source file and add loop points.
"""
def copy_aiff_data(aiffPath, m64Name, decompFolder):
    newPath = os.path.join(decompFolder, "sound/samples/streamed_audio/%s.aiff" % m64Name)

    aRead = aifc.open(aiffPath, "r")
    aWrite = aifc.open(newPath, "w")
    
    frames = aRead.getnframes()
    framerate = aRead.getframerate()
    
    # Copy data
    aWrite.setnchannels(1)
    aWrite.setsampwidth(aRead.getsampwidth())
    aWrite.setframerate(framerate)
    aWrite.writeframes(aRead.readframes(frames))
    aWrite.close()
    
    
    seconds = frames / framerate
    if prompt_yn("Would you like to specify custom loop points?"):
        print("\nEnter a number of seconds between 0 and %.3f.\nYou can use a negative number to offset backwards from the beginning,\nor leave it blank to use the default." % seconds)
        loopStart = int(get_loop_point("Enter timestamp for start of loop (default 0.000): ", frames, framerate, 0))
        loopEnd = int(get_loop_point("Enter timestamp for end of loop (default %.3f): " % seconds, frames, framerate, frames))
    else:
        loopStart = 0
        loopEnd = frames
    print("Looping from frame %d (%.3fs) to frame %d (%.3fs)...\n" % (loopStart, loopStart/framerate, loopEnd, loopEnd/framerate))
    # Add loop points (beginning and end)
    loopStart = struct.pack(">L", loopStart)
    loopEnd = struct.pack(">L", loopEnd)
    add_loop_to_aiff(newPath, loopStart, loopEnd)
    
    print("ADDED: Created sample file 'sound/samples/streamed_audio/%s.aiff'" % m64Name)
    
    aRead.close()


"""
Add a new sequence to the sequence IDs enum in include/seq_ids.h.
"""
def append_seq_id(seqName, decompFolder, replace):
    seqIdsPath = os.path.join(decompFolder, "include/seq_ids.h")
    
    seqIdsFile = open(seqIdsPath, "r")
    seqIdsLines = seqIdsFile.readlines()
    seqIdsFile.close()
    listFound = False
    seq_index = None
    enum_start = 0
    
    for i in range(len(seqIdsLines)):
        # Check for end of enum
        if replace and "enum SeqId {" in seqIdsLines[i]:
            enum_start = i + 1
        elif replace and seqName in seqIdsLines[i]:
            seq_index = i - enum_start
            listFound = True
            break
        elif not replace and "SEQ_COUNT" in seqIdsLines[i]:
            seqIdsLines.insert(i, "    %s,\n" % seqName)
            listFound = True
            break
    
    if not listFound:
        raise ValueError("'SEQ_COUNT' end macro missing from include/seq_ids.h! Aborted")
    
    if not replace:
        seqIdsFile = open(seqIdsPath, "w", newline="\n")
        seqIdsFile.writelines(seqIdsLines)
        seqIdsFile.close()
        
        print("CHANGED: Modified 'include/seq_ids.h'")

    # seq_index will be None if not replacing
    return seq_index

"""
Add corresponding entry for the new sequence in the volume table in src/audio/external.c.
"""
def append_default_volume_table(volume, decompFolder, seq_index):
    externalPath = os.path.join(decompFolder, "src/audio/external.c")
    
    externalFile = open(externalPath, "r")
    externalLines = externalFile.readlines()
    externalFile.close()
    inTable = False
    table_index = 0
    found_volume = seq_index is None # Default to found since we're replacing otherwise
    
    for i in range(len(externalLines)):
        if not inTable:
            # Check for start of table
            if "sBackgroundMusicDefaultVolume" in externalLines[i]:
                inTable = True
        # Check for end of table
        else:
            if table_index == seq_index:
                externalLines[i] = "    %d,\n" % volume
                found_volume = True
                break
            if "}" in externalLines[i] and seq_index is None:
                externalLines.insert(i, "    %d,\n" % volume)
                break
            table_index = table_index + 1

    if not inTable:
        raise ValueError("'sBackgroundMusicDefaultVolume' table missing from src/audio/external.c! Aborted")

    if not found_volume:
        raise ValueError(f"Could not find volume index {seq_index} in src/audio/external.c! Aborted")

    externalFile = open(externalPath, "w", newline="\n")
    externalFile.writelines(externalLines)
    externalFile.close()  
    
    print("CHANGED: Modified 'src/audio/external.c'")
 

"""
Verify a given AIFF file path is valid.
"""
def verify_aiff(aiffPath):
    if not os.path.exists(aiffPath):
        print("Error: aiff file does not exist.")
        return False
    
    try: a = aifc.open(aiffPath, "r")
    except aifc.Error:
        print("Error: file was not a valid AIFF file.\nIf you are exporting with Audacity 2.4 or later,\nplease use an earlier version (2.3.x or earlier)\nas AIFF exporting is broken.")
        return False
    
    if a.getnchannels() > 1:
        print("Error: tool currently only supports mono audio.")
        return False
    
    return True


"""
Verify a given sequence name is valid.
"""
def verify_name(name):
    if not re.fullmatch("[0-9A-Za-z_ ]+", name):
        print("Error: Invalid name entered, must contain only letters, numbers, underscores and spaces")
        return False
    
    return True


"""
Verify a given decomp folder is valid.
"""
def verify_decomp(decompFolder):
    # Check that the folder is decomp
    if not os.path.exists(os.path.join(decompFolder, "Makefile")):
        print("Error: Given directory does not exist / is not a decomp folder.")
        return False
    
    # Check that the required files are there
    if not os.path.exists(os.path.join(decompFolder, "include/seq_ids.h")):
        print("Error: 'include/seq_ids.h' is missing!")
        return False
    
    if not os.path.exists(os.path.join(decompFolder, "src/audio/external.c")):
        print("Error: 'src/audio/external.c' is missing!")
        return False  
    
    return True


"""
Add a new piece of streamed audio to the game.
"""
def add_streamed_audio(aiffPath, name, decompFolder):
    # Todo:
    # Custom volume
    # Custom loop points
    # Option to keep existing loop points (detect loop points?)
    print("")
    name = name.lower().replace(" ","_")
    m64Name, replace = create_new_sequence(name, decompFolder)
    
    copy_aiff_data(aiffPath, m64Name, decompFolder)
    instNo = add_streamed_audio_inst(m64Name, decompFolder, replace)

    volume = prompt_int_range("Song volume", 0, 127)
    if volume is None:
        explicit_exit('No volume was entered.')
    create_m64(m64Name, instNo, volume, decompFolder)
    
    seqName = "SEQ_STREAMED_" + name.upper()
    seq_index = append_seq_id(seqName, decompFolder, replace)
    append_default_volume_table(volume, decompFolder, seq_index)
    print("")
    print("Done! Your sequence has been added as %s." % seqName)


"""
Main user input function.
"""
def main():
    decompFolder = os.path.expanduser(input("Enter decomp directory: "))
    if not verify_decomp(decompFolder): return
    
    check_if_bank_exists(decompFolder)
    aiffPath = os.path.expanduser(input("Enter path for the .aiff file: "))
    if not verify_aiff(aiffPath): return

    a = aifc.open(aiffPath, "r")
    print("\nAIFF data:\n\tSample rate: %dHZ\n\tTotal samples: %d\n\tLength: %.1f seconds\n" % (a.getframerate(), a.getnframes(), a.getnframes()/a.getframerate()))
    if (a.getframerate() > 32000):
        if not prompt_yn("Warning: sample rate (%dHZ) exceeds recommended rate of 32000HZ.\nConsider reducing sample rate to save space.\nContinue?"):
            return
    
    name = input("Enter a name for the streamed audio: ")
    if not verify_name(name): return
    
    add_streamed_audio(aiffPath, name, decompFolder)
    

main()