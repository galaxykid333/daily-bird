import json
import re

LOG_FILE = "/Users/chloecheng/PycharmProjects/daily-bird/scripts/update_log.txt"  # the pasted text saved as a file
JSON_FILE = "/Users/chloecheng/PycharmProjects/daily-bird/src/data/range_maps.json"

# --- Parse the log file ---
with open(LOG_FILE, "r", encoding="utf-8") as f:
    log_text = f.read()

# Match lines like: [    1/3648] Atitlán grebe                → ['GT']
# Skip lines with "(no codes returned)" or "checkpoint saved"
pattern = re.compile(
    r"^\[.*?\]\s+(.+?)\s{2,}→\s+\[(.+?)\]\s*$",
    re.MULTILINE,
)

updates = {}
for m in pattern.finditer(log_text):
    bird_name = m.group(1).strip()
    codes_raw = m.group(2)
    # Parse the country codes: 'GT', 'US', ...
    codes = [c.strip().strip("'\"") for c in codes_raw.split(",")]
    updates[bird_name] = codes

print(f"Parsed {len(updates)} entries with country codes from log.")

# --- Load and update the JSON ---
with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

matched = 0
unmatched = []

for bird_name, codes in updates.items():
    if bird_name in data:
        data[bird_name]["countries"] = codes
        matched += 1
    else:
        unmatched.append(bird_name)

print(f"Updated {matched} entries in JSON.")
if unmatched:
    print(f"{len(unmatched)} entries not found in JSON:")
    for name in unmatched:
        print(f"  - {name}")

# --- Write back ---
with open(JSON_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Saved updated {JSON_FILE}.")
