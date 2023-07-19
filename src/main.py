import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import os, sys
import json
import aifc

import m64, aiff, soundbank
from misc import *


# Import an audio file as streamed audio into a decomp folder
def import_audio(decomp, inputAiff, replace=None,
    seqName=None, seqFilename=None, soundbankName=None, sampleName=None,
    loop=False, loopBegin=None, loopEnd=None,
    panning=None):

    validate_decomp(decomp)

    with open(os.path.join(decomp, "sound", "sequences.json"), "r") as seqJson:
        seqJsonData = json.load(seqJson)
    
    # Generate names if required
    if seqName is None:
        seqName = "SEQ_" + os.path.splitext(os.path.basename(inputAiff))[0].upper().replace(' ', '_')
    if seqFilename is None:
        seqFilename = os.path.splitext(os.path.basename(inputAiff))[0].lower().replace(' ', '_')
    if soundbankName is None:
        soundbankName = os.path.splitext(os.path.basename(inputAiff))[0].lower().replace(' ', '_')
    if sampleName is None:
        sampleName = os.path.splitext(os.path.basename(inputAiff))[0].lower().replace(' ', '_')

    # Validate all names
    validate_name(seqName, "sequence name")
    validate_name(soundbankName, "soundbank name")
    validate_name(sampleName, "sample name")
    validate_name(seqFilename, "sequence filename")

    if replace is None:
        # Get sequence ID of new sequence
        seqId = find_new_seq_id(seqJsonData)
    else:
        # Remove old data before importing sequence
        # Check given sequence ID is valid
        try:
            if replace[:2].lower() == "0x":
                seqId = int(replace[2:], 16)
            else:
                seqId = int(replace)
        except ValueError:
            raise AudioManagerException("Invalid sequence ID '%s'" % replace)
        # Remove sequence entry from sequences.json and find corresponding soundbank
        oldSoundbank = None
        for name in seqJsonData.keys():
            try:
                if int(name[:2], 16) == seqId:
                    if isinstance(seqJsonData[name], dict): # Used for lakitu cutscene
                        oldSoundbank = seqJsonData[name]["banks"][0]
                    else:
                        oldSoundbank = seqJsonData[name][0]
                    seqJsonData.pop(name)
                    # Remove m64 file
                    delete_file(os.path.join(decomp, "sound", "sequences", "us", name+".m64"))
                    break
            except ValueError:
                continue

        if oldSoundbank is None:
            raise AudioManagerException("Sequence ID '%s' is out of range" % replace)

        soundbankPath = os.path.join(decomp, "sound", "sound_banks", oldSoundbank + ".json")
        if os.path.exists(soundbankPath):
            with open(soundbankPath, "r") as soundbankJson:
                soundbankJsonData = json.load(soundbankJson)

            # Check that the soundbank is a streamed audio soundbank and not a vanilla one
            if soundbankJsonData["sample_bank"] == "streamed_audio":
                # Remove referenced samples
                for inst in soundbankJsonData["instruments"].values():
                    delete_file(os.path.join(decomp, "sound", "samples", "streamed_audio", inst["sound"] + ".aiff"))
                # Remove soundbank file
                delete_file(soundbankPath)
    
    # Check that no names are duplicates
    check_names_for_duplicates(decomp, seqId, seqName, soundbankName, sampleName)

    # Split channels of the aiff file and move all the samples to the sample folder.
    # Also add loop points to the samples if required.
    splitFiles = aiff.process_aiff_file(inputAiff,
        os.path.join(decomp, "sound", "samples", "streamed_audio"),
        outputName=sampleName, loop=loop, loopBegin=loopBegin, loopEnd=loopEnd)
    
    # Create the m64 for the sequence.
    m64.create_m64(os.path.join(decomp, "sound", "sequences", "us", ("%02X_" % seqId) + seqFilename + ".m64"), numChannels=len(splitFiles), loop=loop, panning=panning)

    # Create the soundbank.
    soundbank.create_soundbank(decomp, soundbankName, splitFiles)

    # Begin reading the sequence id table.
    seqIdsPath = os.path.join(decomp, "include", "seq_ids.h")
    seqTable = load_table(seqIdsPath, "enum SeqId")

    if replace is not None:
        seqTable[seqId] = (seqName, "0x%02X" % seqId)
    else:
        seqTable.insert(-1, (seqName, "0x%02X" % seqId))

    # Save table
    save_table(seqIdsPath, "enum SeqId", seqTable)

    # Add entry of new sequence to sequences.json
    seqJsonData[("%02X_" % seqId) + seqFilename] = [soundbankName]

    with open(os.path.join(decomp, "sound", "sequences.json"), "w") as seqJson:
        json.dump(seqJsonData, seqJson, indent=4)



# Main loop to handle command line input
if __name__ == "__main__":
    # Process given arguments
    import argparse
    parser = argparse.ArgumentParser(description="Streamed audio tool for the SM64 Decomp")
    subparsers = parser.add_subparsers(dest="command")
    import_parser = subparsers.add_parser("import", help="Import a sound file into a decomp repo as a sequence")
    import_parser.add_argument("decomp", help="Path to the decomp repo", metavar="DECOMP")
    import_parser.add_argument("input", help="Path to the sound file", metavar="SOUND_FILE")
    import_parser.add_argument("-r", "--replace", help="ID of an existing sequence to replace", metavar="SEQ_ID", type=str, default=None)
    import_parser.add_argument("-q", "--seqname", help="Specify name of the sequence (e.g. SEQ_LEVEL_TEST)", metavar="SEQ_NAME", default=None)
    import_parser.add_argument("-f", "--seqfilename", help="Specify the sequence file's name (no extension)", metavar="SEQ_FILENAME", default=None)
    import_parser.add_argument("-k", "--soundbank", help="Specify name of the soundbank", metavar="SOUNDBANK_NAME", default=None)
    import_parser.add_argument("-n", "--samplename", help="Specify name of the sample file(s) (no extension)", metavar="SAMPLE_NAME", default=None)
    import_parser.add_argument("-l", "--loop", help="Enable looping for the sequence", action="store_true")
    loopbegin = import_parser.add_mutually_exclusive_group()
    loopbegin.add_argument("-b", help="Loop beginning (in milliseconds)", metavar="BEGIN", type=float)
    loopbegin.add_argument("-B", help="Loop beginning (in samples)", metavar="BEGIN", type=int)
    loopend = import_parser.add_mutually_exclusive_group()
    loopend.add_argument("-e", help="Loop end (in milliseconds)", metavar="END", type=float)
    loopend.add_argument("-E", help="Loop end (in samples)", metavar="END", type=int)
    import_parser.add_argument("-p", "--panning", help="Panning for each channel (between -63 and 64)", type=int, nargs="+", default=None, metavar="PAN")

    m64_parser = subparsers.add_parser("m64", help="Create a new m64 file for streamed audio with a given number of channels")
    m64_parser.add_argument("output", help="Output path for the m64 file", metavar="OUTPUT")
    m64_parser.add_argument("-c", "--channels", help="Number of channels in the m64 file", type=int, default=1, metavar="CHANNELS")
    m64_parser.add_argument("-l", "--loop", help="Enable looping", action="store_true")
    m64_parser.add_argument("-p", "--panning", help="Panning for each channel (between -63 and 64)", type=int, nargs="+", default=None, metavar="PAN")

    aiff_parser = subparsers.add_parser("aiff", help="Process a sound file into useable sample files")
    aiff_parser.add_argument("sound", help="Path to the sound file", metavar="SOUND_FILE")
    aiff_parser.add_argument("output", help="Output folder for the sample files", metavar="OUTPUT")
    aiff_parser.add_argument("-n", "--samplename", help="Name of the output sample file(s)", metavar="SAMPLE_NAME", default=None)
    aiff_parser.add_argument("-l", "--loop", help="Enable looping for the sample", action="store_true")
    loopbegin = aiff_parser.add_mutually_exclusive_group()
    loopbegin.add_argument("-b", help="Loop beginning (in milliseconds)", metavar="BEGIN", type=float)
    loopbegin.add_argument("-B", help="Loop beginning (in samples)", metavar="BEGIN", type=int)
    loopend = aiff_parser.add_mutually_exclusive_group()
    loopend.add_argument("-e", help="Loop end (in milliseconds)", metavar="END", type=float)
    loopend.add_argument("-E", help="Loop end (in samples)", metavar="END", type=int)

    soundbank_parser = subparsers.add_parser("soundbank", help="Create a new soundbank")
    soundbank_parser.add_argument("decomp", help="Path to the decomp repo", metavar="DECOMP")
    soundbank_parser.add_argument("soundbank", help="Name of the soundbank", metavar="NAME", default=None)
    soundbank_parser.add_argument("samples", help="List of paths to the sample files", nargs="+", metavar="SAMPLES")

    args = parser.parse_args(sys.argv[1:])

    # Print help if called with no arguments
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    # Import audio file into decomp
    if args.command == "import":
        loopBegin, loopEnd = None, None
        if args.loop or not (args.b is None and args.B is None and args.e is None and args.E is None):
            args.loop = True
            loopBegin, loopEnd = calculate_loops(args.sound, args.B, args.b, args.E, args.e)
        import_audio(args.decomp, args.input, args.replace, args.seqname, args.seqfilename, args.soundbank, args.samplename, args.loop, loopBegin, loopEnd, args.panning)
    # Create template m64
    elif args.command == "m64":
        m64.create_m64(args.output, args.channels, args.loop, args.panning)
    # Process, split and add loop points to aiff file
    elif args.command == "aiff":
        loopBegin, loopEnd = None, None
        if args.loop or not (args.b is None and args.B is None and args.e is None and args.E is None):
            args.loop = True
            loopBegin, loopEnd = calculate_loops(args.sound, args.B, args.b, args.E, args.e)
        aiff.process_aiff_file(args.sound, args.output, args.samplename, args.loop, loopBegin, loopEnd)
    # Create new soundbank json file
    elif args.command == "soundbank":
        soundbank.create_soundbank(args.decomp, args.soundbank, args.samples)

