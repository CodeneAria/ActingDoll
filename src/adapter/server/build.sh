#!/bin/bash
set -e

# Build script for acting-doll-server package
echo "=== Building acting-doll-server package ==="

# Clean previous builds
echo "# Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Install build dependencies
echo "# Installing build dependencies..."
pip install --break-system-packages --upgrade build twine

# Install local package dependencies
echo "# Installing local package dependencies..."
pip install --break-system-packages --upgrade ./
ret=$?
if [ $ret -ne 0 ]; then
    echo "=== Failed to install package dependencies. Please check the error messages above. ==="
    exit $ret
fi

# Build the package
echo "# Building package..."
python -m build .

# Check the distribution
echo "# Checking distribution..."
twine check dist/*

echo "=== Complete acting-doll-server ==="

