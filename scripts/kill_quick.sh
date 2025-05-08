#!/bin/bash
# filepath: c:\Users\pmari\Documents\GitHub\Webapp-PCTO\scripts\kill_quick.sh

# Updated program names in the specified order
PROGRAM_NAMES=("log_server.py" "auth_server.py" "api_server.py")

for PROGRAM_NAME in "${PROGRAM_NAMES[@]}"; do
    # Find and kill processes by name
    PIDS=$(pgrep -f "$PROGRAM_NAME")

    if [ -z "$PIDS" ]; then
        echo "No processes found with name: $PROGRAM_NAME"
        continue
    fi

    echo "Killing processes with name: $PROGRAM_NAME"
    for PID in $PIDS; do
        echo "Killing PID: $PID"
        kill -9 $PID
    done

    echo "All processes with name $PROGRAM_NAME have been terminated."
done

# Delete the rate_limit.json file if it exists
RATE_LIMIT_FILE="../rate_limit.json"
if [ -f "$RATE_LIMIT_FILE" ]; then
    rm -f "$RATE_LIMIT_FILE"
    echo "rate_limit.json file deleted."
else
    echo "rate_limit.json file not found."
fi