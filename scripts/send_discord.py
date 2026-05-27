import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

# ===== Webhook URLs from environment =====
WEBHOOK_AI   = os.environ["DISCORD_WEBHOOK_AI"]
WEBHOOK_SPORT = os.environ["DISCORD_WEBHOOK_SPORT"]
WEBHOOK_BIZ  = os.environ["DISCORD_WEBHOOK_BIZ"]
WEBHOOK_CULTURE = os.environ["DISCORD_WEBHOOK_CULTURE"]

# ===== Map: emoji prefix → webhook =====
SECTION_MAP = {
    "\U0001f916": WEBHOOK_AI,      # 🤖
    "⚽":     WEBHOOK_SPORT,   # ⚽
    "\U0001f4c8": WEBHOOK_BIZ,     # 📈
    "\U0001f3ad": WEBHOOK_CULTURE, # 🎭
}

# ===== Thai date helper =====
THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน",
    "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
    "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]

def thai_date(dt: datetime) -> str:
    return f"{dt.day} {THAI_MONTHS[dt.month]} {dt.year + 543}"

# ===== Find latest summary file =====
def get_latest_file() -> Path:
    summaries = sorted(Path("summaries").glob("*.md"), reverse=True)
    if not summaries:
        raise FileNotFoundError("ไม่พบไฟล์ใน summaries/")
    return summaries[0]

# ===== Parse sections by leading emoji =====
def parse_sections(text: str) -> dict[str, str]:
    """
    แยก content ตาม section โดยดูว่า line เริ่มต้นด้วย emoji ที่รู้จักไหม
    คืน dict: {emoji: content_string}
    """
    sections: dict[str, str] = {}
    current_emoji = None
    current_lines: list[str] = []

    for line in text.splitlines():
        matched = None
        for emoji in SECTION_MAP:
            if line.startswith(emoji) or line.startswith(f"## {emoji}") or line.startswith(f"# {emoji}"):
                matched = emoji
                break

        if matched:
            # บันทึก section เก่า
            if current_emoji and current_lines:
                sections[current_emoji] = "\n".join(current_lines).strip()
            current_emoji = matched
            current_lines = [line]
        else:
            if current_emoji is not None:
                current_lines.append(line)

    # บันทึก section สุดท้าย
    if current_emoji and current_lines:
        sections[current_emoji] = "\n".join(current_lines).strip()

    return sections

# ===== Send to Discord via curl =====
def send_discord(webhook_url: str, title: str, description: str) -> None:
    payload = {
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": 5814783,
            }
        ]
    }
    payload_json = json.dumps(payload, ensure_ascii=False)

    result = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
         "-X", "POST",
         "-H", "Content-Type: application/json",
         "-d", payload_json,
         webhook_url],
        capture_output=True,
        text=True,
    )
    status = result.stdout.strip()
    if status not in ("200", "204"):
        print(f"  ⚠️  HTTP {status} — {result.stderr.strip()}")
    else:
        print(f"  ✅  HTTP {status}")

# ===== Section titles =====
SECTION_TITLES = {
    "\U0001f916": "\U0001f916 AI & เทคโนโลยี",
    "⚽":     "⚽ กีฬา",
    "\U0001f4c8": "\U0001f4c8 ธุรกิจ & หุ้น",
    "\U0001f3ad": "\U0001f3ad วัฒนธรรม & ไลฟ์สไตล์",
}

# ===== Main =====
def main():
    file = get_latest_file()
    print(f"📄 อ่านไฟล์: {file}")

    # แปลงวันที่จากชื่อไฟล์
    date_str = file.stem          # "2026-05-27"
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    date_th = thai_date(dt)

    content = file.read_text(encoding="utf-8")
    sections = parse_sections(content)

    print(f"พบ {len(sections)} section: {list(sections.keys())}")

    for emoji, webhook in SECTION_MAP.items():
        if emoji not in sections:
            print(f"  ⚠️  ไม่พบ section {emoji} — ข้ามไป")
            continue

        title = SECTION_TITLES[emoji]
        body  = f"\U0001f4c5 **{date_th}**\n\n{sections[emoji]}"
        print(f"ส่ง {title} ...")
        send_discord(webhook, title, body)

    print("เสร็จสิ้น ✨")

if __name__ == "__main__":
    main()
