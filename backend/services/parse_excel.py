"""
parse_excel.py — Excel parsing and validation service.

Key behaviours:
  - Dynamically detects the header row (scans for Reg.No + Name).
  - Reads preamble rows ABOVE the header and combines ALL non-empty cells
    per row into a single string (fixes "Department CSE" truncation bug).
  - Absent tokens do NOT include standalone "A" / "A+" (those are grades).
  - Detained is handled separately from absent.
  - Subject columns are detected by excluding a strict blacklist.
  - Bad rows (no Reg.No, no Name, repeated headers, blank) are dropped.
  - Returns a structured parsed_data dict instead of a raw DataFrame.
"""

import logging
import os
import re

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token sets
# ---------------------------------------------------------------------------

# Values that mean "student was absent / withheld" — NOT grade letters.
# Removed lone "a" because A/A+ are valid grade letters.
_ABSENT_TOKENS: set[str] = {
    "ab", "abs", "absent",
    "--", "-", "",
    "wh", "w/h", "withheld",
    "na", "n/a",
}

# Values that mean "student was detained" — separate bucket from absent.
_DETAINED_TOKENS: set[str] = {
    "detained", "det", "d",
}

# Column names that are summary/metadata columns, NOT actual subjects.
_SUBJECT_BLACKLIST: set[str] = {
    "cgpa", "sgpa",
    "credits", "credit",
    "result", "results",
    "remarks", "remark",
    "total", "totals",
    "no. of subjects fail", "no.of subjects fail",
    "no. of subjects failed", "no of subjects fail",
    "no of subjects failed",
    "s.no", "s. no", "sno", "serial no", "sr no",
    "si no",
    "grade", "grades",
    "gpa",
    "status",
}

# Column names that are acceptable Reg.No variants
_REGNO_VARIANTS: set[str] = {
    "reg.no", "reg no", "register no", "register no.", "reg. no",
    "registration no", "registration number", "regno",
}

# Column names that are acceptable Name variants
_NAME_VARIANTS: set[str] = {
    "name", "student name", "name of the student", "student's name",
}


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _clean(v) -> str:
    """Convert a cell value to a stripped string; return '' for NaN/None."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def is_absent_value(val) -> bool:
    """Return True if the cell value means the student was absent/withheld."""
    if val is None or (isinstance(v := val, float) and pd.isna(v)):
        return True
    s = str(val).strip().lower()
    # Never treat grade letters (single uppercase) as absent
    if s in _DETAINED_TOKENS:
        return False
    return s in _ABSENT_TOKENS


def is_detained_value(val) -> bool:
    """Return True if the cell value means the student was detained."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    s = str(val).strip().lower()
    return s in _DETAINED_TOKENS


# ---------------------------------------------------------------------------
# Preamble metadata extraction
# ---------------------------------------------------------------------------

def _extract_metadata_from_preamble(raw_df: pd.DataFrame, header_idx: int) -> dict:
    """
    Parse rows ABOVE the actual data header to extract institute-level metadata.

    FIX vs previous version:
      - All non-empty cells in a row are JOINED (not just first cell taken).
        This captures "Department  CSE" as "Department CSE" instead of just
        "Department".

    Returns dict with keys:
      institute, faculty, campus, department,
      branch, year, sem, section, exam_title
    """
    meta = {
        "institute":  "",
        "faculty":    "",
        "campus":     "",
        "department": "",
        "branch":     "",
        "year":       "",
        "sem":        "",
        "section":    "",
        "exam_title": "",
    }

    preamble_rows: list[str] = []
    for i in range(header_idx):
        # Combine ALL non-empty cells from the row into one string
        row_vals = [_clean(v) for v in raw_df.iloc[i].values if _clean(v)]
        if row_vals:
            combined = "  ".join(row_vals)  # double-space separator for readability
            preamble_rows.append(combined)

    logger.debug("Preamble rows (%d): %s", len(preamble_rows), preamble_rows)

    # Assign preamble rows to metadata fields heuristically
    for val in preamble_rows:
        val_lower = val.lower()

        if not meta["institute"] and (
            "srm" in val_lower or "institute" in val_lower or "university" in val_lower
        ):
            meta["institute"] = val
        elif "campus" in val_lower or "chennai" in val_lower or "kattankulathur" in val_lower:
            if not meta["campus"]:
                meta["campus"] = val
        elif "faculty of" in val_lower or "school of" in val_lower:
            if not meta["faculty"]:
                meta["faculty"] = val
        elif "department" in val_lower or "dept" in val_lower:
            meta["department"] = val
        elif "branch" in val_lower and ("year" in val_lower or "sem" in val_lower or "/" in val):
            _parse_branch_line(val, meta)
        elif (
            "result" in val_lower or "analysis" in val_lower
            or "semester" in val_lower or "exam" in val_lower
        ):
            if not meta["exam_title"]:
                meta["exam_title"] = val
        else:
            # Fallback: try to fill institute/faculty in order
            if not meta["institute"]:
                meta["institute"] = val
            elif not meta["faculty"]:
                meta["faculty"] = val

    logger.info("Metadata extracted: %s", meta)
    return meta


def _parse_branch_line(line: str, meta: dict) -> None:
    """
    Parse a line like 'Branch/Year/Sem: CSE - I/II/III'
    and populate meta keys: branch, year, sem, section.
    """
    # Strip leading label like "Branch/Year/Sem:"
    text = re.sub(
        r"^(branch[/\s]*year[/\s]*sem\s*:?\s*)+", "", line, flags=re.IGNORECASE
    ).strip()
    parts = re.split(r"\s*[-–]\s*|\s*/\s*", text)
    if len(parts) >= 1:
        meta["branch"] = parts[0].strip()
    if len(parts) >= 2:
        meta["year"] = parts[1].strip()
    if len(parts) >= 3:
        meta["sem"] = parts[2].strip()
    if len(parts) >= 4:
        meta["section"] = parts[3].strip()


# ---------------------------------------------------------------------------
# Subject column detection
# ---------------------------------------------------------------------------

def _is_valid_subject_column(col_name: str) -> bool:
    """
    Return True only if the column name looks like a real subject column.

    Rejects:
      - Blank / unnamed columns
      - Anything in the blacklist
      - Pure numeric / integer columns (like index columns)
    """
    s = col_name.strip()
    if not s or "unnamed:" in s.lower():
        return False
    if s.lower() in _SUBJECT_BLACKLIST:
        return False
    # Reject if any substring of the blacklist is contained within the column
    sl = s.lower()
    for bad in _SUBJECT_BLACKLIST:
        if bad in sl:
            return False
    return True


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def validate_and_extract_data(file_path: str):
    """
    Reads an Excel file, validates its structure, and returns:
      (DataFrame, subject_columns, metadata_dict)

    DataFrame columns are normalised: Reg.No, Name, <subject>, ...
    No mock data is ever inserted; errors are raised with meaningful messages.

    Raises:
      FileNotFoundError  — file missing on disk
      ValueError("Invalid Excel format: ...")   — unreadable file
      ValueError("Header row not found")        — missing Reg.No + Name header
      ValueError("Subject columns not detected") — no subject columns found
      ValueError("Unsupported file extension: ...") — bad extension
    """
    # ── 1. File existence & extension ────────────────────────────────────────
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Uploaded file not found on disk: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".xls":
        engine = "xlrd"
    elif ext in (".xlsx", ".xlsm", ".xlam"):
        engine = "openpyxl"
    else:
        raise ValueError(
            f"Unsupported file extension: '{ext}'. Please upload .xlsx or .xls"
        )

    # ── 2. Read file ──────────────────────────────────────────────────────────
    try:
        raw_df = pd.read_excel(file_path, engine=engine, header=None, dtype=str)
    except Exception as exc:
        raise ValueError(f"Invalid Excel format: {exc}") from exc

    if raw_df.empty:
        raise ValueError("Uploaded Excel file is empty (no data found)")

    # ── 3. Find header row ────────────────────────────────────────────────────
    header_idx: int | None = None
    for idx, row in raw_df.iterrows():
        row_strings = row.astype(str).str.strip().str.lower()
        has_reg  = any(v in _REGNO_VARIANTS  for v in row_strings.values)
        has_name = any(v in _NAME_VARIANTS   for v in row_strings.values)
        if has_reg and has_name:
            header_idx = idx
            break

    if header_idx is None:
        raise ValueError("Header row not found — expected columns 'Reg.No' and 'Name'")

    logger.info("Header row detected at index %d", header_idx)

    # ── 4. Extract preamble metadata ──────────────────────────────────────────
    metadata = _extract_metadata_from_preamble(raw_df, header_idx)

    # ── 5. Build working DataFrame ────────────────────────────────────────────
    df = raw_df.copy()
    df.columns = df.iloc[header_idx].astype(str).str.strip()
    df = df.iloc[header_idx + 1:].reset_index(drop=True)

    # Normalise Reg.No / Name column names
    new_cols: list[str] = []
    reg_done = name_done = False
    for col in df.columns:
        cl = col.strip().lower()
        if not reg_done and cl in _REGNO_VARIANTS:
            new_cols.append("Reg.No")
            reg_done = True
        elif not name_done and cl in _NAME_VARIANTS:
            new_cols.append("Name")
            name_done = True
        else:
            new_cols.append(col)
    df.columns = new_cols

    # ── 6. Detect subject columns ─────────────────────────────────────────────
    try:
        name_pos = list(df.columns).index("Name")
    except ValueError:
        raise ValueError("Header row not found — 'Name' column missing after normalisation")

    # Find first blacklisted/non-subject column AFTER Name as the end boundary
    end_pos: int | None = None
    for i, col in enumerate(df.columns):
        if i <= name_pos:
            continue
        if not _is_valid_subject_column(col):
            end_pos = i
            break

    raw_subject_cols = list(df.columns[name_pos + 1 : end_pos])
    subject_columns  = [c for c in raw_subject_cols if _is_valid_subject_column(c)]

    if not subject_columns:
        raise ValueError(
            "Subject columns not detected — ensure subject columns appear between "
            "'Name' and summary columns like 'CGPA', 'No. of subjects fail', etc."
        )

    logger.info("Subject columns detected (%d): %s", len(subject_columns), subject_columns)

    # ── 7. Clean student rows ─────────────────────────────────────────────────
    # a) Drop rows where Reg.No is empty / NaN / repeated header token
    df = df[
        df["Reg.No"].notna()
        & (df["Reg.No"].str.strip() != "")
        & (df["Reg.No"].str.lower() != "nan")
        & (~df["Reg.No"].str.strip().str.lower().isin(_REGNO_VARIANTS))
    ].copy()

    # b) Drop rows where Name is missing
    df = df[
        df["Name"].notna()
        & (df["Name"].str.strip() != "")
        & (df["Name"].str.lower() != "nan")
        & (~df["Name"].str.strip().str.lower().isin(_NAME_VARIANTS))
    ].copy()

    # c) Drop completely blank rows (all subject cells are empty)
    def _row_has_any_data(row) -> bool:
        return any(_clean(row.get(sub, "")) for sub in subject_columns)

    if not df.empty:
        df = df[df.apply(_row_has_any_data, axis=1)].copy()

    df.reset_index(drop=True, inplace=True)

    logger.info(
        "Students after cleaning: %d | Subjects: %d",
        len(df), len(subject_columns),
    )

    # ── 8. Return structured result ───────────────────────────────────────────
    return df, subject_columns, metadata
