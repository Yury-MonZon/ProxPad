#!/bin/bash
# Usage: send_warning_msg.sh <message>
IP="192.168.1.250"
PORT=5000
ICON="https://upload.wikimedia.org/wikipedia/commons/1/17/Warning.svg"
TEXT="$*"

if command -v jq &>/dev/null; then
    DATA=$(jq -n --arg t "$TEXT" --arg i "$ICON" --argjson k true '{text: $t, icon: $i, keep: $k}')
else
    TEXT_ESC=$(printf '%s' "$TEXT" | sed 's/"/\\"/g; s/	/\\t/g; s/\n/\\n/g')
    DATA="{\"text\":\"$TEXT_ESC\",\"icon\":\"$ICON\",\"keep\":true}"
fi

curl -s -X POST "http://${IP}:${PORT}/api/popup" \
    -H "Content-Type: application/json" \
    -d "$DATA"

