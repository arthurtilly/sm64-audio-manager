# SM64 Audio Manager (v0.1)

SM64 Audio Manager is a tool for the SM64 Decompilation (and PC Port) created by Arthurtilly that in the future will provide an easy resource for managing audio and music within decomp.

Currently it is in early alpha and only supports importing streamed music tracks. Note that the program may be unstable if given certain incorrect inputs, and while I have done my best to catch these I strongly recommend you use version control such as Git to make sure things can be reverted.

## Usage

In a bash shell:
```bash
cd <directory>
python3 main.py
```
Alternatively, you can run main.py directly from any Python IDE you have installed.

## Features

* Set up a streamed audio sound bank
* Create a looping streamed music track from an AIFF file
 * Specify custom loop points

## Planned features

* An actual GUI
* More streamed audio options
 * Support for maintaining existing loop points
 * Volume options
 * Ability to more effectively manage tracks (deletion, reordering)
* Tools to modify existing instrument banks
* Ability to modify the game's regular sound player
 * Add new sounds and sound IDs
 * Ability to create new sound banks
 * Delete old sounds

## Contributing

Pull requests and raising issues are very welcome.

## Credits

Thanks to Matt, Blakeoramo and Carnivorous for a lot of help getting stuff to work.
