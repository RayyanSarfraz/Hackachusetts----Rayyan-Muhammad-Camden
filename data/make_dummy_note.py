"""
Generate a dependency-free, valid PDF containing a fictional patient note.

The intake tray extracts text with pdf.js, so the PDF must contain real,
selectable text (not an image). This writes each line as a Tj show-text op in a
single Helvetica page. Fictional/demo data only.
"""
from __future__ import annotations

from pathlib import Path

# Fictional clinical note. Written in plain, declarative sentences and with the
# primary condition stated up front, so the extraction model reliably picks it
# up (dense chart-style layouts tended to yield "primary condition: none").
LINES = [
    "FICTIONAL PATIENT NOTE - DEMO DATA ONLY",
    "",
    "The patient is a 54-year-old female.",
    "The patient's primary condition is Type 2 Diabetes.",
    "The patient lives in Boston, Massachusetts.",
    "",
    "The patient has Type 2 Diabetes, diagnosed in 2017.",
    "The patient also has high blood pressure (hypertension).",
    "The patient also has high cholesterol (hyperlipidemia).",
    "",
    "Symptoms: the patient reports fatigue, blurred vision, and numbness",
    "in both feet.",
    "",
    "Current medications: the patient takes Metformin 1000 mg twice daily",
    "for diabetes. The patient takes Lisinopril 20 mg once daily for blood",
    "pressure. The patient takes Atorvastatin 40 mg once daily for",
    "cholesterol.",
    "",
    "Laboratory results: HbA1c is 7.8 percent. Fasting glucose is 148",
    "mg/dL. Blood pressure is 132/84 mmHg.",
    "",
    "The patient is looking for clinical trials for Type 2 Diabetes.",
    "The patient prefers studies within 50 miles with no overnight stays.",
]


def _escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def build_pdf(lines: list[str]) -> bytes:
    # Content stream: a single text block, one line per input line.
    leading = 16  # points between baselines
    start_y = 740
    parts = ["BT", "/F1 11 Tf", f"{leading} TL", f"72 {start_y} Td"]
    for i, line in enumerate(lines):
        if i == 0:
            parts.append(f"({_escape(line)}) Tj")
        else:
            parts.append(f"T* ({_escape(line)}) Tj")
    parts.append("ET")
    content = "\n".join(parts).encode("latin-1")

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
    )
    objects.append(
        b"<< /Length "
        + str(len(content)).encode()
        + b" >>\nstream\n"
        + content
        + b"\nendstream"
    )
    objects.append(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
        b"/Encoding /WinAnsiEncoding >>"
    )

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"

    xref_pos = len(out)
    n = len(objects) + 1
    out += f"xref\n0 {n}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {n} /Root 1 0 R >>\nstartxref\n{xref_pos}\n".encode()
    )
    out += b"%%EOF"
    return bytes(out)


# Second fictional patient: a medical-history note for Major Depressive
# Disorder (another condition well covered in the MA trial dataset). Same plain,
# condition-first style so extraction is reliable.
HISTORY_LINES = [
    "FICTIONAL PATIENT MEDICAL HISTORY - DEMO DATA ONLY",
    "",
    "The patient is a 31-year-old male.",
    "The patient's primary condition is Major Depressive Disorder.",
    "The patient lives in Cambridge, Massachusetts.",
    "",
    "Medical history:",
    "The patient was diagnosed with Major Depressive Disorder in 2021.",
    "The patient also has generalized anxiety.",
    "The patient has no history of psychosis or bipolar disorder.",
    "",
    "Symptoms: the patient reports low mood, loss of interest, poor sleep,",
    "and difficulty concentrating.",
    "",
    "Current medications: the patient takes Sertraline 100 mg once daily",
    "for depression.",
    "",
    "Previous treatments: the patient tried Fluoxetine in 2021, which was",
    "stopped due to side effects. The patient completed a course of",
    "cognitive behavioral therapy in 2022.",
    "",
    "The patient is looking for clinical trials for depression.",
    "The patient prefers studies in the Boston area.",
]


if __name__ == "__main__":
    notes = {
        "dummy-patient-note.pdf": LINES,
        "dummy-patient-history.pdf": HISTORY_LINES,
    }
    for filename, lines in notes.items():
        dest = Path(__file__).with_name(filename)
        dest.write_bytes(build_pdf(lines))
        print(f"Wrote {dest} ({dest.stat().st_size} bytes)")
