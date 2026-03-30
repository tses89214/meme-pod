#!/usr/bin/env python3
"""
drive_upload.py — 上傳設計檔案到 Google Drive 並取得分享連結

使用方式：
  python drive_upload.py auth          # 取得授權 URL（第一次）
  python drive_upload.py auth CODE     # 用授權碼換 token
  python drive_upload.py upload 1      # 上傳第 1 組（Anton）的 3 個版本
"""

import sys
import json
import re
import pickle
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / ".last_meme_session.json"
TOKEN_FILE = BASE_DIR / ".drive_token.pickle"
SECRETS_FILE = Path("/home/tses89214/ambient-pipeline/client_secrets.json")

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
FOLDER_NAME = "meme-pod-designs"
VERIFIER_FILE = BASE_DIR / ".drive_verifier.txt"


def get_auth_url():
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(
        str(SECRETS_FILE),
        scopes=SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )
    # 儲存 code verifier 供 exchange 用
    if flow.code_verifier:
        VERIFIER_FILE.write_text(flow.code_verifier)
    return flow, auth_url


def exchange_code(code: str):
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(
        str(SECRETS_FILE),
        scopes=SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"
    )
    # 還原 code verifier
    if VERIFIER_FILE.exists():
        flow.code_verifier = VERIFIER_FILE.read_text().strip()
    flow.fetch_token(code=code)
    creds = flow.credentials
    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)
    print("✅ 授權成功，token 已儲存")
    return creds


def load_creds():
    if not TOKEN_FILE.exists():
        return None
    with open(TOKEN_FILE, "rb") as f:
        creds = pickle.load(f)
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
    return creds


def get_or_create_folder(service, name: str, parent_id: str = None) -> str:
    """取得或建立指定名稱的資料夾，回傳 folder_id。"""
    q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    results = service.files().list(q=q, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    body = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        body["parents"] = [parent_id]
    folder = service.files().create(body=body, fields="id").execute()
    return folder["id"]


def upload_file(service, file_path: Path, folder_id: str, mimetype: str = "image/png",
                filename: str = None) -> str:
    from googleapiclient.http import MediaFileUpload
    media = MediaFileUpload(str(file_path), mimetype=mimetype, resumable=True)
    file_meta = {"name": filename or file_path.name, "parents": [folder_id]}
    result = service.files().create(
        body=file_meta, media_body=media, fields="id"
    ).execute()
    file_id = result["id"]

    # 設為任何人皆可檢視
    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"}
    ).execute()

    return f"https://drive.google.com/file/d/{file_id}/view"


def cmd_auth():
    _, auth_url = get_auth_url()
    print("\n請在瀏覽器開啟以下連結，完成授權後把授權碼貼回來：\n")
    print(auth_url)
    print("\n授權後執行：python drive_upload.py auth <授權碼>")


def cmd_exchange(code: str):
    exchange_code(code.strip())


def cmd_upload(font_idx: int):
    creds = load_creds()
    if not creds:
        print("❌ 請先執行授權：python drive_upload.py auth")
        sys.exit(1)

    from googleapiclient.discovery import build
    service = build("drive", "v3", credentials=creds)

    with open(SESSION_FILE) as f:
        session = json.load(f)

    chosen = session["sets"][font_idx]
    font_name = session["fonts"][font_idx].upper()
    text = session["text"].replace("*", "").replace("/n", " ").strip()
    print(f"\n🎨 字體: {font_name} | 文字: {text}")

    root_id = get_or_create_folder(service, FOLDER_NAME)

    # 每個設計一個子資料夾
    folder_name = re.sub(r'[^\w\s\-]', '', text)[:40].strip()
    folder_id = get_or_create_folder(service, folder_name, parent_id=root_id)
    print(f"📁 子資料夾：{folder_name}")

    links = {}
    for variant, path_str in chosen.items():
        p = Path(path_str)
        if not p.exists():
            print(f"  ⚠️  找不到：{p.name}")
            continue
        print(f"  ⬆️  上傳 {variant}...", end=" ", flush=True)
        url = upload_file(service, p, folder_id)
        links[variant] = url
        p.unlink(missing_ok=True)
        print(url)

    # 刪除預覽圖
    preview = BASE_DIR / "output" / "_preview_grid_latest.png"
    preview.unlink(missing_ok=True)

    print(f"\n✅ 上傳完成！")
    return links


def build_meta_json(meta: dict) -> str:
    """從 metadata 產生 meta.json 內容（含多語言）。"""
    output = {
        "font": meta.get("font", "").upper(),
        "translations": meta.get("translations", {}),
    }
    if not output["translations"]:
        output["title"] = meta.get("title", "")
        output["description"] = meta.get("description", "")
        output["tags"] = meta.get("tags", [])
    return json.dumps(output, ensure_ascii=False, indent=2)


def cmd_batch():
    """批量上傳 .upload_queue.json 中所有設計。"""
    queue_file = BASE_DIR / ".upload_queue.json"
    if not queue_file.exists():
        print("❌ 找不到 .upload_queue.json")
        sys.exit(1)

    with open(queue_file) as f:
        queue = json.load(f)

    meta_file = BASE_DIR / "upload_metadata.json"
    metadata = []
    if meta_file.exists():
        with open(meta_file) as f:
            metadata = json.load(f)

    if not queue:
        print("✅ 隊列是空的")
        return

    creds = load_creds()
    if not creds:
        print("❌ 請先執行授權：python drive_upload.py auth")
        sys.exit(1)

    from googleapiclient.discovery import build
    service = build("drive", "v3", credentials=creds)

    root_id = get_or_create_folder(service, FOLDER_NAME)
    print(f"📁 根資料夾：{FOLDER_NAME}\n")

    all_links = []
    for item in queue:
        text = item["text"].replace("*", "").replace("/n", " ").strip()
        font = item["font"].upper()
        font_idx = item["font_idx"] - 1  # 0-based

        print(f"🎨 {text} — {font}")

        # 重新生成此設計的檔案
        import subprocess
        result = subprocess.run(
            ["python", "quick_meme.py", item["text"]],
            cwd=BASE_DIR, capture_output=True, text=True
        )

        # 讀取 session 取得路徑
        with open(BASE_DIR / ".last_meme_session.json") as f:
            session = json.load(f)

        chosen = session["sets"][font_idx]
        folder_name = re.sub(r'[^\w\s\-]', '', text)[:40].strip()
        folder_id = get_or_create_folder(service, folder_name, parent_id=root_id)

        links = {}
        for variant, path_str in chosen.items():
            p = Path(path_str)
            if not p.exists():
                print(f"  ⚠️  找不到：{p.name}")
                continue
            print(f"  ⬆️  {variant}...", end=" ", flush=True)
            url = upload_file(service, p, folder_id)
            links[variant] = url
            p.unlink(missing_ok=True)
            print("✓")

        # 刪除預覽圖
        preview = BASE_DIR / "output" / "_preview_grid_latest.png"
        preview.unlink(missing_ok=True)

        # 上傳 meta.txt（含多語言 metadata）
        meta_entry = next((m for m in metadata if m.get("text") == item["text"]), None)
        if meta_entry:
            tmp_path = BASE_DIR / "_tmp_meta.json"
            tmp_path.write_text(build_meta_json(meta_entry), encoding="utf-8")
            print(f"  ⬆️  meta.json...", end=" ", flush=True)
            upload_file(service, tmp_path, folder_id, mimetype="application/json", filename="meta.json")
            tmp_path.unlink()
            print("✓")

        all_links.append({"text": text, "font": font, "links": links})
        print()

    # 清空隊列
    queue_file.write_text("[]", encoding="utf-8")

    print(f"✅ 批量上傳完成，共 {len(all_links)} 組")
    return all_links


def cmd_upload_meta_only():
    """只上傳 meta.txt 到已存在的 Drive 子資料夾（不重新上傳圖片）。"""
    meta_file = BASE_DIR / "upload_metadata.json"
    if not meta_file.exists():
        print("❌ 找不到 upload_metadata.json")
        sys.exit(1)
    with open(meta_file) as f:
        metadata = json.load(f)

    creds = load_creds()
    if not creds:
        print("❌ 請先執行授權：python drive_upload.py auth")
        sys.exit(1)

    from googleapiclient.discovery import build
    service = build("drive", "v3", credentials=creds)

    root_id = get_or_create_folder(service, FOLDER_NAME)
    print(f"📁 根資料夾：{FOLDER_NAME}\n")

    for meta in metadata:
        text = meta.get("text", "").replace("*", "").replace("/n", " ").strip()
        folder_name = re.sub(r'[^\w\s\-]', '', text)[:40].strip()
        folder_id = get_or_create_folder(service, folder_name, parent_id=root_id)
        tmp_path = BASE_DIR / "_tmp_meta.json"
        tmp_path.write_text(build_meta_json(meta), encoding="utf-8")
        print(f"  ⬆️  {folder_name}/meta.json...", end=" ", flush=True)
        upload_file(service, tmp_path, folder_id, mimetype="application/json", filename="meta.json")
        tmp_path.unlink()
        print("✓")

    print(f"\n✅ meta.json 上傳完成，共 {len(metadata)} 組")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""

    if cmd == "auth":
        if len(sys.argv) > 2:
            cmd_exchange(sys.argv[2])
        else:
            cmd_auth()
    elif cmd == "upload":
        idx = int(sys.argv[2]) - 1 if len(sys.argv) > 2 else 0
        cmd_upload(idx)
    elif cmd == "batch":
        cmd_batch()
    elif cmd == "upload-meta":
        cmd_upload_meta_only()
    else:
        print(__doc__)
