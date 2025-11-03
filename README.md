# SM64 Audio Manager

## About

This is a GUI and command line tool for importing and managing instruments, sound effects, and streamed music tracks into the SM64 decompilation via automatically editing the relevant files. It is intended to make adding custom audio to SM64 hacks much easier and more accessible.

## How to Open

### Windows

Run the file named  `windows.bat`. If Python is not already installed on your system, it will be installed first. This will open up the GUI for the tool. Alternatively, you can run `src/gui/gui_main.py` from the command line or from a Python IDE.

### Linux

Run the script named `linux.sh`. This will also install Python and open the GUI. Alternatively, you can run `src/gui/gui_main.py` from the command line or from a Python IDE.

## Using the Tool

When the tool opens, you will be prompted to select your decomp folder. Upon doing so, you will be able to switch between four tabs: **Sound Effects**, **Instruments**, **Convert Audio** and **Streamed Music**.

* **Sound Effects:** Allows you to manage sound effects automatically, allowing you to create sound effects using instruments from the instrument banks and manage `SOUND_<>` defines to be used with `play_sound` and similar functions.
* **Instruments:** Allows you to manage the instrument banks used in the game, allowing you to import new samples and define new instruments in either sound effect banks or music banks.
* **Convert Audio:** Allows you to convert any format of audio file into an AIFF file that can be easily imported as either a sample for an instrument/sound effect or as a streamed music track. Also allows you to resample at a different sample rate and mix down to a mono sample.
* **Streamed Music:** Allows you to manage streamed music tracks, allowing you to import a single audio file as a music track to play in the background.


Here is a basic tutorial on the workflow required to simply add a new sound effect to the game, followed by more in-depth tutorials on the additional features each tab provides.

# How to Create a New Sound Effect

Creating a new sound effect from an audio file requires two steps: first, the sample must be imported as an instrument into one of the sound effect banks in the **Instruments** tab, and then a new sound effect must be created using that instrument in the **Sound Effects** tab.
##
First, if your sample is not an AIFF file, head to the **Convert Audio** tab and convert your audio file into an AIFF file. Samples used for sound effects **MUST** be mono. You can also optionally mix the sample down to a more reasonable sample rate if you wish. The sample rate should be no higher than **32000Hz** as this is the maximum quality SM64 audio can output, but lower sample rates will take up less space in ROM at the cost of quality.
##
Now, head to the **Instruments** tab and choose one of the sound effect banks (anything from `00` to `0A`). Now, Select your AIFF file by clicking the **Browse...** button. Sound effects can either be discrete (will play or start over when `play_sound` is called) or continuous (will continue to play while `play_sound` is called every frame until it stops being called). If your sound is continuous, make sure to set a loop in the sample before importing it, and set the loop points (which are defined in terms of samples) which will default to the very start and end of the sample. Then, press **Import** to import the sample into the sample bank. Note that this will import into the sample bank belonging to the *currently selected instrument bank*.

Now, use the **Insert above/below** button at the top to add a new instrument entry to the bank, or alternatively select one of the existing `<Empty>` entries in the bank. In the *Sample Data* section, select the sample that was just imported. You can use the **Play...** button to preview the sound to make sure it is the correct one. Now, simply press the **Save...** button to save the instrument.

##
Now that the instrument has been created, head to the **Sound Effects** tab. Pick which channel you want your new sound effect to be in; note that only one sound in each channel can be playing at a time. You can use the **Insert above/below** button to add a new sound effect entry to the list, or alternatively select an existing sound to replace it. In the **Replace...** tab, select the bank and instrument that you just created earlier (you can use the **Play...** button to verify it is the correct sound). If your sound effect is continuous, make sure to check the *Continuous* checkbox. Now, simply press the **Replace!** button to initialise the new sound effect.

Finally, to be able to use the sound effect ingame, it must have at least one define associated with it. Press the **Add...** button at the bottom to create a new define and name it whatever you like. Make sure the *Continuous* checkbox matches your sound effect. Now, just press the **Save...** button and you are done! Your sound effect can now be easily played ingame using the define you just created and the `play_sound` function.

# Detailed Feature Explanation

## Sound Effects Tab
### Sound effect list:
* Select the currently focused sound effect from the list on the left of the window.
* You can double-click a sound effect to rename it.
### Add/remove sound entries:
* **Insert below/above**: Creates a new sound effect in the currently selected channel.
* **Delete**: Fully deletes the currently selected sound effect and its defines.
### Edit/replace sound effect:
* **Edit tab**: Lists all currently used banks and instruments in the selected sound effect to be swapped out freely. Can be used to slightly modify existing vanilla sound effects or to change custom ones. More advanced editing of miniseq is not supported.
* **Replace tab**: Completely deletes the miniseq of the currently selected sound effect and replaces it with a simple template based on the given parameters. The template will be slightly different for discrete or continuous sounds.
### Sound defines:
* *Continuous* checkbox: Allows you to override whether or not the `SOUND_DISCRETE` flag is used.
* **Add...**: Create a new define.
* **X** button: Deletes the associated define.
* **Set flags**: Opens a small window where the define's flags can be easily edited and custom flags can be set.
* **Save**: Saves all changes made to `include/sounds.h`.

## Instruments Tab
### Instrument list:
* Select the currently focused bank and instrument from the list on the left of the window.
* Both banks and instruments can be double-clicked to rename them.
### Add/remove instruments:
* **Insert below/above**: Creates a new `<Empty>` instrument in the currently selected bank.
* **Delete**: Deletes the current instrument. This option can only be used either if the instrument is in a music bank, or if the instrument is not used by any sound effects. Deleting an instrument in a sound effect bank will shift all instrument IDs in `00_sound_player.s` automatically. Deleting an instrument in a music bank will **NOT** shift IDs and will cause any sequences using that bank to potentially break.
### Sample import:
* Select a sample to import into the sample bank belonging to the currently selected instrument bank.
* Optionally set loop points, required for continuous sound effects to work properly.
### Sample data:
* Select the sample to be used by the currently selected instrument.
* **Advanced options**: Allows you to set a tuning value (in semitones), additional samples for low and high notes, the release rate, and specify an envelope. These options are uually unnecessary for  sound effects and are intended to be used when adding instruments for music sequences.
* **Save**: Saves the current instrument data to the corresponding instrument bank. If the selected instrument is `<Empty>`, a new instrument will be created.
### References:
* If in a sound effect bank, displays all sound effects that use the currently selected instrument. Instruments can only be deletes if there are no references to them.
## Convert Audio Tab
### Audio file selection:
* Select an audio file of any format to convert it to an AIFF file that can be used by the rest of the tool.
### Output options:
* Choose an output sample rate (anything higher than 32000Hz is unnecessary) and optionally mix down for mono (required for sound effects but not for streamed music).
* Choose an output path and press **Convert!** to convert the audio file. This will automatically select the converted file in the other tabs.
## Streamed Music Tab
### Sequence list:
* Select the sequence to replace on the left of the window, or select the `Add new sequence...` entry to create a new one. Replacing vanilla sequences can potentially cause issues with the build system so making new tracks is preferred.
### Select audio file:
* Select an AIFF audio file to be used as the streamed music track. The estimated size in ROM will be displayed. Note that ROMs cannot exceed 64MB in total so be wary of importing large audio files. Size can be decreased by reducing sample rate or by mixing down to mono, at the cost of audio quality.
### Panning:
* Edit the panning for each channel that the track uses. For mono tracks this will default to 0, and for stereo tracks it will default to -63 (left) and 64 (right).
### Names:
* Select the names that the exported data will use. The sequence name will be what is used to play the track ingame. Note that when replacing vanilla sequences, it is advised not to change the sequence name or sequence filename to avoid build issues.

* Press **Import!** to import the streamed music track.


# Troubleshooting

- If the tool says "Invalid decomp directory!" upon opening your decomp folder, your repository may be too old to work with this tool. Only repositories made with Refresh 13 or higher (e.g. HackerSM64 / UltraSM64) are supported. Check if your repository has the file `include/sounds.h`. If it does not and instead has a file named `include/audio_defines.h`, your repository is too old to be supported.
- If you are not using HackerSM64 v2.1 or higher, in order to build after adding a new streamed music track, you will have to navigate to `src/audio/external.c`, find a table labelled `sBackgroundMusicDefaultVolume[]`, and add an entry corresponding to the new sequence added. This table is deprecated in HackerSM64 and it is highly recommended to make your hacks with this repo instead.