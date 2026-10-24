#!/usr/bin/env python3
"""Build client/src/data/nsclcTrials.json from the Hackachusetts CSV and ClinicalTrials.gov.

Usage:
    python client/scripts/build_nsclc_trials.py [path/to/data.csv] [--dry-run]

CSV path: first argument, else env HACKACHUSETTS_TRIALS_CSV, else
~/Downloads/healthcare/trials/data.csv. With --dry-run every check runs but
the JSON file is not written.

Standard library only. The JSON is written only after every check passes, so a
failed run leaves the committed file untouched.
"""
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SELECTED_IDS = [
    "NCT04410796",
    "NCT04181060",
    "NCT03191149",
    "NCT07291037",
    "NCT06767514",
    "NCT07063745",
    "NCT06119581",
    "NCT05920356",
]

API_URL = "https://clinicaltrials.gov/api/v2/studies"
OUT_PATH = Path(__file__).resolve().parent.parent / "src" / "data" / "nsclcTrials.json"
DEFAULT_CSV = Path.home() / "Downloads" / "healthcare" / "trials" / "data.csv"

# Hand-set approximate miles from Boston. Extend by hand when a new city appears.
MILES_FROM_BOSTON = {
    "Boston": 2,
    "Burlington": 13,
    "Peabody": 15,
    "Beverly": 18,
    "Worcester": 40,
    "Springfield": 80,
}

KIND_ORDER = ["condition", "age", "egfr", "stage", "ecog"]
DEPENDS_ON = {
    "condition": ["condition"],
    "age": ["age"],
    "egfr": ["egfrStatus"],
    "stage": ["cancerStage"],
    "ecog": ["ecogStatus"],
}
EFFORT = {"condition": 1, "age": 1, "egfr": 1, "stage": 3, "ecog": 3}

# Per trial, per kind: substring of the normalized eligibility text, rule, category.
# "age" with substring None uses the listing's minimumAge/maximumAge fallback.
# The condition criterion never has a rule.
CONFIG = {
    "NCT04410796": {
        "condition": {"substring": "Biopsy proven metastatic non-small cell lung cancer"},
        "age": {"substring": "Age ≥ 18 years", "rule": {"minAge": 18}},
        "egfr": {"substring": "Somatic activating mutation in EGFR", "rule": {"egfr": "positive"}},
        "stage": {"substring": "Biopsy proven metastatic non-small cell lung cancer", "rule": {"stages": ["IV"]}},
        # No ECOG criterion: this trial uses Karnofsky performance status.
    },
    "NCT04181060": {
        "condition": {"substring": "pathologically-confirmed diagnosis of non-squamous, non-small cell lung cancer"},
        "age": {"substring": "Patient must be ≥ 18 years of age", "rule": {"minAge": 18}},
        "egfr": {"substring": "somatic activating sensitizing mutation in EGFR", "rule": {"egfr": "positive"}},
        "stage": {"substring": "Patient must have advanced disease", "rule": {"stages": ["III", "IV"]}},
        "ecog": {"substring": "performance status of 0 to 2", "rule": {"ecogMax": 2}},
    },
    "NCT03191149": {
        "condition": {"substring": "pathologically-confirmed diagnosis of non-small cell lung cancer (NSCLC)"},
        "age": {"substring": "Age >= 18 years", "rule": {"minAge": 18}},
        "egfr": {"substring": "An EGFR exon 20 insertion mutation must be detected", "rule": {"egfr": "positive"}},
        "stage": {"substring": "Participants must have advanced disease", "rule": {"stages": ["III", "IV"]}},
        "ecog": {"substring": "performance status =< 1", "rule": {"ecogMax": 1}},
    },
    "NCT07291037": {
        "condition": {"substring": "Pathologically documented Stage IIIB, IIIC, or Stage IV non-squamous"},
        "age": {"substring": None},
        "egfr": {"substring": "documented negative test results for EGFR", "rule": {"egfr": "negative"}},
        "stage": {"substring": "Pathologically documented Stage IIIB, IIIC, or Stage IV non-squamous", "rule": {"stages": ["III", "IV"]}},
        "ecog": {"substring": "Performance Status (PS) of 0 or 1", "rule": {"ecogMax": 1}},
    },
    "NCT06767514": {
        "condition": {"substring": "Histologically or cytologically confirmed squamous or non-squamous NSCLC"},
        "age": {"substring": "Age ≥ 18 years old at the time of enrollment", "rule": {"minAge": 18}},
        "egfr": {
            "substring": "Known actionable genomic alterations for which first-line approved therapies are indicated",
            "rule": {"egfr": "negative"},
            "category": "exclusion",
        },
        "stage": {"substring": "Metastatic (Stage IV) NSCLC", "rule": {"stages": ["IV"]}},
        "ecog": {"substring": "performance status score of 0 - 1", "rule": {"ecogMax": 1}},
    },
    "NCT07063745": {
        "condition": {"substring": "histologically confirmed diagnosis of NSCLC and homozygous"},
        "age": {"substring": None},
        "egfr": {
            "substring": "Nonsquamous participants must not have documented targetable oncogenic mutation",
            "rule": {"egfr": "negative"},
            "category": "exclusion",
        },
        "stage": {"substring": "Participants must have Metastatic (Stage IV or recurrent)", "rule": {"stages": ["IV"]}},
        "ecog": {"substring": "performance status of 0-1", "rule": {"ecogMax": 1}},
    },
    "NCT06119581": {
        "condition": {"substring": "confirmed NSCLC with Stage IIIB-IIIC or Stage IV disease"},
        "age": {"substring": None},
        "stage": {"substring": "confirmed NSCLC with Stage IIIB-IIIC or Stage IV disease", "rule": {"stages": ["III", "IV"]}},
        "ecog": {"substring": "Must have an ECOG performance status of 0 or 1", "rule": {"ecogMax": 1}},
    },
    "NCT05920356": {
        "condition": {"substring": "diagnosis of nonsquamous stage IV or advanced Stage IIIB or IIIC NSCLC"},
        "age": {"substring": None},
        "stage": {"substring": "diagnosis of nonsquamous stage IV or advanced Stage IIIB or IIIC NSCLC", "rule": {"stages": ["III", "IV"]}},
        "ecog": {"substring": "Eastern Cooperative Oncology Group (ECOG) ≤ 1", "rule": {"ecogMax": 1}},
    },
}

BULLET_RE = re.compile(r"^\s*[*+-]\s+")
ESCAPE_RE = re.compile(r"\\([^\w\s])")


def fail(message):
    print(message, file=sys.stderr)
    sys.exit(1)


def normalize(text):
    """Unescape ctgov backslash escapes and strip leading markdown bullets per line.

    Unescaping runs first so escaped bullets such as "\\- text" are stripped too.
    """
    lines = []
    for line in text.splitlines():
        line = ESCAPE_RE.sub(r"\1", line)
        line = BULLET_RE.sub("", line)
        lines.append(line)
    return "\n".join(lines)


def resolve_csv_path(args):
    if args:
        return Path(args[0]).expanduser()
    env = os.environ.get("HACKACHUSETTS_TRIALS_CSV")
    if env:
        return Path(env).expanduser()
    return DEFAULT_CSV


def read_csv(path):
    if not path.is_file():
        fail(f"CSV not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = {row["nct_id"].strip(): row for row in csv.DictReader(handle)}
    missing = [nct for nct in SELECTED_IDS if nct not in rows]
    if missing:
        for nct in missing:
            print(f"Missing from CSV: {nct}", file=sys.stderr)
        sys.exit(1)
    return rows


def fetch_studies():
    query = urllib.parse.urlencode({"filter.ids": ",".join(SELECTED_IDS), "pageSize": 10})
    request = urllib.request.Request(
        f"{API_URL}?{query}",
        headers={"Accept": "application/json", "User-Agent": "hackachusetts-build-nsclc-trials/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError) as error:
        fail(f"ClinicalTrials.gov request failed: {error}")
    studies = {}
    for study in payload.get("studies", []):
        nct = study.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
        if nct:
            studies[nct] = study
    missing = [nct for nct in SELECTED_IDS if nct not in studies]
    if missing:
        fail(f"Missing from ClinicalTrials.gov response: {', '.join(missing)}")
    return studies


def find_line(nct, normalized, substring):
    for line in normalized.splitlines():
        if substring in line:
            return line.strip()
    fail(f"{nct}: substring not found in eligibility text: {substring!r}")


def parse_years(value):
    match = re.match(r"\s*(\d+)\s*Year", value or "")
    return int(match.group(1)) if match else None


def age_fallback(nct, eligibility):
    minimum = eligibility.get("minimumAge")
    maximum = eligibility.get("maximumAge")
    parts = []
    rule = {}
    if minimum:
        parts.append(f"minimum age {minimum}")
        years = parse_years(minimum)
        if years is None:
            fail(f"{nct}: cannot parse minimumAge {minimum!r}")
        rule["minAge"] = years
    if maximum:
        parts.append(f"maximum age {maximum}")
        years = parse_years(maximum)
        if years is None:
            fail(f"{nct}: cannot parse maximumAge {maximum!r}")
        rule["maxAge"] = years
    if not parts:
        fail(f"{nct}: no age line configured and no minimumAge/maximumAge in listing")
    return "ClinicalTrials.gov listing: " + ", ".join(parts), rule


def pick_location(nct, study):
    locations = study.get("protocolSection", {}).get("contactsLocationsModule", {}).get("locations", [])
    for location in locations:
        if location.get("state") == "Massachusetts":
            facility = location.get("facility")
            city = location.get("city")
            if city not in MILES_FROM_BOSTON:
                fail(f"{nct}: city {city!r} not in MILES_FROM_BOSTON; add it by hand")
            return f"{facility}, {city}, MA", MILES_FROM_BOSTON[city]
    fail(f"{nct}: no Massachusetts location")


def build_trial(nct, row, study):
    eligibility = study.get("protocolSection", {}).get("eligibilityModule", {})
    normalized = normalize(eligibility.get("eligibilityCriteria", ""))
    criteria = []
    for kind in KIND_ORDER:
        entry = CONFIG[nct].get(kind)
        if entry is None:
            continue
        substring = entry.get("substring")
        rule = entry.get("rule")
        if substring is None:
            if kind != "age":
                fail(f"{nct}: {kind} criterion has no substring")
            text, rule = age_fallback(nct, eligibility)
        else:
            text = find_line(nct, normalized, substring)
        criterion = {
            "id": f"{nct}-{kind}",
            "text": text,
            "category": entry.get("category", "inclusion"),
            "dependsOn": DEPENDS_ON[kind],
            "estimatedEffort": EFFORT[kind],
            "kind": kind,
        }
        if rule and kind != "condition":
            criterion["rule"] = rule
        criteria.append(criterion)

    location, miles = pick_location(nct, study)
    return {
        "id": nct,
        "nctId": nct,
        "name": row["title"].strip(),
        "phase": row["phase"].strip(),
        "recruitmentStatus": row["status"].strip(),
        "sourceUrl": f"https://clinicaltrials.gov/study/{nct}",
        "sourceLabel": "ClinicalTrials.gov",
        "location": location,
        "distance": {"miles": miles, "label": "approximate"},
        "criteria": criteria,
    }


def main(argv):
    dry_run = "--dry-run" in argv
    args = [arg for arg in argv if arg != "--dry-run"]
    rows = read_csv(resolve_csv_path(args))
    studies = fetch_studies()
    trials = [build_trial(nct, rows[nct], studies[nct]) for nct in SELECTED_IDS]
    output = json.dumps(trials, indent=2, ensure_ascii=False) + "\n"
    if dry_run:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(output)
        return
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(output, encoding="utf-8", newline="\n")
    print(f"Wrote {len(trials)} trials to {OUT_PATH}")


if __name__ == "__main__":
    main(sys.argv[1:])
