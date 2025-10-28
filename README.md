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
