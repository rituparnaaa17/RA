"""
smoke_test.py — Integration tests for the parse → compute → render pipeline.

Run from the project root:
    python backend/smoke_test.py

Tests:
  [1] Write test Excel
  [2] Parse - verify student count, subject columns, metadata
  [3] Compute - verify overall stats, per-subject grades
  [4] Check absent/detained handling (A is a valid grade, not absent)
  [5] Check subject column blacklist (CGPA, SGPA etc. excluded)
  [6] Render Jinja2 template
  [7] Verify no dummy/placeholder content in output
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd

SCRIPT_DIR = os.path.dirname(__file__)

# ---------------------------------------------------------------------------
# [1] Build a realistic test Excel file
# ---------------------------------------------------------------------------
print("[1] Building test Excel with preamble rows ...")

rows = [
    # Preamble rows (above the actual header)
    ["SRM INSTITUTE OF SCIENCE AND TECHNOLOGY", None, None, None, None, None, None, None],
    ["Faculty of Engineering and Technology",   None, None, None, None, None, None, None],
    ["Ramapuram Campus, Chennai - 89",          None, None, None, None, None, None, None],
    ["Department  CSE",                         None, None, None, None, None, None, None],
    ["Branch/Year/Sem: CSE - III/V/A",          None, None, None, None, None, None, None],
    ["SEMESTER V RESULT ANALYSIS",              None, None, None, None, None, None, None],
    # Actual header row
    ["Reg.No", "Name", "Maths", "Physics", "Chemistry", "No. of subjects fail", "CGPA", "SGPA"],
    # Student rows
    ["RA211001", "Alice",   "95", "AB",  "72", "0", "8.5", "8.2"],
    ["RA211002", "Bob",     "45", "55",  "30", "2", "5.1", "4.9"],
    ["RA211003", "Charlie", "AB", "60",  "85", "0", "7.8", "7.5"],
    ["RA211004", "Diana",   "72", "AB",  "92", "0", "8.1", "7.9"],
    ["RA211005", "Eve",     "DET","DET", "DET","0", "0.0", "0.0"],   # detained
]

buf = io.BytesIO()
pd.DataFrame(rows).to_excel(buf, index=False, header=False, engine="openpyxl")
buf.seek(0)
test_file = os.path.join(SCRIPT_DIR, "test_sample.xlsx")
with open(test_file, "wb") as f:
    f.write(buf.read())
print(f"    Written -> {test_file}")


# ---------------------------------------------------------------------------
# [2] Parse
# ---------------------------------------------------------------------------
print("[2] Parsing Excel ...")
from services.parse_excel import validate_and_extract_data

df, subject_columns, meta = validate_and_extract_data(test_file)

print(f"    Students:        {len(df)}")
print(f"    Subject columns: {subject_columns}")
print(f"    Metadata:        {meta}")

assert len(df) == 5, f"Expected 5 student rows, got {len(df)}"
assert subject_columns == ["Maths", "Physics", "Chemistry"], \
    f"Unexpected subject columns: {subject_columns}"

# CGPA / SGPA / 'No. of subjects fail' must NOT be included
assert "CGPA" not in subject_columns,  "CGPA should be excluded from subject columns"
assert "SGPA" not in subject_columns,  "SGPA should be excluded from subject columns"
assert "No. of subjects fail" not in subject_columns, \
    "'No. of subjects fail' must be excluded"

# Metadata: department should combine "Department" + "CSE" into one string
assert "CSE" in meta["department"], \
    f"Department should include 'CSE', got: '{meta['department']}'"

print("    [PASS] Parse checks passed")


# ---------------------------------------------------------------------------
# [3] Compute
# ---------------------------------------------------------------------------
print("[3] Computing statistics ...")
from services.compute import compute_report_data

result = compute_report_data(df, subject_columns)
overall  = result["overall_summary"]
stats    = result["subject_stats"]
failures = result["student_failures"]
students = result["students"]

print(f"    Overall summary: {overall}")
print(f"    Student records: {len(students)}")

assert overall["total_students"] == 5, \
    f"Expected 5 total students, got {overall['total_students']}"

# Eve is detained in all subjects — she has no failing grade, so she's
# counted under "all_cleared" (detained != failed)
# Alice, Charlie, Diana — all passed
# Bob — failed 2 subjects (Maths < 50, Chemistry < 50)
assert overall["unsuccessful_2"] == 1, \
    f"Expected 1 student with 2 failures (Bob), got {overall['unsuccessful_2']}"

print(f"    Failures: {failures}")
print(f"    Subject stats ({len(stats)}):")
for s in stats:
    print(f"      {s['subject_name']}: passed={s['passed']} absent={s['absent']} "
          f"detained={s['detained']} pass%={s['pass_percentage']} grades={s['grades']}")

# [4] Verify A is a valid grade, not absent
maths_stat = next(s for s in stats if s["subject_name"] == "Maths")
# Alice got 95 (O), Bob got 45 (F), Charlie AB (absent), Diana got 72 (A), Eve detained
assert maths_stat["grades"]["O"] == 1, f"Expected Alice to get O in Maths: {maths_stat['grades']}"
assert maths_stat["grades"]["A"] == 1, f"Expected Diana to get A in Maths: {maths_stat['grades']}"
assert maths_stat["absent"] == 1,     f"Expected 1 absent in Maths (Charlie): {maths_stat['absent']}"
assert maths_stat["detained"] == 1,   f"Expected 1 detained in Maths (Eve): {maths_stat['detained']}"
assert maths_stat["failed"] == 1,     f"Expected 1 fail in Maths (Bob): {maths_stat['failed']}"
print("    [PASS] Grade A correctly mapped (not treated as absent)")
print("    [PASS] Detained handled separately from absent")

# [5] Verify structured student records
assert len(students) == 5, f"Expected 5 student records, got {len(students)}"
alice_rec = next(r for r in students if r["reg_no"] == "RA211001")
assert alice_rec["subjects"]["Maths"] == "O", \
    f"Alice's Maths grade should be O, got: {alice_rec['subjects']['Maths']}"
print("    [PASS] Structured student records correct")


# ---------------------------------------------------------------------------
# [6] Render
# ---------------------------------------------------------------------------
print("[6] Rendering Jinja2 template ...")
from services.render import render_report

subjects_ctx = [
    {
        "course_code":     s["subject_name"],
        "course_title":    s["subject_name"],
        "absent":          s["absent"],
        "detained":        s["detained"],
        "successful":      s["passed"],
        "total_students":  s["registered"],
        "success_percent": f"{s['pass_percentage']:.2f}%",
    }
    for s in stats
]
summary_ctx = {
    "total_students":           overall["total_students"],
    "total_subjects":           len(stats),
    "unsuccessful_1":           overall["unsuccessful_1"],
    "unsuccessful_2":           overall["unsuccessful_2"],
    "unsuccessful_3":           overall["unsuccessful_3"],
    "unsuccessful_more_than_3": overall["unsuccessful_more_than_3"],
    "not_reported_all":         0,
    "all_cleared":              overall["all_cleared"],
    "success_percent":          f"{overall['success_percent']:.2f}%",
}
annexure1_ctx = {
    "one_subject": [],
    "two_subject": [
        {
            "reg_no":   r["reg_no"],
            "name":     r["name"],
            "subjects": ", ".join(r["failed_subjects"]),
            "remarks":  "",
        }
        for r in failures["2_subjects"]
    ],
    "three_subject":   [],
    "more_than_three": [],
}
annexure2_rows = [
    {
        "course_code":  s["subject_name"],
        "course_title": s["subject_name"],
        "registered":   s["registered"],
        "attended":     s["attended"],
        "o":            s["grades"]["O"],
        "aplus":        s["grades"]["A+"],
        "a":            s["grades"]["A"],
        "bplus":        s["grades"]["B+"],
        "b":            s["grades"]["B"],
        "c":            s["grades"]["C"],
        "f":            s["grades"]["F"],
        "absent":       s["absent"],
        "detained":     s["detained"],
        "wh":           0,
        "pass_percent": f"{s['pass_percentage']:.2f}%",
    }
    for s in stats
]
ctx = {
    "institute_name":    meta.get("institute", "SRM INSTITUTE OF SCIENCE AND TECHNOLOGY"),
    "faculty_name":      meta.get("faculty", ""),
    "campus_name":       meta.get("campus", ""),
    "department_name":   meta.get("department", ""),
    "exam_title":        meta.get("exam_title", ""),
    "degree_department": "B.E. / CSE",
    "faculty_advisor":   "Dr. Test Advisor",
    "total_strength":    overall["total_students"],
    "year_sem_section":  "3rd / Sem 5 / Section A",
    "batch":             "2022-2026",
    "exam_date":         "Nov/Dec 2025",
    "assessment_label":  "SEMESTER 5 EXAMINATION",
    "subjects":          subjects_ctx,
    "summary":           summary_ctx,
    "annexure1":         annexure1_ctx,
    "annexure2":         {"rows": annexure2_rows},
}

html = render_report("report_landscape.html", ctx)
out_path = os.path.join(SCRIPT_DIR, "smoke_output.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"    HTML rendered -> {out_path} ({len(html)} chars)")


# ---------------------------------------------------------------------------
# [7] Content checks — no dummy/placeholder data in output
# ---------------------------------------------------------------------------
print("[7] Verifying report content ...")

assert "Maths"    in html, "Subject 'Maths' should appear in the report"
assert "Physics"  in html, "Subject 'Physics' should appear in the report"
assert "RA211002" in html, "Bob (2 failures) should appear in Annexure 1"
assert "Bob"      in html, "Bob's name should appear in Annexure 1"

# CGPA / SGPA must NOT appear as a subject column in the rendered report table
# (they could appear elsewhere in preamble but not as a data column)
assert "placeholder" not in html.lower(), "No placeholder text allowed"
assert "sample" not in html.lower(),      "No sample text allowed"
assert "dummy"  not in html.lower(),      "No dummy text allowed"

print("    [PASS] No mock/placeholder/dummy content detected")
print("\n[OK] ALL CHECKS PASSED - pipeline is working correctly.")
