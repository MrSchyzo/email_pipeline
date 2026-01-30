#!/usr/bin/env bash

# Copies whatever is inside /app/builtins_inject to /app/builtins
# This is useful for injecting custom built-in functions or scripts
# into an application without modifying the original source code.
SOURCE_DIR="/app/builtins_inject"
TARGET_DIR="/app/builtins"
if [ -d "$SOURCE_DIR" ]; then
    cp -r "$SOURCE_DIR/"* "$TARGET_DIR/"
    echo "Injected built-ins from $SOURCE_DIR to $TARGET_DIR"
else
    echo "Source directory $SOURCE_DIR does not exist. No built-ins injected."
fi