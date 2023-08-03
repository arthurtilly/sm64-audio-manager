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
    elif command_exists pacman; then
        # Install Python for Arch Linux
        sudo pacman -Sy --noconfirm python
    elif command_exists dnf; then
        # Install Python for Fedora-based distributions
        sudo dnf install -y python3
    else
        echo "Unsupported distribution. Please install Python manually."
        exit 1
    fi

    echo "Python has been installed."
fi

# Install Python dependencies
if command_exists pacman; then
    if ! pacman -Q python-pyqt6 &>/dev/null; then
        sudo pacman -S python-pyqt6
    fi
    if ! pacman -Q python-av &>/dev/null; then
        temp_folder=$(mktemp -d)
        wget -O "$temp_folder/PKGBUILD" "https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=python-av"
        cd "$temp_folder"
        makepkg -si
        cd -
        rm -rf "$temp_folder"
    fi
else
    python3 -m pip install PyQt6
    python3 -m pip install av
fi

# Run GUI
python3 src/gui/gui_main.py
