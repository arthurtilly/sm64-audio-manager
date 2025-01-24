# SM64 Audio Manager

## About

This is a GUI and command line tool for importing and managing streamed audio sequences in the SM64 decompilation. It supports audio files of any number of channels and can add new sequences to the game or replace old ones.

## How to Open

### Windows

Run the file named  `windows.bat`. If Python is not already installed on your system, it will be installed first. This will open up the GUI for the tool. Alternatively, you can run `src/gui/gui_main.py` from the command line or from a Python IDE.

### Linux

Run the script named `linux.sh`. This will also install Python and open the GUI. Alternatively, you can run `src/gui/gui_main.py` from the command line or from a Python IDE.

## Using the Tool

When the tool opens, you will be prompted to select your decomp folder. After this, click on the "Browse..." button, and select the AIFF file you wish to import. From here you can choose loop points, panning for each channel, and the names to save the outputted files as. On the left, you can select which sequence you want to replace, or add a new sequence.

Once you are done, press the "Import" button. The new sequence will be imported into your repository. From here, you can just use `make`.

It is HIGHLY recommended to use Git to back up your repository before using this tool on the offchance that something goes wrong.

## Troubleshooting

- If you are replacing vanilla sequences, you should use the same sequence name and sequence filename as the old sequence.
    - Using a different sequence name will result in the old references of the sequence name needing to be updated.
    - Using a different sequence filename will cause the repo to fail to build due to the asset extraction program extracting the old sequence again. You will either need to use the same sequence filename, or edit the asset extraction script to skip the old sequence file being replaced.
###
- If you are not using HackerSM64 v2.1 or higher, in order to build after adding a new sequence you will have to navigate to `src/audio/external.c`, find a table labelled `sBackgroundMusicDefaultVolume[]`, and add an entry corresponding to the new sequence added. This table is deprecated in HackerSM64 and it is highly recommended to make your hacks with this repo instead.
###
- If you have used the older version of this tool in the past, then attemping to use this tool will result in an error of `reference to non-existing sound bank streamed_audio` when building.
    - To fix this without breaking the old songs, reset the repository if you tried to press Import.
    - Then navigate to `sound/samples` and find the `streamed_audio` folder.
    - Rename this folder to something else, and then go to the `sound/sound_banks` folder.
    - From here, find and open the JSON file corresponding to the old streamed audio bank.
    - Find the line that says `"sample_bank": "streamed_audio",` and update this to whatever you renamed the streamed_audio folder to.
    - You will only have to do these steps once in order for your repo to now be compatible with the new tool.
###
- If you get an error saying "No module named 'aifc'", your Python version is too new. You will need to use a Python version that is 3.12 or earlier due to the aifc module being deprecated in Python 3.13. This will be fixed in the future.

## Command Line

This tool also supports advanced command line usage. To use this, run `python src/main.py <arguments>` from the command line. There are four submodules that can be used.

### Importing

Usage: `python src/main.py import <decomp> <aiff file> [optional arguments]`

#### Optional Arguments:
```
-r <sequence ID>           (replace an existing sequence)
-l                         (enable looping)
-b <loop begin (ms)>       (default: 0)
-B <loop begin (samples)>  (default: 0)
-e <loop end (ms)>         (default: end of file)
-E <loop end (samples)>    (default: end of file)
-p <pan> [<pan>, ...]      (default: 0, or -63, 64 if the input has 2 channels)
-q <sequence name>         (default: SEQ_<INPUT_FILE>)
-f <sequence filename>     (default: lowercase, same as input file)
-k <soundbank name>        (default: lowercase, same as input file)
-n <sample name>           (default: lowercase, same as input file)
-h                         (show the help message)
```

#### Example Uses
With a decomp directory located at `U:/home/user/sm64`:
```
python src/main.py import U:/home/user/sm64 example1.aiff -r 0x18 -b 0 -e 60000
                                        ... example2.aiff -l -q SEQ_TEST -f test -k test -n test
                                        ... example3.aiff -l -p -63 63 0
                                        ... example4.aiff -r 0x01 -q SEQ_NEW_STAR_JINGLE
```

#### Argument Descriptions:

- `-r <sequence ID>` (or `--replace`)
    - If specified, the import will be done over an existing sequence.
    - Otherwise the import will create a new sequence and sequence ID.
    - The sequence ID must be a number in either decimal or hex.
    - Example: `-r 0x18` will replace sequence 0x18 which by default is the Endless Stairs.
    - This will delete the previous .m64 file and sequence defines. If the sequence to be replaced is one already exported by this tool, it will also delete the soundbank and sample files.
- `-l` (or `--loop`)
    - Enable looping on the sample. If not specified, the sample will not loop.
- `-b`/`-B <loop begin>` and `-e`/`-E <loop end>`
    - Specify the beginning and ending of the loop. Will enable `-l` if specified.
    - `-b` and `-e` take their arguments in milliseconds.
    - `-B` and `-E` take their arguments in number of samples.
    - The commands for milliseconds and samples are mutually exclusive.
    - By default, the loop will be between the start and end of the entire audio file.
- `-p <pan> [<pan>, ...]` (or `--panning`)
    - Specify the panning on each channel of the audio track, between -63 and 64.
    - If only one value is provided, it will be used for every channel.
    - Otherwise, the number of arguments passed must equal the number of channels.
    - By default the panning will be 0 for every channel.
    - If the track has 2 channels then the default will be -63, 64 instead for a normal stereo track.
- `-q <sequence name>` (or `--seqname`)
    - Specify the name of the sequence. This will be used for the sequence define.
    - Example: `-q SEQ_LEVEL_TEST`
- `-f <sequence filename>` (or `--seqfilename`)
    - Specify the name of the sequence .m64 file to be saved.
    - The file will be saved as `<seq ID>_<seq filename>.m64` in `sound/sequences/us`.
- `-k <soundbank name>` (or `--soundbank`)
    - Specify the name of the soundbank .json file to be saved.
    - The file will be saved as `<soundbank name>.json` in `sound/sound_banks`.
- `-n <sample name>` (or `--samplename`)
    - Specify the name of the sample .aiff file(s) to be saved.
    - If the track has one channel, the file will be saved as `<sample name>.aiff` in `sound/samples`.
    - If the track has multiple channels, the channels will be split into multiple files and will be saved as `<sample name>_1.aiff`, `<sample name>_2.aiff`, etc. instead.

### Creating M64 Sequence Files

Usage: `python src/main.py m64 <output file path> [optional arguments]`

#### Optional Arguments:
```
-l                        (enable looping)
-c <number of channels>   (default: 1)
-p <pan> [<pan>, ...]     (default: 0, or -63, 64 if given 2 channels)
-h                        (show the help message)
```

#### Example Uses
```
python src/main.py m64 generic_stereo.m64 -l -c 2
python src/main.py m64 C:/Users/user/Desktop/three_channels.m64 -c 3 -p -63 64 0
python src/main.py m64 U:/home/user/sm64/sound/sequences/us/23_test.m64 -l
```

#### Argument Descriptions:

- `-l` (or `--loop`)
    - Enable looping support in the m64 file. If not specified, the sequence will not loop.
- `-c <number of channels>` (or `--channels`)
    - Specify the number of channels in the sequence, up to 16.
    - By default, the sequence will have 1 channel.
- `-p <pan> [<pan>, ...]` (or `--panning`)
    - Specify the panning on each channel of the audio track, between -63 and 64.
    - If only one value is provided, it will be used for every channel.
    - Otherwise, the number of arguments passed must equal the number of channels.
    - By default the panning will be 0 for every channel.
    - If the track has 2 channels then the default will be -63, 64 instead for a normal stereo track.

### Processing and Splitting AIFF Sample Files

Usage: `python src/main.py aiff <input file path> <output folder path> [optional arguments]`

#### Optional Arguments:
```
-l                         (enable looping)
-b <loop begin (ms)>       (default: 0)
-B <loop begin (samples)>  (default: 0)
-e <loop end (ms)>         (default: end of file)
-E <loop end (samples)>    (default: end of file)
-n <output sample name>    (default: lowercase, same as input file)
-h                         (show the help message)
```

#### Example Uses
```
python src/main.py aiff example1.aiff output -b 0 -e 60000
python src/main.py aiff example2.aiff U:/home/user/sm64/sound/samples/streamed_audio -l
python src/main.py aiff example3.aiff C:/Users/user/Desktop -n output_file
```

#### Argument Descriptions:

- `-n <output sample name>` (or `--samplename`)
    - Specify the name of the sample .aiff file(s) to be saved.
    - If the track has one channel, the file will be saved as `<sample name>.aiff`.
    - If the track has multiple channels, the channels will be split into multiple files and will be saved as `<sample name>_1.aiff`, `<sample name>_2.aiff`, etc. instead.
- `-l` (or `--loop`)
    - Enable looping on the sample. If not specified, the sample will not loop.
- `-b`/`-B <loop begin>` and `-e`/`-E <loop end>`
    - Specify the beginning and ending of the loop. Will enable `-l` if specified.
    - `-b` and `-e` take their arguments in milliseconds.
    - `-B` and `-E` take their arguments in number of samples.
    - The commands for milliseconds and samples are mutually exclusive.
    - By default, the loop will be between the start and end of the entire audio file.

### Creating Soundbank JSON Files

Usage: `python src/main.py soundbank <decomp> <soundbank name> <samples> [<samples>, ...] [-h]`

#### Example Uses
```
python src/main.py soundbank U:/home/user/sm64 new_soundbank example.aiff
python src/main.py soundbank U:/home/user/sm64 new_soundbank2 example1.aiff example2.aiff example3.aiff
python src/main.py soundbank U:/home/user/sm64 test example_test.aiff
```
Note that only the filename of the sample is needed. The path to the sample does not matter and it does not have to exist.
