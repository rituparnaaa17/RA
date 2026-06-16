"""
seed_faculty.py — Run once to populate the `faculty` table in MySQL.

Usage (from the RA/backend directory):
    python seed_faculty.py

Add more entries to FACULTY_DATA as needed.
"""

import sys
import os

# Allow running from the project root
sys.path.insert(0, os.path.dirname(__file__))

import bcrypt
from db import engine, SessionLocal, Base
from models import Faculty


# ---- Add your faculty members here ----
FACULTY_DATA = [
    {
        "email": "admin@srmist.edu.in",
        "password": "admin123",
        "name": "Admin",
        "department": "CSE",
    },
    {
        "email": "faculty@srmist.edu.in",
        "password": "faculty123",
        "name": "Faculty User",
        "department": "CSE",
    },
    {
        "email": "rg0592@srmist.edu.in",
        "password": "okokokok",
        "name": "Rituparnaaa",
        "department": "CSE",
    },
]


def seed():
    # Create tables if they don't exist yet
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    added = 0
    skipped = 0

    try:
        for entry in FACULTY_DATA:
            existing = db.query(Faculty).filter(Faculty.email == entry["email"]).first()
            if existing:
                print(f"  [SKIP] Already exists: {entry['email']}")
                skipped += 1
                continue

            faculty = Faculty(
                email=entry["email"],
                password=bcrypt.hashpw(entry["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
                name=entry["name"],
                department=entry["department"],
            )
            db.add(faculty)
            added += 1
            print(f"  [OK]   Added: {entry['email']}")

        db.commit()
        print(f"\nDone. Added {added}, skipped {skipped}.")

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
