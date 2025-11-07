#!/bin/bash

# Function to check if a command is available
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists python; then
    echo "Python is not found. Installing..."

    # Detect the package manager
    if command_exists apt; then
        # Update package repositories
        sudo apt update

        # Install Python for Ubuntu-based distributions
        sudo apt install -y python3

        # Install uv from python pip, then we can continue
        python3 -m pip install uv
    elif command_exists pacman; then
        # Install Python for Arch Linux
        sudo pacman -Sy --noconfirm uv
    elif command_exists dnf; then
        # Install Python for Fedora-based distributions
        sudo dnf install -y uv
    else
        echo "Unsupported distribution. Please install Python/uv manually."
        exit 1
    fi

    echo "uv has been installed."
fi

# Install locked python version
uv python install 3.12

# Create the venv
uv venv --clear

# install all packages specified in uv.lock
uv sync

# Run the GUI
uv run src/gui/gui_main.py
