import json
import os
import subprocess
import sys
from glob import glob
from datetime import datetime

# หาไฟล์ข่าวล่าสุด
files = sorted(glob("summaries/*.md"), reverse=True)
if not files:
    print("ไม่พบไฟล์ข่าว")
    sys.exit(1)

filename = os.path.basename(files[0])
date_str = filename.replace(".md", "")

# แปลงวันที่เป็นภาษาไทย
try:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    thai_months = ["","มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน",
                   "กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ธันวาคม"]
    date_th = f"{dt.day} {thai_months[dt.month]} {dt.year + 543}"
except:
    date_th = date_str

with open(files[0], encoding="utf-8") as f:
    content = f.read()

WEBHOOK_AI    = os.environ.get("WEBHOOK_AI", "")
WEBHOOK_SPORT = os.environ.get("WEBHOOK_SPORT", "")
WEBHOOK_BIZ   = os.environ.get("WEBHOOK_BIZ", "")

# แยก section แบบ line-by-line (แม่นกว่า regex กับ emoji)
def split_sections(text):
    buckets = {"ai": [], "sport": [], "biz": []}
    current = None

    for line in text.splitlines():
        s = line.strip()
        if s.startswith("\U0001f916"):    # 🤖
            current = "ai"
        elif s.startswith("⚽"):      # ⚽
            current = "sport"
        elif s.startswith("\U0001f4c8"):  # 📈
            current = "biz"
        elif s.startswith("\U0001f50d") or s.startswith("---"):  # 🔍 หรือ ---
            current = None

        if current:
            buckets[current].append(line)

    return {k: "\n".join(v).strip() for k, v in buckets.items()}

sections = split_sections(content)

def send(text, webhook, color, title):
    if not text or not webhook:
        print(f"Skipping {title} (no content or webhook)")
        return
    payload = json.dumps({
        "embeds": [{
            "title": f"{title}",
            "description": f"📅 **{date_th}**\n\n{text[:3800]}",
            "color": color,
            "footer": {"text": "Daily Update by Claude"}
        }]
    })
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", webhook,
         "-H", "Content-Type: application/json",
         "-d", payload],
        capture_output=True, text=True
    )
    print(f"{title}: {result.stdout or result.stderr}")

send(sections.get("ai",""),    WEBHOOK_AI,    5765993,  "🤖 AI & เทคโนโลยี")
send(sections.get("sport",""), WEBHOOK_SPORT, 5763719,  "⚽ กีฬา")
send(sections.get("biz",""),   WEBHOOK_BIZ,   16766720, "📈 ธุรกิจ & หุ้น")

print("Done!")
