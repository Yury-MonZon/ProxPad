#!/bin/bash
# Usage: send_slack_msg.sh <message>
IP="192.168.1.250"
ICON="https://upload.wikimedia.org/wikipedia/commons/d/d5/Slack_icon_2019.svg" 
DATA=$(jq -n --arg t "$*" --arg i "$ICON" --argjson k true '{text: $t, icon: $i, keep: $k}')
curl -s -X POST "http://${IP}:5000/api/popup" \
    -H "Content-Type: application/json" \
    -d "$DATA"

