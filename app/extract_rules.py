"""Extractor 1: no LLM. pdfplumber text lines + regex. Fast, free, deterministic.

Needs a text layer. Scanned PDFs raise ExtractionError; use the LLM extractor for those.
"""

import re
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from app.models import LabReport, LabResult, Patient, ReferenceRange, ResultStatus, Sex
from app.pdf import ExtractionError, read_text

NUM = r"\d+(?:\.\d+)?"
DATE = r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{1,2} [A-Za-z]{3} \d{4}"
DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d %b %Y"]

ROW = re.compile(rf"^(?P<name>[^:\d]+?)\s+(?P<value>{NUM})(?:\s+(?P<rest>.*))?$")
RANGE_BOTH = re.compile(rf"({NUM})\s*(?:-|to)\s*({NUM})")
RANGE_HIGH = re.compile(rf"(?:<=|<|up to)\s*({NUM})")
RANGE_LOW = re.compile(rf"(?:>=|>|above)\s*({NUM})")

FLAG_STATUS = {
    "H": ResultStatus.HIGH,
    "L": ResultStatus.LOW,
    "HH": ResultStatus.CRITICAL_HIGH,
    "LL": ResultStatus.CRITICAL_LOW,
}


def parse_date(s: str) -> datetime:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ExtractionError(f"unrecognised date: {s!r}")


def find(pattern: str, text: str) -> re.Match[str] | None:
    return re.search(pattern, text, re.MULTILINE)


def parse_range(rest: str) -> tuple[ReferenceRange | None, str]:
    """Return the range found in `rest` and `rest` with the range removed."""
    if m := RANGE_BOTH.search(rest):
        rr = ReferenceRange(low=float(m[1]), high=float(m[2]))
    elif m := RANGE_HIGH.search(rest):
        rr = ReferenceRange(high=float(m[1]))
    elif m := RANGE_LOW.search(rest):
        rr = ReferenceRange(low=float(m[1]))
    else:
        return None, rest
    return rr, rest[: m.start()] + rest[m.end() :]


def status_from_range(value: float, rr: ReferenceRange | None) -> ResultStatus:
    if rr is not None and rr.low is not None and value < rr.low:
        return ResultStatus.LOW
    if rr is not None and rr.high is not None and value > rr.high:
        return ResultStatus.HIGH
    return ResultStatus.NORMAL


def parse_results(lines: list[str]) -> list[LabResult]:
    results = []
    panel: str | None = None
    for i, line in enumerate(lines):
        m = ROW.match(line)
        if not m:
            # A line with no digits and no colon, after the lab name, is a panel heading.
            if i > 0 and ":" not in line and not line.startswith("Test"):
                panel = line.strip()
            continue
        value = float(m["value"])
        rest = re.sub(r"\(?Ref:?\s*|\)", "", m["rest"] or "")
        rr, rest = parse_range(rest)
        flag = None
        unit_parts = []
        for tok in rest.split():
            if tok in FLAG_STATUS:
                flag = tok
            else:
                unit_parts.append(tok)
        results.append(
            LabResult(
                name=m["name"].strip(),
                value=value,
                unit=" ".join(unit_parts) or None,
                reference_range=rr,
                status=FLAG_STATUS[flag] if flag else status_from_range(value, rr),
                panel=panel,
            )
        )
    return results


def extract(path: Path) -> LabReport:
    text = read_text(path)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        raise ExtractionError("no text layer (scanned PDF?). Use --method llm.")

    def field(pattern: str) -> str | None:
        m = find(pattern, text)
        return m[1].strip() if m else None

    sex = field(r"Sex:\s*(\S+)")
    dob = field(rf"DOB:\s*({DATE})")
    collected = find(rf"Collected:\s*({DATE})\s+(\d{{2}}:\d{{2}})", text)
    reported = find(rf"Reported:\s*({DATE})\s+(\d{{2}}:\d{{2}})", text)

    def when(m: re.Match[str] | None) -> datetime | None:
        if not m:
            return None
        return datetime.combine(parse_date(m[1]).date(), datetime.strptime(m[2], "%H:%M").time())

    name = field(r"^Patient:\s*(.+?)(?:\s+Sex:.*)?$")
    if name is None:
        raise ExtractionError("patient name not found")
    try:
        return LabReport(
            lab_name=lines[0],
            accession_number=field(r"Accession:\s*(\S+)"),
            patient=Patient(
                name=name,
                sex=Sex.MALE if sex and sex[0] in "Mm" else Sex.FEMALE if sex else None,
                date_of_birth=parse_date(dob).date() if dob else None,
                patient_id=field(r"Patient ID:\s*(\S+)"),
            ),
            ordering_physician=field(r"Ordering Physician:\s*(.+)$"),
            collected_at=when(collected),
            reported_at=when(reported),
            results=parse_results(lines),
        )
    except ValidationError as e:
        raise ExtractionError(f"extracted data is invalid: {e}") from e
