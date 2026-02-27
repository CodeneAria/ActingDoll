#!/bin/sh
#set -e
###################################
# Settings
###################################
CURRENT_DIR=$(dirname "$(readlink -f "$0")")
MCP_DIR=$(readlink -f "${CURRENT_DIR}/server")
NODE_DIR=$(readlink -f "${CURRENT_DIR}/acting_doll")
BUILD_MCP=${BUILD_MCP:-"true"}
BUILD_NODE=${BUILD_NODE:-"true"}
PRODUCTION=${PRODUCTION:-"true"}
BUILD_MCP_WITH_DIST=${BUILD_MCP_WITH_DIST:-"false"}
if [ "${BUILD_MCP_WITH_DIST}" == "true" ]; then
    BUILD_MCP="true"
fi

###################################
# Build
###################################
if [ "${BUILD_MCP}" == "true" ]; then
    cd ${MCP_DIR}
    ###############################################################################
    # Control Server Build Script
    ###############################################################################
    # Build script for acting-doll-server package
    echo "# Building acting-doll-server package..."

    # Clean previous builds
    echo "## Cleaning previous builds..."
    rm -rf dist/ build/ *.egg-info/

    # Install build dependencies
    if [ "${BUILD_MCP_WITH_DIST}" == "true" ]; then
        echo "## Installing build dependencies..."
        pip install --break-system-packages --upgrade build twine
    fi

    # Install local package dependencies
    echo "## Installing local package dependencies..."
    pip install --break-system-packages --root-user-action=ignore --upgrade ./
    ret=$?
    if [ $ret -ne 0 ]; then
        echo "=== Failed to install package dependencies. Please check the error messages above. ==="
        exit $ret
    fi

    if [ "${BUILD_MCP_WITH_DIST}" == "true" ]; then
        # Build the package
        echo "## Building package..."
        python -m build .
        ret=$?
        if [ $ret -ne 0 ]; then
            echo "=== Failed to build package. Please check the error messages above. ==="
            exit $ret
        fi

        # Check the distribution
        echo "## Checking distribution..."
        twine check dist/*
        ret=$?
        if [ $ret -ne 0 ]; then
            echo "=== Failed to check distribution. Please check the error messages above. ==="
            exit $ret
        fi
    else
        rm -rf ${MCP_DIR}/dist
    fi

    echo "=== Complete acting-doll-server ==="
fi

###############################################################################
# npm
###############################################################################

if [ "${BUILD_NODE}" == "true" ]; then
    cd ${NODE_DIR}
    # Build script for node package
    echo "# Building node package..."
    npm install -g npm > /dev/null 2>&1
    #npm install > /dev/null 2>&1
    npm audit fix
    if [ "${PRODUCTION}" == "true" ]; then
         npm run build:prod
         ret=$?
    else
         npm run build
         ret=$?
    fi
    if [ $ret -ne 0 ]; then
        echo "=== Failed to build node package. Please check the error messages above. ==="
        exit $ret
    fi
fi

echo "=== Build Settings ==="
echo " - Build MCP: ${BUILD_MCP}"
echo " - Build Node: ${BUILD_NODE}"
echo " - Production Mode: ${PRODUCTION}"
