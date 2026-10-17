#!/bin/bash
set -e

echo "=== Initializing Media Manager Directory Structure ==="

# 1. Create base directories
mkdir -p src/core
mkdir -p src/modules
mkdir -p tests/unit/core
mkdir -p tests/unit/modules
mkdir -p tests/integration
mkdir -p data
mkdir -p .github/workflows

# 2. Move existing core or modules folders into src/ if they exist in root
if [ -d "core" ] && [ ! -d "src/core" ]; then
    echo "Moving existing 'core' folder into 'src/'..."
        mv core src/
        elif [ -d "core" ] && [ -d "src/core" ]; then
            echo "Merging existing 'core' folder into 'src/core'..."
                cp -r core/* src/core/
                    rm -rf core
                    fi

                    if [ -d "modules" ] && [ ! -d "src/modules" ]; then
                        echo "Moving existing 'modules' folder into 'src/'..."
                            mv modules src/
                            elif [ -d "modules" ] && [ -d "src/modules" ]; then
                                echo "Merging existing 'modules' folder into 'src/modules'..."
                                    cp -r modules/* src/modules/
                                        rm -rf modules
                                        fi

                                        # 3. Create __init__.py files where necessary
                                        touch src/core/__init__.py
                                        touch src/modules/__init__.py
                                        touch tests/__init__.py
                                        touch tests/unit/__init__.py
                                        touch tests/unit/core/__init__.py
                                        touch tests/unit/modules/__init__.py

                                        echo "=== Folder structure and __init__.py files created successfully! ==="
                                        