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

# Run GUI
python3 src/gui/main.py
