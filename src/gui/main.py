import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import tkinter as tk
import os
import json
import tkinter.ttk as ttk
from tkinter import filedialog as fd

from music import *
from resample import *


decomp = None

window = tk.Tk()
window.tk.call('tk', 'scaling', 1.3)
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


# The main window
class MainFrameManager:
    def __init__(self, parent):
        self.parent = parent
        self.create_frame(self.parent)
        if decomp is None:
            self.create_no_dir_set_page()
        else:
            self.create_main_page()
            bottomFrameManager.decompDirectoryText.set("Decomp directory: %s" % decomp)


    # Create a frame for the main window
    def create_frame(self, parent):
        self.frame = ttk.Frame(master=parent)
        self.frame.pack(fill=tk.BOTH, expand=True)


    # Destroy the current frame and load a new one
    def switch_page(self, createPageFunc):
        self.frame.destroy()
        self.create_frame(self.parent)
        createPageFunc(self)


    # Create the page that is displayed when no decomp directory is set
    def create_no_dir_set_page(self):
        self.noDirSetLabel = ttk.Label(master=self.frame, text="No decomp directory chosen...")
        self.noDirSetLabel.pack(anchor="center", expand=True)


    # Create the main page notebook and add all the tabs to it
    def create_main_page(self):
        self.mainNotebook = ttk.Notebook(master=self.frame)
        self.mainNotebook.pack(fill=tk.BOTH, expand=True)
        self.tabs = []

        self.add_tab(StreamedMusicTab, "Streamed Music")
        self.add_tab(ResampleAudioTab, "Resample Audio")


    # Add a new tab to the main page notebook
    def add_tab(self, tabClass, text):
        newFrame = ttk.Frame(master=self.mainNotebook)
        self.mainNotebook.add(newFrame, text=text)
        self.tabs.append(tabClass(newFrame, decomp))


    # Switch the decomp directory for all tabs and reload anything relying on decomp
    def switch_decomp(self, decomp):
        for tab in self.tabs:
            tab.switch_decomp(decomp)


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
        mainFrameManager.switch_decomp(decomp)

bottomFrameManager = BottomFrameManager(window)
mainFrameManager = MainFrameManager(window)

window.mainloop()