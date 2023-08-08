#!/bin/bash

# Create and activate venv.
python3 -m venv env 
source env/bin/activate

# Set up submodule and requirements.
pip3 --default-timeout=1000 install -r requirements.txt
