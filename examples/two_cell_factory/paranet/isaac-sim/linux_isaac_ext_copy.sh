#!/bin/bash
set -e

# Define directory paths
SOURCE_DIR="$HOME/code/robot-ces/paranet/isaac-sim/extension"
TARGET_DIR="$HOME/.local/share/ov/pkg/isaac-sim-4.2.0/exts/omni.isaac.examples/omni/isaac/examples/user_examples"

# Check if the script is executable
if [ ! -x "$0" ]; then
    echo "Warning: This script is not executable."
    echo "         Please run the following command to make it executable:"
    echo "         chmod +x $0"
    exit 1
fi

# Check if the source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory $SOURCE_DIR does not exist."
    echo "       Where did you clone the repo?"
    echo "       Assumes \"$HOME/code/\""
    exit 1
fi

# Check if the target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Target directory $TARGET_DIR does not exist."
    exit 1
fi

# Delete all files in the target directory
echo "Deleting all files in $TARGET_DIR..."
rm -rf "$TARGET_DIR"/*

# Copy all files from source to target directory
echo "Copying files from $SOURCE_DIR to $TARGET_DIR..."
cp -r "$SOURCE_DIR"/* "$TARGET_DIR"

# Confirm completion
echo "All files have been successfully copied to $TARGET_DIR."

exit 0
