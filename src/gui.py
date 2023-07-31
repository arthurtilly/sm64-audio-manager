import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import tkinter as tk
import os
import aifc
import json
import tkinter.ttk as ttk
from tkinter import DISABLED, filedialog as fd

from misc import *
import main

SCALE = 1
decomp = None

guiscale = lambda x: int(x * SCALE)

window = tk.Tk()
window.tk.call('tk', 'scaling', SCALE * 1.3)
window.title("SM64 Audio Manager")
style = ttk.Style()
style.theme_use('default')

# this stuff is to remove some ugly default styling on focused elements
style.configure('Treeview.Item', indicatorsize=0)
style.configure("Bottom.TFrame",background="lightgrey", relief="groove")
style.configure("Tab", focuscolor=style.configure(".")["background"])
style.configure("TButton", focuscolor=style.configure(".")["background"])

if not os.path.exists("persistent.json"):
    persistent = {}
else:
    with open("persistent.json", "r") as jsonFile:
        persistent = json.load(jsonFile)

if "decomp" in persistent:
    decomp = persistent["decomp"]

# Generic class for a frame that can switch between multiple pages
class SwitchableFrame:
    def __init__(self, parent):
        self.parent = parent
        self.create_frame(self.parent)
        
    def create_frame(self, parent):
        self.frame = ttk.Frame(master=parent)
        self.frame.pack(fill=tk.BOTH, expand=True)

    def switch_page(self, createPageFunc):
        self.frame.destroy()
        self.create_frame(self.parent)
        createPageFunc(self)

# The frame in the top right that controls the main input
class MainFrameManager(SwitchableFrame):
    def __init__(self, parent):
        SwitchableFrame.__init__(self, parent)
        if decomp is None:
            self.create_no_dir_set_page()
        else:
            self.create_regular_page()
            bottomFrameManager.decompDirectoryText.set("Decomp directory: %s" % decomp)


    # Create the page that is displayed when no decomp directory is set
    def create_no_dir_set_page(self):
        self.noDirSetLabel = ttk.Label(master=self.frame, text="No decomp directory chosen...")
        self.noDirSetLabel.pack(anchor="center", expand=True)

    
    # Create the regular page for importing sequences
    def create_regular_page(self):
        self.leftFrame = ttk.Frame(master=self.frame)
        self.leftFrame.pack(fill=tk.Y, side=tk.LEFT)

        self.sequences = scan_all_sequences(decomp)
        self.currentSeqId = 0

        # Create the list of sequences on the left
        self.seqList = ttk.Treeview(master=self.leftFrame, show="tree")
        self.seqList.column("#0",width=guiscale(180), stretch=tk.NO, anchor="w")
        for i, seq in enumerate(self.sequences):
            self.seqList.insert(parent='',id=i+1,index=i,text="0x%02X - %s" % (i+1,seq[0]))
        self.seqList.insert(parent='',id=0,index=0,text="Add new sequence...")
        self.seqList.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        self.seqList.selection_set(0)
        self.seqList.bind("<<TreeviewSelect>>", self.seqlist_selection_changed)

        # Create the scrollbar for the sequence list
        vsb = ttk.Scrollbar(master=self.leftFrame, orient="vertical", command=self.seqList.yview)
        vsb.pack(fill=tk.Y, side=tk.RIGHT, expand=True)
        self.seqList.configure(yscrollcommand=vsb.set)

        # Create the options page
        self.optionsFrame = ttk.Frame(master=self.frame)
        self.optionsFrame.pack(fill=tk.X, side=tk.TOP, expand=True, padx=10, pady=10)

        for i in range(4):
            self.optionsFrame.rowconfigure(i, minsize=guiscale(30))

        self.optionsFrame.columnconfigure(0, weight=1)

        # First line: Select sfx
        self.selectSoundFileFrame = ttk.Frame(master=self.optionsFrame)
        self.selectSoundFileFrame.grid(row=0, column=0, pady=(10,0))
        self.selectedSoundFile = None
        self.selectedFileLabelText = tk.StringVar()
        self.selectedFileLabelText.set("Selected sound file: None")
        self.selectedFileLabel = ttk.Label(master=self.selectSoundFileFrame, textvariable=self.selectedFileLabelText)
        self.selectedFileLabel.grid(sticky=tk.W, row=0,column=0)
        self.selectSoundFileButton = ttk.Button(master=self.selectSoundFileFrame, text="Browse...",command=self.select_sound_file_button_pressed)
        self.selectSoundFileButton.grid(row=0,column=1, padx=(10,0))
        self.estimatedSizeLabel = ttk.Label(master=self.selectSoundFileFrame, text="")
        self.estimatedSizeLabel.grid(sticky=tk.W, row=1,column=0)

        # Second line: Set loop info
        self.loopInfoFrame = ttk.Frame(master=self.optionsFrame)
        self.loopInfoFrame.grid(row=1, column=0, padx=20, pady=10)

        self.doLoop = tk.IntVar()
        self.doLoop.set(True)
        self.loopCheckbutton = ttk.Checkbutton(master=self.loopInfoFrame, text="Loop", variable=self.doLoop, takefocus=False, command=self.loop_checkbutton_pressed)
        self.loopCheckbutton.pack(side=tk.LEFT)

        self.loopBeginLabel = ttk.Label(master=self.loopInfoFrame, text="Loop start:")
        self.loopBeginLabel.pack(side=tk.LEFT, padx=(40,2))

        self.loopBegin = tk.StringVar()
        self.loopBegin.set("0")
        self.loopBeginEntry = ttk.Entry(master=self.loopInfoFrame, width=10, textvariable=self.loopBegin, justify=tk.RIGHT)
        self.loopBeginEntry.pack(side=tk.LEFT)

        self.loopEndLabel = ttk.Label(master=self.loopInfoFrame, text="Loop end:")
        self.loopEndLabel.pack(side=tk.LEFT, padx=(40,2))

        self.loopEnd = tk.StringVar()
        self.loopEnd.set("0")
        self.loopEndEntry = ttk.Entry(master=self.loopInfoFrame, width=10, textvariable=self.loopEnd, justify=tk.RIGHT)
        self.loopEndEntry.pack(side=tk.LEFT)

        # Third line: Set panning 
        self.panningNotebook = ttk.Notebook(master=self.optionsFrame)
        self.panningNotebook.grid(row=2, column=0)

        self.pans = []
        self.create_panning_tab()

        # Grid for containing name options
        self.namesFrame = ttk.Frame(master=self.optionsFrame)
        self.namesFrame.grid(row=3, column=0, padx=10, pady=(20,0))

        for i in range(4):
            self.namesFrame.rowconfigure(i, minsize=guiscale(30))

        # Fourth line: Set sequence name
        self.sequenceNameLabel = ttk.Label(master=self.namesFrame, text="Sequence name:")
        self.sequenceNameLabel.grid(row=0, column=0, sticky=tk.E, padx=(0,2))

        self.sequenceName = tk.StringVar()
        self.sequenceName.set("")
        self.sequenceNameEntry = ttk.Entry(master=self.namesFrame, width=30, textvariable=self.sequenceName, justify=tk.LEFT)
        self.sequenceNameEntry.grid(row=0, column=1, sticky=tk.W)

        # Fifth line: Set sequence filename
        self.sequenceFilenameLabel = ttk.Label(master=self.namesFrame, text="Sequence filename:")
        self.sequenceFilenameLabel.grid(row=1, column=0, sticky=tk.E, padx=(0,2))

        self.sequenceFilename = tk.StringVar()
        self.sequenceFilename.set("")
        self.sequenceFilename.trace("w", self.sequence_filename_changed)
        self.sequenceFilenameEntry = ttk.Entry(master=self.namesFrame, width=30, textvariable=self.sequenceFilename, justify=tk.LEFT)
        self.sequenceFilenameEntry.grid(row=1, column=1, sticky=tk.W)

        # Sixth line: Set soundbank name
        self.soundbankNameLabel = ttk.Label(master=self.namesFrame, text="Soundbank name:")
        self.soundbankNameLabel.grid(row=2, column=0, sticky=tk.E, padx=(0,2))

        self.soundbankName = tk.StringVar()
        self.soundbankName.set("")
        self.soundbankNameEntry = ttk.Entry(master=self.namesFrame, width=30, textvariable=self.soundbankName, justify=tk.LEFT)
        self.soundbankNameEntry.grid(row=2, column=1, sticky=tk.W)

        # Seventh line: Set sample name
        self.sampleNameLabel = ttk.Label(master=self.namesFrame, text="Sample name:")
        self.sampleNameLabel.grid(row=3, column=0, sticky=tk.E, padx=(0,2))

        self.sampleName = tk.StringVar()
        self.sampleName.set("")
        self.sampleNameEntry = ttk.Entry(master=self.namesFrame, width=30, textvariable=self.sampleName, justify=tk.LEFT)
        self.sampleNameEntry.grid(row=3, column=1, sticky=tk.W)

        # Import button
        self.importButtonFrame = ttk.Frame(master=self.frame)
        self.importButtonFrame.pack(side=tk.TOP)

        self.importButton = ttk.Button(master=self.importButtonFrame, text="Import", command=self.import_pressed)
        self.importButton.pack(padx=(2,2), pady=2)

        self.importInfoLabel = ttk.Label(master=self.importButtonFrame, text="")
        self.importInfoLabel.pack(padx=(2,2),pady=4)

        self.toggle_import_options(tk.DISABLED)


    # Switch between having all options enabled or disabled
    def toggle_import_options(self, state):
        self.estimatedSizeLabel.config(state=state)
        self.loopCheckbutton.config(state=state)
        for i, (frame, label, value, slider) in enumerate(self.pans):
            label.config(state=state)
            slider.config(state=state)
            self.panningNotebook.tab(i, state=state)
        self.sequenceNameLabel.config(state=state)
        self.sequenceNameEntry.config(state=state)
        self.sequenceFilenameLabel.config(state=state)
        self.sequenceFilenameEntry.config(state=state)
        self.soundbankNameLabel.config(state=state)
        self.soundbankNameEntry.config(state=state)
        self.sampleNameLabel.config(state=state)
        self.sampleNameEntry.config(state=state)
        self.importButton.config(state=state)
        if state == tk.DISABLED or self.doLoop:
            self.toggle_loop_options(state)


    # Toggle loop options between enabled and disabled
    def toggle_loop_options(self, state):
        self.loopBeginLabel.config(state=state)
        self.loopBeginEntry.config(state=state)
        self.loopEndLabel.config(state=state)
        self.loopEndEntry.config(state=state)


    # Change the info message
    def set_info_message(self, message, colour):
        self.importInfoLabel.config(text=message, foreground=colour)


    # Create a new tab for the panning of an audio channel
    def create_panning_tab(self):
        panningFrame = ttk.Frame(master=self.panningNotebook)
        self.panningNotebook.add(panningFrame, text="Channel %d" % (len(self.pans)+1))

        panningLabel = ttk.Label(master=panningFrame, text="Pan: 0")
        panningLabel.pack(side=tk.LEFT, padx=(0,5))

        panningValue = tk.IntVar()
        panningValue.set(0)
        panningValue.trace("w", self.panning_changed)
        panningSlider = ttk.Scale(master=panningFrame, from_=-63, to=63, orient=tk.HORIZONTAL, variable=panningValue, takefocus=False)
        panningSlider.pack(side=tk.RIGHT)

        self.pans.append((panningFrame, panningLabel, panningValue, panningSlider))


    # Make the notebook for the panning tabs have the exact right number of tabs
    def resize_panning_notebook(self, size):
        if len(self.pans) > size:
            for i in range(len(self.pans) - size):
                frame, label, value, slider = self.pans.pop()
                self.panningNotebook.forget(frame)
                frame.destroy(); label.destroy(); slider.destroy()
        elif len(self.pans) < size:
            # Create new frames
            for i in range(size - len(self.pans)):
                self.create_panning_tab()


    # Import a sequence into decomp
    def import_pressed(self):
        # Validate entered loop points
        try:
            loopBeginValue = float(self.loopBegin.get()) * 1000
        except ValueError:
            self.set_info_message("Error: Invalid loop start value '%s'" % self.loopBegin.get(), "red")
            return
        
        try:
            loopEndValue = float(self.loopEnd.get()) * 1000
        except ValueError: 
            self.set_info_message("Error: Invalid loop end value '%s'" % self.loopEnd.get(), "red")
            return
        
        loopBegin, loopEnd = calculate_loops(self.selectedSoundFile,
            None, loopBeginValue, None, loopEndValue)

        # Calculate array of panning values
        panning = []
        for frame, label, value, slider in self.pans:
            panning.append(value.get())

        # Determine which sequence ID to replace, or to add a new one
        if self.currentSeqId == 0:
            replace = None
        else:
            replace = str(self.currentSeqId)

        try:
            main.import_audio(decomp, self.selectedSoundFile, replace,
                    self.sequenceName.get(), self.sequenceFilename.get(), self.soundbankName.get(), self.sampleName.get(),
                    self.doLoop.get(), loopBegin, loopEnd, panning)
            self.set_info_message("Success!", "green")
            if replace is None:
                # If not replacing, add a new sequence to the view and select it
                self.sequences.append((self.sequenceFilename.get(), self.sequenceName.get()))
                id = len(self.sequences)
                self.seqList.insert(parent='',index=id, id=id, text="0x%02X - %s" % (id,self.soundbankName.get()))
                self.seqList.selection_set(id)
            else:
                # If replacing, change the text of the selected sequence in the view
                self.sequences[self.currentSeqId-1] = (self.sequenceFilename.get(), self.sequenceName.get())
                self.seqList.item(self.currentSeqId, text="0x%02X - %s" % (self.currentSeqId,self.sequenceFilename.get()))
        except AudioManagerException as e:
            # Error encountered, echo the error message
            self.set_info_message("Error: " + str(e), "red")
            

    # Load new sound file
    def select_sound_file_button_pressed(self):
        selectedFile = fd.askopenfilename(filetypes=[("Sound files", "*.aiff")])
        if selectedFile:
            self.selectedSoundFile = selectedFile
            aiffFile = aifc.open(self.selectedSoundFile, "r")
            self.selectedFileLabelText.set("Selected sound file: " + os.path.basename(self.selectedSoundFile))

            # Determine number of channels and initialise notebook for panning tabs
            self.resize_panning_notebook(aiffFile.getnchannels())
            if aiffFile.getnchannels() == 2:
                self.pans[0][2].set(-63)
                self.pans[1][2].set(63)
            else:
                for i in range(len(self.pans)):
                    self.pans[i][2].set(0)
            self.pan_slider_changed(None)
            aiffFile.close()

            # Initialise other data fields
            self.loopEnd.set("%.4f" % (aiffFile.getnframes() / aiffFile.getframerate()))
            filename = os.path.splitext(os.path.basename(self.selectedSoundFile))[0].replace(' ', '_')
            self.sequenceName.set("SEQ_STREAMED_%s" % filename.upper())
            # If a vanilla sequence, don't change the sequence filename to be safe
            if self.currentSeqId == 0 or self.currentSeqId > 0x22:
                self.sequenceFilename.set("%s" % filename.lower())

            self.soundbankName.set("%s" % filename.lower())
            self.sampleName.set("%s" % filename.lower())
            self.estimatedSizeLabel.config(text="Estimated size: %.2f MB" % estimate_audio_size(selectedFile), foreground="black")

            # Enable all options
            self.toggle_import_options(tk.NORMAL)
            self.panningNotebook.select(0)


    # Toggle the loop options on or off whenever the loop checkbox is modified
    def loop_checkbutton_pressed(self):
        self.toggle_loop_options(tk.NORMAL if self.doLoop.get() else tk.DISABLED)


    # Update the pan value display when the slider is changed
    def panning_changed(self, *args):
        for frame, label, value, slider in self.pans:
            label.config(text = "Pan: %d" % slider.get())
    

    # Update the warning message when the sequence filename is changed
    def sequence_filename_changed(self, *args):
        # If vanilla sequence:
        if self.currentSeqId != 0 and self.currentSeqId <= 0x22:
            if self.sequences[self.currentSeqId-1][0] != self.sequenceFilename.get():
                self.set_info_message("Warning: Changing vanilla sequence filenames can cause build issues.", "darkorange")
            else:
                self.set_info_message("", "black")


    # When a new sequence is selected, update some of the info on the right
    def seqlist_selection_changed(self, event):
        id = int(self.seqList.selection()[0])
        self.currentSeqId = id
        if id != 0:
            self.sequenceName.set(self.sequences[id-1][1])
            self.sequenceFilename.set(self.sequences[id-1][0])


# The frame that displays the current decomp directory
class BottomFrameManager:
    def __init__(self, parent):
        self.frame = ttk.Frame(master=parent, style="Bottom.TFrame")
        self.frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.decompDirectoryText = tk.StringVar(value="Decomp directory: Not set")
        
        self.decompTextLabel = ttk.Label(master=self.frame, textvariable=self.decompDirectoryText, background="lightgrey")
        self.decompTextLabel.pack(side=tk.LEFT, padx=(2,10))
        
        self.setDecompFolder = ttk.Button(master=self.frame, text="Choose decomp folder...", command=change_decomp_folder, takefocus=False)
        self.setDecompFolder.pack(side=tk.LEFT, padx=(2,2), pady=4)


# Save all persistent data
def save_persistent():
    with open("persistent.json", "w") as f:
        json.dump(persistent, f)


# Open a new decomp folder
def change_decomp_folder():
    global decomp
    folder = fd.askdirectory()
    if folder:
        persistent["decomp"] = folder
        save_persistent()
        decomp = folder
        bottomFrameManager.decompDirectoryText.set("Decomp directory: %s" % decomp)
        mainFrameManager.switch_page(MainFrameManager.create_regular_page)

bottomFrameManager = BottomFrameManager(window)
mainFrameManager = MainFrameManager(window)

window.mainloop()