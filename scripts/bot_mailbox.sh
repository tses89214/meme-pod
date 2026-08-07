#!/bin/bash
# Send/read messages on the shared bot-mailbox chatroom file.
# See ~/.claude/bot-mailbox/README.md for the convention.
# Logic copied from pi-admin/scripts/bot_mailbox.sh, SELF changed to meme-pod.
set -euo pipefail

MAILBOX_DIR="$HOME/.claude/bot-mailbox"
CHAT_FILE="$MAILBOX_DIR/chat.jsonl"
SELF="meme-pod"
CURSOR_FILE="$MAILBOX_DIR/.cursor-$SELF"

usage() {
    echo "Usage: $0 send <to> <message>" >&2
    echo "       $0 read" >&2
    exit 1
}

json_escape() {
    python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1"
}

cmd_send() {
    local to="$1" message="$2"
    local ts
    ts=$(date -Iseconds)
    local line
    line=$(printf '{"from":%s,"to":%s,"ts":%s,"message":%s}' \
        "$(json_escape "$SELF")" "$(json_escape "$to")" "$(json_escape "$ts")" "$(json_escape "$message")")
    mkdir -p "$MAILBOX_DIR"
    (
        flock -x 200
        echo "$line" >> "$CHAT_FILE"
    ) 200>"$MAILBOX_DIR/.lock"
}

cmd_read() {
    local last=0
    [ -f "$CURSOR_FILE" ] && last=$(cat "$CURSOR_FILE")
    [ -f "$CHAT_FILE" ] || { echo "(no messages yet)"; return; }

    local total
    total=$(wc -l < "$CHAT_FILE")
    if [ "$total" -gt "$last" ]; then
        tail -n "+$((last + 1))" "$CHAT_FILE" | grep -E "\"to\":[[:space:]]*\"($SELF|all)\"" || true
    fi
    echo "$total" > "$CURSOR_FILE"
}

case "${1:-}" in
    send) [ $# -eq 3 ] || usage; cmd_send "$2" "$3" ;;
    read) cmd_read ;;
    *) usage ;;
esac
