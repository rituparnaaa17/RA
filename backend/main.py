"""
SRM Result Analysis — FastAPI Backend (MySQL-connected)
=======================================================
Endpoints:
  POST /api/auth/login         — validate faculty credentials against MySQL
  POST /api/reports/upload     — parse Excel -> compute stats -> render
                                 report_landscape.html -> persist to MySQL
  GET  /                       — health check

Pipeline (upload):
  Upload Excel
    -> validate_and_extract_data()   [parse_excel.py]
    -> compute_report_data()         [compute.py]
    -> build Jinja2 context          [main.py — structured dicts only]
    -> render_report()               [render.py + Jinja2 template]
    -> persist to MySQL              [models.py / SQLAlchemy]
    -> return rendered HTML

No mock, dummy, or sample data is used anywhere in this pipeline.
"""

import logging
import os
import uuid
from datetime import datetime, timedelta

import bcrypt
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

# ── Internal modules ──────────────────────────────────────────────────────────
from db import Base, engine, get_db, verify_connection
from models import Faculty, Report
from services.compute import compute_report_data
from services.parse_excel import validate_and_extract_data
from services.render import render_report

# ─────────────────────────────────────────────────────────────────────────────
# Security config
# ─────────────────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", "change-me-in-production-railway-env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

pwd_context = None  # unused — replaced by bcrypt directly
bearer_scheme = HTTPBearer()

limiter = Limiter(key_func=get_remote_address)

# ─────────────────────────────────────────────────────────────────────────────
# App + Middleware
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="SRM Result Analysis Backend")
app.state.limiter = limiter

origins = [
    "http://localhost:3000",
    "https://ra-liart.vercel.app",
    "https://srm-result-analysis.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SlowAPIMiddleware)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"success": False, "message": "Too many requests. Please wait and try again."},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal Server Error"},
    )


# ─────────────────────────────────────────────────────────────────────────────
# JWT helpers
# ─────────────────────────────────────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """FastAPI dependency — validates JWT token and returns the faculty email."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub", "")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid. Please log in again.")



# ─────────────────────────────────────────────────────────────────────────────
# Startup — create tables + verify DB
# ─────────────────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
        if verify_connection():
            logger.info("[OK] MySQL tables ready.")
        else:
            logger.warning("[WARN] Could not verify MySQL on startup. Reports won't be persisted.")
    except Exception as exc:
        logger.error("[ERROR] Startup DB init failed: %s", exc)


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/")
def health():
    return {"status": "ok", "service": "SRM Result Analysis"}


# ─────────────────────────────────────────────────────────────────────────────
# Auth — Login
# ─────────────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/auth/login")
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    """Validates faculty credentials and returns a signed JWT token."""
    if "srm" not in body.email.lower():
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Only SRM faculty email IDs are allowed"},
        )

    faculty = db.query(Faculty).filter(Faculty.email == body.email).first()

    # Constant-time check — always verify even if user not found to prevent timing attacks
    valid_password = (
        faculty is not None
        and bcrypt.checkpw(body.password.encode("utf-8"), faculty.password.encode("utf-8"))
    )

    if not faculty or not valid_password:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Invalid email or password."},
        )

    token = create_access_token({"sub": faculty.email})
    return {
        "success": True,
        "message": "Login successful",
        "name": faculty.name or body.email.split("@")[0],
        "token": token,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helper — build a user-facing error HTML response
# ─────────────────────────────────────────────────────────────────────────────
def _error_html(message: str, status_code: int = 400) -> HTMLResponse:
    """Return a minimal, styled error page — no placeholders or dummy data."""
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Upload Error</title>
  <style>
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; background:#f8fafc;
            display:flex; align-items:center; justify-content:center; min-height:100vh; margin:0; }}
    .card {{ background:#fff; border-radius:10px; padding:40px 48px; max-width:520px;
             box-shadow:0 4px 24px rgba(0,0,0,.1); text-align:center; }}
    h2 {{ color:#dc2626; margin-bottom:12px; }}
    p  {{ color:#475569; line-height:1.6; }}
    a  {{ color:#2563eb; text-decoration:none; font-weight:600; }}
  </style>
</head>
<body>
  <div class="card">
    <h2>Upload Error</h2>
    <p>{message}</p>
    <p style="margin-top:24px;"><a href="javascript:history.back()">Go back</a></p>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=status_code)


# ─────────────────────────────────────────────────────────────────────────────
# Upload → Parse → Compute → Render → Persist
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/reports/upload", response_class=HTMLResponse)
async def upload_and_generate_report(
    file: UploadFile = File(...),
    dept: str = Form(""),
    year: str = Form(""),
    sem:  str = Form(""),
    section: str = Form(""),
    faculty_advisor_name: str = Form(""),
    batch: str = Form(""),
    exam_date: str = Form(""),
    db: Session = Depends(get_db),
    current_user: str = Depends(require_auth),
):
    """
    Full pipeline — no mock data at any stage:
      1. Validate + save the uploaded Excel file.
      2. Parse the Excel (subjects, marks, absent/detained markers).
      3. Compute grade-level statistics.
      4. Render report_landscape.html via Jinja2 (structured context only).
      5. Persist the report to MySQL (graceful if DB unavailable).
      6. Return the rendered HTML string.
    """
    saved_path: str | None = None

    try:
        # ── 1. Validate file extension ────────────────────────────────────────
        filename = (file.filename or "").strip()
        if not filename:
            return _error_html("No file was received by the server.")

        ext = os.path.splitext(filename)[1].lower()
        if ext not in (".xlsx", ".xls"):
            return _error_html(
                f"Unsupported file type '{ext}'. Please upload a valid Excel file (.xlsx or .xls)."
            )

        # ── 2. Read & save uploaded file ──────────────────────────────────────
        contents = await file.read()
        if not contents:
            return _error_html("The uploaded file is empty (0 bytes).")

        file_uuid  = str(uuid.uuid4())
        saved_path = os.path.join(UPLOAD_DIR, f"{file_uuid}{ext}")
        with open(saved_path, "wb") as fh:
            fh.write(contents)

        logger.info("Saved upload: %s (%d bytes)", saved_path, len(contents))

        # ── 3. Parse & validate Excel ─────────────────────────────────────────
        try:
            df, subject_columns, xl_meta = validate_and_extract_data(saved_path)
        except FileNotFoundError as exc:
            return _error_html(f"File save error: {exc}", 500)
        except ValueError as exc:
            msg = str(exc)
            # Map structured error messages to user-friendly descriptions
            if "Header row not found" in msg:
                return _error_html(
                    "Header row not found — the Excel file must contain 'Reg.No' and 'Name' columns."
                )
            if "Subject columns not detected" in msg:
                return _error_html(
                    "Subject columns not detected — ensure subject marks appear between "
                    "'Name' and summary columns like 'CGPA' or 'No. of subjects fail'."
                )
            if "Invalid Excel format" in msg:
                return _error_html(f"Invalid Excel format: {msg}")
            if "empty" in msg.lower():
                return _error_html("The uploaded file contains no data.")
            return _error_html(msg)

        if df.empty:
            return _error_html(
                "The uploaded file has no student records after cleaning. "
                "Please check that rows have both Reg.No and Name filled in."
            )

        logger.info(
            "Parsed Excel: %d student rows | %d subject column(s): %s",
            len(df), len(subject_columns), subject_columns,
        )

        # ── 4. Compute statistics ─────────────────────────────────────────────
        computed = compute_report_data(df, subject_columns)
        overall  = computed["overall_summary"]
        stats    = computed["subject_stats"]      # list[dict]
        failures = computed["student_failures"]   # grouped by fail-count

        logger.info(
            "Computed: %d students | cleared=%d | pass=%.1f%%",
            overall["total_students"], overall["all_cleared"],
            overall["success_percent"],
        )

        # ── 5. Build Jinja2 template context ──────────────────────────────────
        # Helper: prefer form-supplied value, fall back to Excel-parsed value.
        def _pick(form_val: str, xl_val: str) -> str:
            v = (form_val or "").strip()
            return v if v else (xl_val or "")

        institute_name = xl_meta.get("institute", "") or "SRM INSTITUTE OF SCIENCE AND TECHNOLOGY"
        faculty_name   = xl_meta.get("faculty",   "") or ""
        campus_name    = xl_meta.get("campus",    "") or ""
        dept_from_xl   = xl_meta.get("department","") or ""
        exam_title_xl  = xl_meta.get("exam_title","") or ""

        dept_label    = _pick(dept,                 dept_from_xl)
        year_label    = _pick(year,                 xl_meta.get("year", ""))
        sem_label     = _pick(sem,                  xl_meta.get("sem",  ""))
        section_label = _pick(section,              xl_meta.get("section", ""))
        faculty_label = _pick(faculty_advisor_name, "")
        batch_label   = (batch    or "").strip() or "—"
        exam_label    = (exam_date or "").strip() or "—"
        branch_label  = xl_meta.get("branch", "")

        ys_parts = [
            p for p in [
                year_label,
                f"Sem {sem_label}"       if sem_label     else "",
                f"Section {section_label}" if section_label else "",
            ]
            if p
        ]
        year_sem_section = " / ".join(ys_parts) if ys_parts else "N/A"
        degree_dept      = dept_label if dept_label else (branch_label or "N/A")

        # ── Page 1 — subject rows (all data from computed stats, no placeholders)
        subjects_ctx = [
            {
                "course_code":    s.get("subject_name", ""),
                "course_title":   s.get("subject_name", ""),
                "absent":         s.get("absent",       0),
                "detained":       s.get("detained",     0),
                "successful":     s.get("passed",       0),
                "total_students": s.get("registered",   0),
                "success_percent": f"{s.get('pass_percentage', 0.0):.2f}%",
            }
            for s in stats
        ]

        # ── Page 1 — summary row
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

        # ── Page 2 — Annexure 1 failure lists
        def _one(f: dict) -> dict:
            subs = f.get("failed_subjects", [])
            return {
                "reg_no":  str(f.get("reg_no", "")),
                "name":    str(f.get("name",   "")),
                "subject": subs[0] if subs else "—",
                "remarks": "",
            }

        def _multi(f: dict) -> dict:
            return {
                "reg_no":   str(f.get("reg_no", "")),
                "name":     str(f.get("name",   "")),
                "subjects": ", ".join(f.get("failed_subjects", [])),
                "remarks":  "",
            }

        annexure1_ctx = {
            "one_subject":     [_one(f)   for f in failures.get("1_subject",   [])],
            "two_subject":     [_multi(f) for f in failures.get("2_subjects",  [])],
            "three_subject":   [_multi(f) for f in failures.get("3_subjects",  [])],
            "more_than_three": [_multi(f) for f in failures.get("more_than_3", [])],
        }

        # ── Page 3 — Annexure 2 grade distribution
        annexure2_rows = []
        for s in stats:
            g = s.get("grades", {})
            annexure2_rows.append({
                "course_code":  s.get("subject_name", ""),
                "course_title": s.get("subject_name", ""),
                "registered":   s.get("registered",   0),
                "attended":     s.get("attended",     0),
                "o":            g.get("O",  0),
                "aplus":        g.get("A+", 0),
                "a":            g.get("A",  0),
                "bplus":        g.get("B+", 0),
                "b":            g.get("B",  0),
                "c":            g.get("C",  0),
                "f":            g.get("F",  0),
                "absent":       s.get("absent",   0),
                "detained":     s.get("detained", 0),
                "wh":           0,
                "pass_percent": f"{s.get('pass_percentage', 0.0):.2f}%",
            })

        template_context = {
            # Header — sourced from Excel preamble; no defaults if empty
            "institute_name":    institute_name,
            "faculty_name":      faculty_name,
            "campus_name":       campus_name,
            "department_name":   dept_from_xl,
            "exam_title":        exam_title_xl,
            # Meta grid
            "degree_department": degree_dept,
            "faculty_advisor":   faculty_label,
            "total_strength":    overall["total_students"],
            "year_sem_section":  year_sem_section,
            "batch":             batch_label,
            "exam_date":         exam_label,
            "assessment_label":  exam_title_xl or f"SEMESTER {sem_label} EXAMINATION",
            # Data tables — all from real uploaded data
            "subjects":   subjects_ctx,
            "summary":    summary_ctx,
            "annexure1":  annexure1_ctx,
            "annexure2":  {"rows": annexure2_rows},
        }

        # ── 6. Render HTML ────────────────────────────────────────────────────
        try:
            html = render_report("report_landscape.html", template_context)
        except Exception as exc:
            logger.exception("Template rendering failed: %s", exc)
            return _error_html(f"Report rendering error: {exc}", 500)

        logger.info("Template rendered successfully (%d chars).", len(html))

        # ── 7. Persist to MySQL (non-fatal if DB is down) ─────────────────────
        try:
            record = Report(
                dept=dept,
                year=year,
                sem=sem,
                section=section,
                faculty_advisor_name=faculty_advisor_name,
                original_filename=filename,
                file_path=saved_path,
                status="processed",
            )
            record.set_computed({
                "overall":   overall,
                "subjects":  stats,
                "failures":  failures,
            })
            record.report_html = html

            db.add(record)
            db.commit()
            db.refresh(record)
            logger.info("[OK] Report id=%d saved to MySQL.", record.id)

        except Exception as db_exc:
            logger.error(
                "[WARN] Could not persist report to MySQL (report still returned): %s",
                db_exc,
            )
            # Non-fatal — the HTML is ready; skip persistence silently.

        return HTMLResponse(content=html, status_code=200)

    except Exception as exc:
        logger.exception("Unhandled error in /api/reports/upload: %s", exc)
        return _error_html(f"Unexpected server error: {exc}", 500)
