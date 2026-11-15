"""Build the benchmark database (SQLite) from a fixed random seed.

Usage:
    python build_db.py            # writes gulf_gov.db next to this file

The data is synthetic but shaped like real Gulf public-sector systems:
bilingual (Arabic / English) reference data, Arabic personal names,
Saudi Riyal amounts, and the kind of messy distributions you meet in practice.
"""
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

SEED = 2026
DB_PATH = Path(__file__).with_name("gulf_gov.db")

SCHEMA = """
CREATE TABLE regions (
    region_id   INTEGER PRIMARY KEY,
    name_en     TEXT NOT NULL,
    name_ar     TEXT NOT NULL
);
CREATE TABLE cities (
    city_id     INTEGER PRIMARY KEY,
    region_id   INTEGER NOT NULL REFERENCES regions(region_id),
    name_en     TEXT NOT NULL,
    name_ar     TEXT NOT NULL
);
CREATE TABLE departments (
    dept_id     INTEGER PRIMARY KEY,
    name_en     TEXT NOT NULL,
    name_ar     TEXT NOT NULL
);
CREATE TABLE employees (
    emp_id        INTEGER PRIMARY KEY,
    full_name_ar  TEXT NOT NULL,
    full_name_en  TEXT NOT NULL,
    gender        TEXT NOT NULL CHECK (gender IN ('M','F')),
    nationality   TEXT NOT NULL,          -- 'Saudi' or 'Non-Saudi'
    dept_id       INTEGER NOT NULL REFERENCES departments(dept_id),
    city_id       INTEGER NOT NULL REFERENCES cities(city_id),
    grade         INTEGER NOT NULL,       -- civil service grade 1-15
    hire_date     TEXT NOT NULL,          -- ISO date
    salary_sar    REAL NOT NULL,          -- monthly basic salary, SAR
    status        TEXT NOT NULL CHECK (status IN ('active','on_leave','retired'))
);
CREATE TABLE permits (
    permit_id      INTEGER PRIMARY KEY,
    permit_type    TEXT NOT NULL,         -- building, commercial, signage, excavation
    applicant_type TEXT NOT NULL,         -- individual, company
    city_id        INTEGER NOT NULL REFERENCES cities(city_id),
    submitted_date TEXT NOT NULL,
    decision_date  TEXT,                  -- NULL while pending
    status         TEXT NOT NULL CHECK (status IN ('approved','rejected','pending')),
    fee_sar        REAL NOT NULL
);
CREATE TABLE inspections (
    inspection_id    INTEGER PRIMARY KEY,
    permit_id        INTEGER NOT NULL REFERENCES permits(permit_id),
    inspection_date  TEXT NOT NULL,
    result           TEXT NOT NULL CHECK (result IN ('pass','fail')),
    violations_count INTEGER NOT NULL
);
"""

REGIONS = [
    (1, "Riyadh", "الرياض"),
    (2, "Makkah", "مكة المكرمة"),
    (3, "Eastern Province", "المنطقة الشرقية"),
    (4, "Madinah", "المدينة المنورة"),
    (5, "Qassim", "القصيم"),
]
CITIES = [
    (1, 1, "Riyadh", "الرياض"),
    (2, 1, "Al Kharj", "الخرج"),
    (3, 2, "Jeddah", "جدة"),
    (4, 2, "Makkah", "مكة المكرمة"),
    (5, 2, "Taif", "الطائف"),
    (6, 3, "Dammam", "الدمام"),
    (7, 3, "Al Khobar", "الخبر"),
    (8, 3, "Al Ahsa", "الأحساء"),
    (9, 4, "Madinah", "المدينة المنورة"),
    (10, 5, "Buraydah", "بريدة"),
    (11, 5, "Unaizah", "عنيزة"),
]
DEPARTMENTS = [
    (1, "Human Resources", "الموارد البشرية"),
    (2, "Finance", "المالية"),
    (3, "Urban Planning", "التخطيط العمراني"),
    (4, "Licensing", "التراخيص"),
    (5, "Inspection", "الرقابة والتفتيش"),
    (6, "Information Technology", "تقنية المعلومات"),
]
FIRST_M = [("محمد", "Mohammed"), ("عبدالله", "Abdullah"), ("فهد", "Fahad"),
           ("خالد", "Khalid"), ("سعود", "Saud"), ("فيصل", "Faisal"),
           ("عمر", "Omar"), ("ناصر", "Nasser"), ("تركي", "Turki"), ("سلمان", "Salman")]
FIRST_F = [("نورة", "Noura"), ("سارة", "Sara"), ("ريم", "Reem"), ("هيا", "Haya"),
           ("لمى", "Lama"), ("أمل", "Amal"), ("منيرة", "Munira"), ("عبير", "Abeer")]
FAMILY = [("القحطاني", "Al-Qahtani"), ("العتيبي", "Al-Otaibi"), ("الشمري", "Al-Shammari"),
          ("الدوسري", "Al-Dosari"), ("الغامدي", "Al-Ghamdi"), ("الزهراني", "Al-Zahrani"),
          ("الحربي", "Al-Harbi"), ("المطيري", "Al-Mutairi"), ("السبيعي", "Al-Subaie")]
PERMIT_TYPES = ["building", "commercial", "signage", "excavation"]
FEES = {"building": 5000, "commercial": 2500, "signage": 800, "excavation": 3500}


def rand_date(rng, start, end):
    return start + timedelta(days=rng.randint(0, (end - start).days))


def build(path=DB_PATH):
    rng = random.Random(SEED)
    if Path(path).exists():
        Path(path).unlink()
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO regions VALUES (?,?,?)", REGIONS)
    con.executemany("INSERT INTO cities VALUES (?,?,?,?)", CITIES)
    con.executemany("INSERT INTO departments VALUES (?,?,?)", DEPARTMENTS)

    employees = []
    for emp_id in range(1, 401):
        gender = "F" if rng.random() < 0.38 else "M"
        fa, fe = rng.choice(FIRST_F if gender == "F" else FIRST_M)
        la, le = rng.choice(FAMILY)
        nationality = "Saudi" if rng.random() < 0.82 else "Non-Saudi"
        grade = rng.randint(1, 15)
        salary = round(4000 + grade * 1150 + rng.uniform(-600, 900), 2)
        hire = rand_date(rng, date(2004, 1, 1), date(2026, 6, 30))
        status = rng.choices(["active", "on_leave", "retired"], [0.86, 0.06, 0.08])[0]
        employees.append((emp_id, f"{fa} {la}", f"{fe} {le}", gender, nationality,
                          rng.randint(1, 6), rng.choice(CITIES)[0], grade,
                          hire.isoformat(), salary, status))
    con.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?,?,?,?,?,?)", employees)

    permits, inspections, insp_id = [], [], 1
    for permit_id in range(1, 1201):
        ptype = rng.choices(PERMIT_TYPES, [0.35, 0.35, 0.18, 0.12])[0]
        city = rng.choices(CITIES, [20, 4, 14, 6, 4, 9, 6, 5, 7, 4, 3])[0][0]
        submitted = rand_date(rng, date(2024, 1, 1), date(2026, 10, 31))
        status = rng.choices(["approved", "rejected", "pending"], [0.68, 0.17, 0.15])[0]
        decision = None
        if status != "pending":
            decision = (submitted + timedelta(days=rng.randint(2, 75))).isoformat()
        fee = round(FEES[ptype] * rng.uniform(0.8, 1.6), 2)
        permits.append((permit_id, ptype, rng.choice(["individual", "company"]), city,
                        submitted.isoformat(), decision, status, fee))
        if (status == "approved" and ptype in ("building", "commercial", "excavation")
                and rng.random() < 0.85):
            for _ in range(rng.randint(1, 3)):
                d = submitted + timedelta(days=rng.randint(10, 200))
                result = "fail" if rng.random() < 0.22 else "pass"
                v = rng.randint(1, 6) if result == "fail" else rng.choice([0, 0, 0, 1])
                inspections.append((insp_id, permit_id, d.isoformat(), result, v))
                insp_id += 1
    con.executemany("INSERT INTO permits VALUES (?,?,?,?,?,?,?,?)", permits)
    con.executemany("INSERT INTO inspections VALUES (?,?,?,?,?)", inspections)
    con.commit()
    con.close()
    return path


if __name__ == "__main__":
    p = build()
    print(f"Built {p}")
