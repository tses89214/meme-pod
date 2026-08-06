#!/bin/bash
# quick_meme_remote.sh — 在 cjs-dev（8 core/15GB，比這台 Pi 快很多）跑 quick_meme.py
# 純 CPU 算圖（PIL 字型繪製），不需要瀏覽器/display，適合丟遠端算。
# fonts/ 已經一次性同步過去（638MB），這裡每次只同步小檔（程式碼 + 產出圖）。
#
# 用法: ./quick_meme_remote.sh "<句子>"
set -euo pipefail

TEXT="$1"
REMOTE="root@cjs-dev"
REMOTE_DIR="/home/tses89214/meme-pod"
LOCAL_DIR="/home/tses89214/meme-pod"

if ssh -o BatchMode=yes -o ConnectTimeout=5 "$REMOTE" true 2>/dev/null; then
    rsync -az "$LOCAL_DIR/design_generator.py" "$LOCAL_DIR/quick_meme.py" "$REMOTE:$REMOTE_DIR/"
    ssh "$REMOTE" "cd $REMOTE_DIR && python3 quick_meme.py \"$TEXT\""
    rsync -az "$REMOTE:$REMOTE_DIR/output/" "$LOCAL_DIR/output/"
    rsync -az "$REMOTE:$REMOTE_DIR/.last_meme_session.json" "$LOCAL_DIR/.last_meme_session.json"
else
    echo "cjs-dev 連不上，改本機跑" >&2
    cd "$LOCAL_DIR" && python3 quick_meme.py "$TEXT"
fi
