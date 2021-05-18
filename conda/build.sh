#!/bin/bash

# pip install into the site-packages directory
python -m pip install --target=$PREFIX/lib/python$PY_VER/site-packages --ignore-installed --no-deps -vv .

# Move the entry point script into bin
mkdir $PREFIX/bin
mv $PREFIX/lib/python$PY_VER/site-packages/bin/nexus_streamer $PREFIX/bin
