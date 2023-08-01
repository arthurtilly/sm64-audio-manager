import sys
import os


# Allows importing from the parent directory
def append_parent_dir():
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(parent_dir)


# Base class for a tab in the main window notebook
class MainTab:
    def __init__(self, frame, decomp):
        self.switch_decomp(decomp)
        self.create_page(frame)

    def switch_decomp(self, decomp):
        self.decomp = decomp

    def create_page(frame):
        pass
