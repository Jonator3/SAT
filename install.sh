#!/bin/bash
venv_dir=venv
python3 -m venv $venv_dir
source $venv_dir/bin/activate
pip install -r requirements.txt
