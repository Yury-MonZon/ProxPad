#!/usr/bin/env bash
# Restart proxpad.py: kill running process and start again

PROC_NAME="proxpad.py"

# Find and kill running process
PID=$(pgrep -f "$PROC_NAME")
echo $PID
if [ -n "$PID" ]; then
    echo "Killing $PROC_NAME (PID: $PID)"
    kill $PID
    sleep 1
else
    echo "$PROC_NAME not running."
fi

bash /root/ProxPad/run_me.sh
echo "$PROC_NAME restarted."