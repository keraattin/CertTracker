#!/bin/sh

# Create the schema before anything serves. Both processes below import
# app.py, which calls db.create_all(); against an empty database the two
# of them race, and the loser dies with "table already exists". Doing it
# once up front leaves them nothing to race over.
python3 -c "import app"

# Start the first(autorun) process
python3 autorun.py &

# Start the second(flask app) process
# Served by waitress, a production WSGI server. The Flask development
# server in app.py is only used when running app.py directly.
waitress-serve --host=0.0.0.0 --port="${PORT}" app:app
