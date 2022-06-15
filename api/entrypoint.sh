#!/bin/bash

# Start the first(autorun) process
python3 autorun.py &

# Start the second(flask app) process
python3 app.py