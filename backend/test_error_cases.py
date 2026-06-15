"""
test_error_cases.py — Verifies that the refactored API returns proper error messages
for invalid uploads instead of crashing or returning mock data.

Run from project root:
    python backend/test_error_cases.py
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import requests
import pandas as pd

BASE = "http://localhost:8000/api/reports/upload"
FORM = {"dept": "CSE", "year": "3rd", "sem": "5", "section": "A",
        "faculty_advisor_name": "Dr. Test", "batch": "", "exam_date": ""}


def upload(label, buf, filename="test.xlsx"):
    buf.seek(0)
    files = {"file": (filename, buf,
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = requests.post(BASE, files=files, data=FORM)
    ok = "Upload Error" in r.text or r.status_code != 200
    tag = "[PASS]" if ok else "[FAIL]"
    print(f"  {tag}  {label} — HTTP {r.status_code}")
    if not ok:
        print(f"         Expected error, got success ({len(r.text)} chars)")
    return r


def make_excel(data: dict) -> io.BytesIO:
    buf = io.BytesIO()
    pd.DataFrame(data).to_excel(buf, index=False, engine="openpyxl")
    return buf


print("\n=== Error-handling tests ===\n")

# Case 1 — No Reg.No / Name columns (irrelevant file)
print("[1] File with no Reg.No/Name header:")
upload("Irrelevant column names", make_excel({"ColA": [1, 2], "ColB": [3, 4]}))

# Case 2 — Valid header but zero student rows
print("[2] Valid header, no student rows:")
upload("Empty student list", make_excel({"Reg.No": [], "Name": [], "Maths": []}))

# Case 3 — Header + students but NO subject columns (only blacklisted cols)
print("[3] No subject columns (only CGPA/SGPA after Name):")
upload("Only summary columns", make_excel({
    "Reg.No": ["RA001"], "Name": ["Alice"],
    "CGPA": ["8.5"], "SGPA": ["8.0"], "No. of subjects fail": ["0"]
}))

# Case 4 — Wrong file extension
print("[4] Wrong file extension (.csv):")
buf = io.BytesIO(b"Reg.No,Name,Maths\nRA001,Alice,95\n")
r = requests.post(BASE, files={"file": ("test.csv", buf, "text/csv")}, data=FORM)
ok = r.status_code != 200 or "Upload Error" in r.text
print(f"  {'[PASS]' if ok else '[FAIL]'}  CSV rejected — HTTP {r.status_code}")

print("\n=== Done ===")
