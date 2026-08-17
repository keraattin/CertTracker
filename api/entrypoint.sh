#!/bin/sh

# Start the first(autorun) process
python3 autorun.py &

# Start the second(flask app) process
# Served by waitress, a production WSGI server. The Flask development
# server in app.py is only used when running app.py directly.
waitress-serve --host=0.0.0.0 --port="${PORT}" app:app
