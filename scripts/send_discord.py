import os
import json
import re
import urllib.request
import urllib.error
from glob import glob

# หาไฟล์ล่าสุด
files = sorted(glob("summaries/*.md"), reverse=True)
if not files:
    print("ไม่พบไฟล์ข่าว")
    exit(1)

with open(files[0], encoding="utf-8") as f:
    content = f.read()

webhook = os.environ["DISCORD_WEBHOOK"]

# หัวข้อวันที่ (บรรทัดแรก)
title_line = content.split("\n")[0].strip()

# แยก 3 section ด้วย emoji
def extract_section(text, start_emoji, end_emojis):
    pattern = rf"({re.escape(start_emoji)}[^\n]*\n)(.*?)(?={'|'.join(re.escape(e) for e in end_emojis)}|$)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return None, None
    header = match.group(1).strip()
    body = match.group(2).strip()
    return header, body

ai_header, ai_body       = extract_section(content, "🤖", ["⚽", "📈", "🔍"])
sport_header, sport_body = extract_section(content, "⚽", ["📈", "🔍"])
biz_header, biz_body     = extract_section(content, "📈", ["🔍"])

embeds = []

if ai_header and ai_body:
    embeds.append({
        "title": ai_header,
        "description": ai_body[:4000],
        "color": 0x5865F2   # Discord Blurple
    })

if sport_header and sport_body:
    embeds.append({
        "title": sport_header,
        "description": sport_body[:4000],
        "color": 0x57F287   # Green
    })

if biz_header and biz_body:
    embeds.append({
        "title": biz_header,
        "description": biz_body[:4000],
        "color": 0xFEE75C   # Yellow
    })

payload = json.dumps({
    "content": f"## {title_line}",
    "embeds": embeds
}).encode("utf-8")

req = urllib.request.Request(
    webhook,
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    res = urllib.request.urlopen(req)
    print(f"✅ ส่ง Discord สำเร็จ: {res.status}")
except urllib.error.HTTPError as e:
    print(f"❌ Error {e.code}: {e.read().decode()}")
    exit(1)