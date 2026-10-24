"""
Generate realistic *fictional* dummy patient history data for TrialBridge intake
testing, in every format the intake tray accepts (PDF, TXT, CSV, JSON, XML).

The intake tray (client/src/lib/normalize.ts) parses:
  - PDF  -> pdf.js text extraction (needs selectable text)
  - CSV  -> "header: value" pairs per row
  - JSON -> FHIR Bundle summary (Patient/Condition/Observation/Medication*/
            AllergyIntolerance/Procedure) or a flattened key/value dump
  - XML  -> Apple Health export (<HealthData><Me/><Record/></HealthData>)
  - TXT  -> used as-is

So each format here is shaped to match what those parsers look for, giving a
realistic end-to-end test of the upload paths.

ALL DATA IS FICTIONAL / DEMO ONLY. Not real patients. Not for clinical use.

Run:  python data/make_dummy_patients.py
Output: data/patients/<name>.<ext>
"""
from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

OUT_DIR = Path(__file__).with_name("patients")


# --------------------------------------------------------------------------- #
# Patient model (one source of truth; each exporter renders a subset)
# --------------------------------------------------------------------------- #
@dataclass
class Med:
    name: str
    dosage: str
    status: str = "active"  # active | discontinued


@dataclass
class Lab:
    name: str
    value: str
    unit: str = ""
    date: str = ""


@dataclass
class Patient:
    slug: str
    name: str
    mrn: str
    age: int
    birth_date: str
    sex: str  # female | male
    city: str
    state: str
    chief_complaint: str
    hpi: str
    conditions: list[str]
    symptoms: list[str]
    medications: list[Med]
    previous_treatments: list[str]
    allergies: list[str]
    labs: list[Lab]
    plan: str
    note_date: str = field(default_factory=lambda: date.today().isoformat())


PATIENTS: list[Patient] = [
    Patient(
        slug="marcus-chen-nsclc",
        name="Marcus Chen",
        mrn="DEMO-10231",
        age=63,
        birth_date="1963-03-12",
        sex="male",
        city="Worcester",
        state="MA",
        chief_complaint="Persistent cough and unintended weight loss over 2 months.",
        hpi=(
            "63-year-old former smoker (30 pack-years, quit 2015) with a "
            "biopsy-confirmed stage IIIB non-small cell lung carcinoma, presenting "
            "with worsening dyspnea on exertion and a 12-pound weight loss."
        ),
        conditions=[
            "Non-small cell lung cancer (stage IIIB, dx 2026-08)",
            "COPD",
            "Hypertension",
        ],
        symptoms=["Chronic cough", "Dyspnea on exertion", "Fatigue", "Weight loss"],
        medications=[
            Med("Carboplatin", "AUC 5 IV, every 3 weeks"),
            Med("Paclitaxel", "200 mg/m2 IV, every 3 weeks"),
            Med("Amlodipine", "10 mg, once daily"),
            Med("Albuterol inhaler", "2 puffs, as needed"),
        ],
        previous_treatments=[
            "Lobectomy evaluation - deferred (locally advanced)",
            "Smoking cessation program (2015)",
        ],
        allergies=["Penicillin (rash)"],
        labs=[
            Lab("ECOG performance status", "1", "", "2026-10-15"),
            Lab("Hemoglobin", "11.2", "g/dL", "2026-10-15"),
            Lab("Platelets", "180", "x10^9/L", "2026-10-15"),
            Lab("Creatinine", "0.9", "mg/dL", "2026-10-15"),
            Lab("EGFR mutation", "negative", "", "2026-09-02"),
            Lab("PD-L1 expression", "45%", "", "2026-09-02"),
        ],
        plan=(
            "Discuss immunotherapy and targeted-therapy clinical trials for stage "
            "III NSCLC. Continue current chemotherapy cycle. Patient willing to "
            "travel up to 75 miles; open to overnight stays for infusion visits."
        ),
    ),
    Patient(
        slug="sofia-ramirez-ra",
        name="Sofia Ramirez",
        mrn="DEMO-10244",
        age=41,
        birth_date="1985-07-28",
        sex="female",
        city="Cambridge",
        state="MA",
        chief_complaint="Joint pain and morning stiffness in hands and wrists.",
        hpi=(
            "41-year-old woman with seropositive rheumatoid arthritis diagnosed in "
            "2021, reporting increasing morning stiffness lasting over an hour and "
            "swelling in the metacarpophalangeal joints despite methotrexate."
        ),
        conditions=[
            "Rheumatoid arthritis (seropositive, dx 2021)",
            "Hypothyroidism",
            "Vitamin D deficiency",
        ],
        symptoms=[
            "Symmetric joint pain",
            "Morning stiffness",
            "Hand and wrist swelling",
            "Fatigue",
        ],
        medications=[
            Med("Methotrexate", "20 mg, once weekly"),
            Med("Folic acid", "1 mg, daily"),
            Med("Levothyroxine", "75 mcg, once daily"),
            Med("Hydroxychloroquine", "200 mg, twice daily"),
            Med("Prednisone", "5 mg, once daily", status="discontinued"),
        ],
        previous_treatments=[
            "Sulfasalazine (discontinued 2022, GI intolerance)",
            "Physical therapy for hand function (2023)",
        ],
        allergies=["No known drug allergies"],
        labs=[
            Lab("Anti-CCP antibody", "positive", "", "2026-09-30"),
            Lab("Rheumatoid factor", "88", "IU/mL", "2026-09-30"),
            Lab("CRP", "14", "mg/L", "2026-10-10"),
            Lab("ESR", "42", "mm/hr", "2026-10-10"),
            Lab("TSH", "2.1", "mIU/L", "2026-10-10"),
        ],
        plan=(
            "Consider biologic DMARD trials for moderate-to-severe RA inadequately "
            "controlled on methotrexate. Patient prefers studies within 30 miles "
            "and wants to avoid overnight stays."
        ),
    ),
    Patient(
        slug="eleanor-whitfield-chf",
        name="Eleanor Whitfield",
        mrn="DEMO-10258",
        age=72,
        birth_date="1954-11-05",
        sex="female",
        city="Springfield",
        state="MA",
        chief_complaint="Shortness of breath and ankle swelling, worse when lying flat.",
        hpi=(
            "72-year-old woman with heart failure with reduced ejection fraction "
            "(HFrEF, EF 35%) and chronic kidney disease stage 3, presenting with "
            "progressive orthopnea, bilateral lower-extremity edema, and a 6-pound "
            "weight gain over one week."
        ),
        conditions=[
            "Heart failure with reduced ejection fraction (EF 35%)",
            "Chronic kidney disease, stage 3",
            "Atrial fibrillation",
            "Type 2 diabetes mellitus",
        ],
        symptoms=["Orthopnea", "Lower-extremity edema", "Fatigue", "Palpitations"],
        medications=[
            Med("Furosemide", "40 mg, twice daily"),
            Med("Carvedilol", "12.5 mg, twice daily"),
            Med("Sacubitril/valsartan", "49/51 mg, twice daily"),
            Med("Apixaban", "5 mg, twice daily"),
            Med("Empagliflozin", "10 mg, once daily"),
        ],
        previous_treatments=[
            "Cardiac catheterization (2024, no intervention)",
            "Cardioversion for atrial fibrillation (2023)",
        ],
        allergies=["Sulfa drugs (hives)"],
        labs=[
            Lab("NT-proBNP", "2450", "pg/mL", "2026-10-19"),
            Lab("Ejection fraction", "35", "%", "2026-09-14"),
            Lab("eGFR", "48", "mL/min/1.73m2", "2026-10-19"),
            Lab("Potassium", "4.6", "mmol/L", "2026-10-19"),
            Lab("HbA1c", "6.9", "%", "2026-10-02"),
        ],
        plan=(
            "Evaluate for HFrEF device and drug trials. Optimize diuresis. Patient "
            "has limited mobility; prefers trial sites within 25 miles and no "
            "overnight stays."
        ),
    ),
]


# --------------------------------------------------------------------------- #
# PDF (dependency-free; selectable text so pdf.js extracts it)
# --------------------------------------------------------------------------- #
def _pdf_escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def build_pdf(lines: list[str]) -> bytes:
    leading = 15
    start_y = 750
    parts = ["BT", "/F1 10 Tf", f"{leading} TL", f"54 {start_y} Td"]
    for i, line in enumerate(lines):
        # pdf.js needs WinAnsi-safe bytes; approximate a couple of unicode chars.
        line = line.replace("\u2014", "-").replace("\u2013", "-").replace("\u2265", ">=")
        parts.append(f"({_pdf_escape(line)}) Tj" if i == 0 else f"T* ({_pdf_escape(line)}) Tj")
    parts.append("ET")
    content = "\n".join(parts).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_pos = len(out)
    n = len(objects) + 1
    out += f"xref\n0 {n}\n".encode() + b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {n} /Root 1 0 R >>\nstartxref\n{xref_pos}\n".encode()
    out += b"%%EOF"
    return bytes(out)


def note_lines(p: Patient) -> list[str]:
    lines = [
        "CONFIDENTIAL PATIENT INTAKE NOTE  (FICTIONAL - DEMO DATA ONLY)",
        "",
        f"Patient: {p.name}          MRN: {p.mrn}",
        f"Age: {p.age}        Sex: {p.sex.title()}         Date: {p.note_date}",
        f"Location: {p.city}, {p.state}",
        "",
        "CHIEF COMPLAINT",
        p.chief_complaint,
        "",
        "HISTORY OF PRESENT ILLNESS",
    ]
    lines += _wrap(p.hpi)
    lines += ["", "ACTIVE DIAGNOSES / CONDITIONS"] + [f"- {c}" for c in p.conditions]
    lines += ["", "SYMPTOMS", ", ".join(p.symptoms) + "."]
    lines += ["", "CURRENT MEDICATIONS"] + [
        f"- {m.name} {m.dosage} ({m.status})" for m in p.medications
    ]
    lines += ["", "PREVIOUS TREATMENTS"] + [f"- {t}" for t in p.previous_treatments]
    lines += ["", "ALLERGIES", ", ".join(p.allergies) + "."]
    lines += ["", "LABS / MEASUREMENTS"] + [
        f"- {l.name}: {l.value}{(' ' + l.unit) if l.unit else ''}"
        f"{('  (' + l.date + ')') if l.date else ''}"
        for l in p.labs
    ]
    lines += ["", "ASSESSMENT / PLAN"] + _wrap(p.plan)
    return lines


def _wrap(text: str, width: int = 92) -> list[str]:
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out


# --------------------------------------------------------------------------- #
# TXT
# --------------------------------------------------------------------------- #
def build_txt(p: Patient) -> str:
    return "\n".join(note_lines(p)) + "\n"


# --------------------------------------------------------------------------- #
# CSV (lab-results table; tray renders "header: value" per row)
# --------------------------------------------------------------------------- #
def build_csv(p: Patient) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["test", "result", "unit", "date", "reference_range"])
    for l in p.labs:
        w.writerow([l.name, l.value, l.unit, l.date, ""])
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# JSON (FHIR R4 bundle — matches tryFhirBundle in normalize.ts)
# --------------------------------------------------------------------------- #
def _codeable(text: str) -> dict:
    return {"text": text}


def build_fhir(p: Patient) -> str:
    entries: list[dict] = []

    entries.append(
        {
            "resource": {
                "resourceType": "Patient",
                "id": p.slug,
                "gender": p.sex,
                "birthDate": p.birth_date,
                "name": [{"text": p.name}],
                "address": [{"city": p.city, "state": p.state}],
            }
        }
    )
    for c in p.conditions:
        entries.append(
            {"resource": {"resourceType": "Condition", "code": _codeable(c),
                          "clinicalStatus": _codeable("active")}}
        )
    for l in p.labs:
        obs: dict = {"resourceType": "Observation", "status": "final",
                     "code": _codeable(l.name), "effectiveDateTime": l.date}
        # Numeric labs -> valueQuantity; non-numeric -> valueString.
        try:
            float(l.value)
            obs["valueQuantity"] = {"value": float(l.value), "unit": l.unit}
        except ValueError:
            obs["valueString"] = l.value
        entries.append({"resource": obs})
    for m in p.medications:
        entries.append(
            {
                "resource": {
                    "resourceType": "MedicationStatement",
                    "status": "active" if m.status == "active" else "stopped",
                    "medicationCodeableConcept": _codeable(f"{m.name} {m.dosage}"),
                }
            }
        )
    for a in p.allergies:
        if a.lower().startswith("no known"):
            continue
        entries.append(
            {"resource": {"resourceType": "AllergyIntolerance", "code": _codeable(a)}}
        )
    for t in p.previous_treatments:
        entries.append(
            {"resource": {"resourceType": "Procedure", "status": "completed",
                          "code": _codeable(t)}}
        )

    bundle = {"resourceType": "Bundle", "type": "collection", "entry": entries}
    return json.dumps(bundle, indent=2)


# --------------------------------------------------------------------------- #
# XML (Apple Health export.xml — matches appleHealthToText in normalize.ts)
# --------------------------------------------------------------------------- #
def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_apple_health(p: Patient) -> str:
    sex_map = {"female": "HKBiologicalSexFemale", "male": "HKBiologicalSexMale"}
    rows = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<HealthData locale=\"en_US\">",
        f'  <Me HKCharacteristicTypeIdentifierBiologicalSex="{sex_map.get(p.sex, "HKBiologicalSexNotSet")}" '
        f'HKCharacteristicTypeIdentifierDateOfBirth="{p.birth_date}"/>',
    ]
    for l in p.labs:
        unit = f' unit="{_xml_escape(l.unit)}"' if l.unit else ""
        d = l.date or p.note_date
        rows.append(
            f'  <Record type="HKQuantityTypeIdentifier{_xml_escape(l.name.replace(" ", ""))}" '
            f'value="{_xml_escape(l.value)}"{unit} '
            f'startDate="{d} 09:00:00 -0500" endDate="{d} 09:00:00 -0500"/>'
        )
    rows.append("</HealthData>")
    return "\n".join(rows) + "\n"


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written: list[tuple[str, int]] = []

    # Rotate formats so each patient demonstrates a different real-world export,
    # and also give everyone a PDF note (the primary intake path).
    exporters = {
        "pdf": lambda p: build_pdf(note_lines(p)),
        "txt": lambda p: build_txt(p).encode("utf-8"),
        "csv": lambda p: build_csv(p).encode("utf-8"),
        "json": lambda p: build_fhir(p).encode("utf-8"),
        "xml": lambda p: build_apple_health(p).encode("utf-8"),
    }

    # Everyone gets a PDF note.
    for p in PATIENTS:
        for ext in ("pdf", "txt", "csv", "json", "xml"):
            data = exporters[ext](p)
            dest = OUT_DIR / f"{p.slug}.{ext}"
            dest.write_bytes(data)
            written.append((str(dest.relative_to(OUT_DIR.parent)), len(data)))

    width = max(len(name) for name, _ in written)
    for name, size in written:
        print(f"  {name.ljust(width)}  {size:>6} bytes")
    print(f"\nWrote {len(written)} files for {len(PATIENTS)} fictional patients -> {OUT_DIR}")


if __name__ == "__main__":
    main()
