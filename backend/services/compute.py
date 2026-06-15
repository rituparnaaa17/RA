"""
compute.py — Statistics engine.

Consumes a cleaned DataFrame + subject_columns list from parse_excel.py.
Produces structured JSON-safe dicts — NO raw DataFrames are ever returned.

No mock/sample/dummy data is generated here.
"""

import logging

import pandas as pd

from services.parse_excel import is_absent_value, is_detained_value

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Grade mapping
# ---------------------------------------------------------------------------

def calculate_grade(val) -> str:
    """
    Map a raw Excel cell value to a grade letter.

    Priority:
      1. Detained marker  → "Detained"
      2. Absent / withheld marker → "Absent"
      3. Numeric value    → O | A+ | A | B+ | B | C | F
      4. Unknown string   → "Absent" (safe fallback — never fabricate a mark)

    Grade scale (SRM):
      O   : >= 91
      A+  : 81–90
      A   : 71–80
      B+  : 61–70
      B   : 56–60
      C   : 50–55
      F   : < 50
    """
    if is_detained_value(val):
        return "Detained"
    if is_absent_value(val):
        return "Absent"

    try:
        mark = float(str(val).strip())
    except (ValueError, TypeError):
        # Non-numeric, non-absent string — treat as absent, log for debugging
        logger.debug("Unknown cell value '%s' — treating as Absent", val)
        return "Absent"

    if mark >= 91:
        return "O"
    if mark >= 81:
        return "A+"
    if mark >= 71:
        return "A"
    if mark >= 61:
        return "B+"
    if mark >= 56:
        return "B"
    if mark >= 50:
        return "C"
    return "F"


# ---------------------------------------------------------------------------
# Main computation
# ---------------------------------------------------------------------------

def compute_report_data(df: pd.DataFrame, subject_columns: list) -> dict:
    """
    Core statistics engine.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned student data from validate_and_extract_data().
        Must have columns: Reg.No, Name, <subject>, ...
    subject_columns : list[str]
        Names of the subject columns to process.

    Returns
    -------
    dict with keys:
        "overall_summary"  : { total_students, unsuccessful_1..4+,
                                all_cleared, success_percent }
        "subject_stats"    : [ { subject_name, registered, attended,
                                  absent, detained, passed, failed,
                                  grades:{O,A+,A,B+,B,C,F},
                                  pass_percentage } … ]
        "student_failures" : { 1_subject:[…], 2_subjects:[…],
                               3_subjects:[…], more_than_3:[…] }
        "students"         : [ { reg_no, name, subjects:{sub:grade,…} } … ]

    NOTE: If df is empty, returns zero-filled structure — no dummy rows.
    """
    _empty_overall = {
        "total_students":           0,
        "unsuccessful_1":           0,
        "unsuccessful_2":           0,
        "unsuccessful_3":           0,
        "unsuccessful_more_than_3": 0,
        "all_cleared":              0,
        "success_percent":          0.0,
    }
    _empty_groups = {
        "1_subject":   [],
        "2_subjects":  [],
        "3_subjects":  [],
        "more_than_3": [],
    }

    if df.empty or not subject_columns:
        logger.warning("compute_report_data called with empty DataFrame — returning zero totals")
        return {
            "overall_summary":  _empty_overall,
            "subject_stats":    [],
            "student_failures": _empty_groups,
            "students":         [],
        }

    # ── Per-subject accumulators ──────────────────────────────────────────────
    subject_stats: dict[str, dict] = {}
    for sub in subject_columns:
        subject_stats[sub] = {
            "registered":      0,
            "attended":        0,
            "absent":          0,
            "detained":        0,
            "passed":          0,
            "failed":          0,
            "grades":          {"O": 0, "A+": 0, "A": 0, "B+": 0, "B": 0, "C": 0, "F": 0},
            "pass_percentage": 0.0,
        }

    # ── Per-student tracking ──────────────────────────────────────────────────
    total_students    = len(df)
    all_cleared_count = 0
    unsuccessful      = {1: 0, 2: 0, 3: 0, "more_than_3": 0}
    failure_records: list[dict] = []
    student_records: list[dict] = []

    for _, row in df.iterrows():
        reg_no = str(row.get("Reg.No", "")).strip()
        name   = str(row.get("Name",   "")).strip()

        failed_subs:    list[str] = []
        student_grades: dict[str, str] = {}

        for sub in subject_columns:
            val   = row.get(sub)
            grade = calculate_grade(val)
            st    = subject_stats[sub]
            student_grades[sub] = grade

            st["registered"] += 1

            if grade == "Detained":
                st["detained"] += 1
            elif grade == "Absent":
                st["absent"] += 1
            else:
                st["attended"]        += 1
                st["grades"][grade]   += 1
                if grade == "F":
                    st["failed"]     += 1
                    failed_subs.append(sub)
                else:
                    st["passed"] += 1

        # Student-level record (structured JSON, no raw DataFrame)
        student_records.append({
            "reg_no":   reg_no,
            "name":     name,
            "subjects": student_grades,
        })

        # Failure counting
        fail_count = len(failed_subs)
        if fail_count == 0:
            all_cleared_count += 1
        elif fail_count == 1:
            unsuccessful[1] += 1
        elif fail_count == 2:
            unsuccessful[2] += 1
        elif fail_count == 3:
            unsuccessful[3] += 1
        else:
            unsuccessful["more_than_3"] += 1

        if fail_count > 0:
            failure_records.append({
                "reg_no":          reg_no,
                "name":            name,
                "failed_subjects": failed_subs,
                "fail_count":      fail_count,
            })

    # ── Finalise subject pass % ───────────────────────────────────────────────
    final_subject_stats: list[dict] = []
    for sub, st in subject_stats.items():
        # Denominator excludes detained students
        denom = st["registered"] - st["detained"]
        st["pass_percentage"] = (
            round(st["passed"] / denom * 100, 2) if denom > 0 else 0.0
        )
        entry = {"subject_name": sub}
        entry.update(st)
        final_subject_stats.append(entry)

    # ── Annexure 1 grouping ───────────────────────────────────────────────────
    grouped = {
        "1_subject":   [r for r in failure_records if r["fail_count"] == 1],
        "2_subjects":  [r for r in failure_records if r["fail_count"] == 2],
        "3_subjects":  [r for r in failure_records if r["fail_count"] == 3],
        "more_than_3": [r for r in failure_records if r["fail_count"] >  3],
    }

    # ── Overall summary ───────────────────────────────────────────────────────
    overall = {
        "total_students":           total_students,
        "all_cleared":              all_cleared_count,
        "unsuccessful_1":           unsuccessful[1],
        "unsuccessful_2":           unsuccessful[2],
        "unsuccessful_3":           unsuccessful[3],
        "unsuccessful_more_than_3": unsuccessful["more_than_3"],
        "success_percent": (
            round(all_cleared_count / total_students * 100, 2)
            if total_students > 0 else 0.0
        ),
    }

    logger.info(
        "Computed: %d students | %d cleared | pass=%.1f%% | %d subject(s)",
        total_students, all_cleared_count,
        overall["success_percent"], len(final_subject_stats),
    )

    return {
        "overall_summary":  overall,
        "subject_stats":    final_subject_stats,
        "student_failures": grouped,
        "students":         student_records,
    }
