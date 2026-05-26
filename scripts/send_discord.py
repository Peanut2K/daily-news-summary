import re
import json
import os
import subprocess
import sys
from glob import glob

# หาไฟล์ข่าวล่าสุด
files = sorted(glob("summaries/*.md"), reverse=True)
if not files:
    print("ไม่พบไฟล์ข่าว")
    sys.exit(1)

with open(files[0], encoding="utf-8") as f:
    content = f.read()

WEBHOOK_AI    = os.environ.get("WEBHOOK_AI", "")
WEBHOOK_SPORT = os.environ.get("WEBHOOK_SPORT", "")
WEBHOOK_BIZ   = os.environ.get("WEBHOOK_BIZ", "")

def extract(text, start, ends):
    pattern = start + r"[^\n]*\n.*?(?=" + "|".join(ends) + r"|$)"
    m = re.search(pattern, text, re.DOTALL)
    return m.group(0).strip() if m else ""

ai    = extract(content, "\U0001f916", [r"\n⚽", r"\n\U0001f4c8", r"\n\U0001f50d"])
sport = extract(content, "⚽",     [r"\n\U0001f4c8", r"\n\U0001f50d"])
biz   = extract(content, "\U0001f4c8", [r"\n\U0001f50d"])

def send(section_text, webhook, color):
    if not section_text or not webhook:
        return
    payload = json.dumps({
        "embeds": [{"description": section_text[:3900], "color": color}]
    })
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", webhook,
         "-H", "Content-Type: application/json",
         "-d", payload],
        capture_output=True, text=True
    )
    print(f"Response: {result.stdout}")

send(ai,    WEBHOOK_AI,    5765993)   # น้ำเงิน
send(sport, WEBHOOK_SPORT, 5763719)   # เขียว
send(biz,   WEBHOOK_BIZ,   16766720)  # เหลือง

print("Done!")
