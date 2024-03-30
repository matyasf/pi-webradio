#!/usr/bin/env bash
sleep 1
source ./venv/bin/activate
# 2>&1 means to redirect stderr to stdout, so both are written to the log
# -u means that the outputs are unbuffered
python -u main.py >> /home/hudejo/CODE/pi-radio/log.txt 2>&1