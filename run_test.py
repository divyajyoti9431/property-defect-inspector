# -*- coding: utf-8 -*-
"""
Test runner - submits 6 BD3 sample images to the running API,
generates a PDF report, and saves it to reports/test_report.pdf
"""
import sys
import os
import shutil
from pathlib import Path

# Force UTF-8 output on Windows and log to file
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Tee output to log file
import io
class Tee:
    def __init__(self, *streams): self.streams = streams
    def write(self, data):
        for s in self.streams: s.write(data)
    def flush(self):
        for s in self.streams: s.flush()

_log = open("test_run.log", "w", encoding="utf-8")
sys.stdout = Tee(sys.__stdout__, _log)

BASE_URL = "http://localhost:8001"

# ── 1. Map downloaded WebFetch images to friendly names ──────────
TEMP_DIR = Path(r"C:\Users\divya\.claude\projects\C--Users-divya-OBJECT-DETECTION\e526de47-a8b5-42c7-939a-4f06bb140ef7\tool-results")

# NoBroker Indiranagar, Bangalore flat images (real property photos)
IMAGE_MAP = {
    "01_bedroom.jpg":     "webfetch-1774022749112-21wvcg.jpg",
    "02_kitchen.jpg":     "webfetch-1774022757678-etdpm0.jpg",
    "03_living_room.jpg": "webfetch-1774022766826-lo769t.jpg",
}

# ── 2. Copy images into project test_images/ folder ──────────────
TEST_DIR = Path("test_images")
TEST_DIR.mkdir(exist_ok=True)

print("[STEP 1] Copying sample images into test_images/")
copied = []
for name, src_name in IMAGE_MAP.items():
    src = TEMP_DIR / src_name
    dst = TEST_DIR / name
    if src.exists():
        shutil.copy2(src, dst)
        copied.append(dst)
        print(f"   OK  {name}")
    else:
        print(f"   MISSING: {src_name}")

if not copied:
    print("ERROR: No images found. Aborting.")
    sys.exit(1)

print(f"\n{len(copied)} images ready\n")

# ── 3. POST /api/analyze ─────────────────────────────────────────
import requests

print("[STEP 2] Submitting images to /api/analyze ...")
print("         Claude Opus 4.6 is analyzing each image - please wait\n")

files_payload = [
    ("files", (p.name, open(p, "rb"), "image/jpeg"))
    for p in copied
]
data_payload = {
    "property_address": "No. 47, 3rd Cross, Indiranagar, Bangalore, Karnataka 560038",
    "agent_name":       "Rajesh Kumar (NoBroker Realty Pvt. Ltd., Bangalore)",
    "owner_name":       "Mr. Suresh Venkataraman",
    "inspection_date":  "2026-03-20",
    "unit_number":      "Flat 302, Block B",
}

resp = requests.post(
    f"{BASE_URL}/api/analyze",
    data=data_payload,
    files=files_payload,
    timeout=300,
)

if resp.status_code != 200:
    print(f"ERROR {resp.status_code}: {resp.text}")
    sys.exit(1)

session     = resp.json()
session_id  = session["session_id"]
results     = session.get("results", [])

print(f"[OK] Analysis complete!  Session ID: {session_id[:8]}...\n")
print("=" * 65)

total = major = moderate = minor = 0

for r in results:
    fname    = r["filename"]
    analysis = r.get("analysis", {})
    defects  = analysis.get("defects", [])
    cond     = analysis.get("overall_condition", "unknown").upper()
    summary  = analysis.get("summary", "")

    print(f"\n[IMAGE] {fname}  |  Condition: {cond}")
    print(f"        {summary}")

    if defects:
        for d in defects:
            sev  = d.get("severity", "minor").upper()
            cat  = d.get("category", "")
            desc = d.get("description", "")
            act  = d.get("action_required", "")
            print(f"  [{sev:8s}] {cat}")
            print(f"             {desc}")
            print(f"             Action: {act}")
            total += 1
            if sev == "MAJOR":        major += 1
            elif sev == "MODERATE":   moderate += 1
            else:                     minor += 1
    else:
        print("  --> No defects detected")

print("\n" + "=" * 65)
print(f"\n[SUMMARY]  Total Defects={total}  |  Major={major}  Moderate={moderate}  Minor={minor}")
print(f"           Images Analyzed={len(results)}")

# ── 4. Generate PDF ───────────────────────────────────────────────
print("\n[STEP 3] Generating PDF report ...")
resp2 = requests.post(
    f"{BASE_URL}/api/generate-report",
    json={"session_id": session_id},
    timeout=60,
)

if resp2.status_code == 200:
    result2  = resp2.json()
    dl_url   = f"{BASE_URL}{result2['download_url']}"

    pdf_resp = requests.get(dl_url, timeout=30)
    out_path = Path("reports") / "test_report.pdf"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_bytes(pdf_resp.content)

    print(f"[OK] PDF saved  -->  {out_path.resolve()}")
    print(f"[OK] Download   -->  {dl_url}")
    print("\nDONE - Open reports/test_report.pdf to view the inspection report.")
else:
    print(f"PDF ERROR {resp2.status_code}: {resp2.text}")
