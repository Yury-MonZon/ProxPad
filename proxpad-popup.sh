#!/bin/bash
# ProxPad Popup - Send notification popups to ProxPad web interface
#
# Usage:
#   proxpad-popup.sh -t "Your message" [-i icon] [-k] [-u host]
#
# Options:
#   -t TEXT     Popup message text (required)
#   -i ICON     Bootstrap icon name or image URL (default: info-circle)
#   -k          Keep popup until user taps (otherwise auto-dismiss after 10s)
#   -u HOST     ProxPad server host/IP (default: localhost)
#
# Examples:
#   proxpad-popup.sh -t "Hello World!"
#   proxpad-popup.sh -t "Backup done" -i check-circle -k
#   proxpad-popup.sh -t "Alert" -i "https://example.com/warning.png" -k
#   ssh user@host /path/to/proxpad-popup.sh -t "VM started" -i play-circle

PORT=5000
SERVER_URL="http://localhost:${PORT}"
TEXT=""
ICON="info-circle"
KEEP="false"

while getopts "t:i:ku:" opt; do
    case $opt in
        t) TEXT="$OPTARG" ;;
        i) ICON="$OPTARG" ;;
        k) KEEP="true" ;;
        u) SERVER_URL="http://${OPTARG}:${PORT}" ;;
        *) echo "Usage: $0 -t TEXT [-i ICON] [-k] [-u HOST]" >&2; exit 1 ;;
    esac
done

if [ -z "$TEXT" ]; then
    echo "Error: -t TEXT is required" >&2
    echo "Usage: $0 -t TEXT [-i ICON] [-k] [-u HOST]" >&2
    exit 1
fi

if command -v jq &>/dev/null; then
    DATA=$(jq -n --arg t "$TEXT" --arg i "$ICON" --argjson k "$KEEP" \
        '{text: $t, icon: $i, keep: $k}')
else
    TEXT_ESC=$(printf '%s' "$TEXT" | sed 's/"/\\"/g; s/	/\\t/g; s/\n/\\n/g')
    DATA="{\"text\":\"$TEXT_ESC\",\"icon\":\"$ICON\",\"keep\":$KEEP}"
fi

curl -s -X POST "$SERVER_URL/api/popup" \
    -H "Content-Type: application/json" \
    -d "$DATA"
echo
