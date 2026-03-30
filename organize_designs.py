#!/usr/bin/env python3
"""
organize_designs.py — 依設計整理成資料夾結構
每個設計：output/<設計名稱>/ + 圖片 + meta.txt

使用方式：
  python organize_designs.py
"""

import json
import re
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
QUEUE_FILE = BASE_DIR / ".upload_queue.json"
META_FILE = BASE_DIR / "upload_metadata.json"

with open(QUEUE_FILE) as f:
    queue = json.load(f)

with open(META_FILE) as f:
    metadata = json.load(f)

# 需要重新生成各設計的圖檔路徑（從 session 重跑）
import subprocess

for i, (item, meta) in enumerate(zip(queue, metadata)):
    text = item["text"]
    font = item["font"]
    font_idx = item["font_idx"] - 1  # 0-based

    # 資料夾名稱
    folder_name = re.sub(r'[^\w\s\-]', '', meta["title"])[:50].strip()
    folder_name = re.sub(r'\s+', '_', folder_name)
    design_dir = OUTPUT_DIR / folder_name
    design_dir.mkdir(exist_ok=True)

    # 重新生成取得最新路徑
    subprocess.run(["python", "quick_meme.py", text], cwd=BASE_DIR,
                   capture_output=True, text=True)

    with open(BASE_DIR / ".last_meme_session.json") as f:
        session = json.load(f)

    chosen = session["sets"][font_idx]
    font_name = session["fonts"][font_idx]

    # 複製圖片到資料夾（black = 淺色衣服用，white = 深色衣服用）
    for variant, src_path in chosen.items():
        src = Path(src_path)
        if src.exists():
            label = "for_light_shirt.png" if variant == "black" else "for_dark_shirt.png"
            dst = design_dir / label
            shutil.copy2(src, dst)

    # 寫入 meta.json
    meta_json = design_dir / "meta.json"
    output = {
        "font": font.upper(),
        "translations": meta.get("translations", {}),
    }
    if not output["translations"]:
        output["title"] = meta.get("title", "")
        output["description"] = meta.get("description", "")
        output["tags"] = meta.get("tags", [])
    with open(meta_json, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ {folder_name}/")
    print(f"   for_light_shirt.png / for_dark_shirt.png / meta.json")

print(f"\n✅ 完成！位於 {OUTPUT_DIR}")
