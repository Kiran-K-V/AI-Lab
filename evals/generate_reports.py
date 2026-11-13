"""Generate synthetic lab report PDFs (some as noisy image-only scans) plus ground-truth JSON.

Usage: uv run python -m evals.generate_reports --count 20 --seed 0

Ground truth is what is PRINTED: value and unit are not converted between unit systems.
Each report rolls a random Style (layout, units, range format, ...). manifest.json lists them.
"""

import argparse
import json
import random
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TypeVar

import pypdfium2
from fpdf import FPDF
from PIL import Image, ImageFilter

from app.models import LabReport, LabResult, Patient, ReferenceRange, ResultStatus, Sex


@dataclass(frozen=True)
class TestSpec:
    name: str
    panel: str
    unit: str
    low: float | None
    high: float | None
    mean: float
    sd: float
    decimals: int
    crit_low: float | None = None
    crit_high: float | None = None
    si_unit: str | None = None  # alternative unit; None = same in both systems
    si_factor: float = 1.0
    si_decimals: int = 0


# fmt: off
CATALOG = [
    TestSpec("Hemoglobin", "Complete Blood Count", "g/dL", 12.0, 17.5, 14.5, 2.5, 1, 7.0, 20.0,
             si_unit="g/L", si_factor=10, si_decimals=0),
    TestSpec("WBC Count", "Complete Blood Count", "x10^3/uL", 4.0, 11.0, 7.5, 3, 1, 2.0, 30.0),
    TestSpec("Glucose, Fasting", "Metabolic Panel", "mg/dL", 70, 99, 95, 30, 0, 40.0, 500.0,
             si_unit="mmol/L", si_factor=0.0555, si_decimals=1),
    TestSpec("Creatinine", "Metabolic Panel", "mg/dL", 0.6, 1.3, 0.95, 0.35, 2, None, 7.4,
             si_unit="umol/L", si_factor=88.4, si_decimals=0),
    TestSpec("Potassium", "Metabolic Panel", "mmol/L", 3.5, 5.1, 4.3, 0.8, 1, 2.8, 6.5),
    TestSpec("Total Cholesterol", "Lipid Panel", "mg/dL", None, 200, 195, 40, 0,
             si_unit="mmol/L", si_factor=0.02586, si_decimals=1),
    TestSpec("HDL Cholesterol", "Lipid Panel", "mg/dL", 40, None, 52, 14, 0,
             si_unit="mmol/L", si_factor=0.02586, si_decimals=2),
    TestSpec("Triglycerides", "Lipid Panel", "mg/dL", None, 150, 130, 60, 0,
             si_unit="mmol/L", si_factor=0.01129, si_decimals=2),
    TestSpec("ALT", "Liver Function", "U/L", 7, 56, 30, 20, 0),
]
# fmt: on

LABS = ["Northside Diagnostics", "Meridian Clinical Laboratory", "Apex Pathology Services"]
FIRST = ["Ava", "Liam", "Noah", "Maya", "Ethan", "Sofia", "Omar", "Priya", "Lucas", "Hana"]
LAST = ["Nguyen", "Patel", "Garcia", "Kim", "Okafor", "Silva", "Brown", "Rossi", "Haddad", "Chen"]

FLAGS = {
    ResultStatus.NORMAL: "",
    ResultStatus.LOW: "L",
    ResultStatus.HIGH: "H",
    ResultStatus.CRITICAL_LOW: "LL",
    ResultStatus.CRITICAL_HIGH: "HH",
}
# range style -> (low and high, high only, low only)
RANGE_STYLES = {
    "dash": ("{lo} - {hi}", "< {hi}", "> {lo}"),
    "tight": ("{lo}-{hi}", "<{hi}", ">{lo}"),
    "words": ("{lo} to {hi}", "up to {hi}", "above {lo}"),
    "inclusive": ("{lo} - {hi}", "<= {hi}", ">= {lo}"),
}
COLUMNS = {
    "table": ["test", "result", "flag", "unit", "range"],
    "table_alt": ["test", "result", "unit", "range", "flag"],
}
WIDTHS = {"test": 50, "result": 25, "flag": 20, "unit": 30, "range": 45}
P_MISSING = 0.15


@dataclass
class Style:
    layout: str  # "table" | "table_alt" | "lines"
    show_flags: bool
    group_panels: bool
    range_style: str
    date_fmt: str
    si_units: bool
    sex_letter: bool
    result_header: str
    range_header: str
    scanned: bool


def roll_style(rng: random.Random, scan_rate: float) -> Style:
    return Style(
        layout=rng.choice(["table", "table_alt", "lines"]),
        show_flags=rng.random() < 0.7,
        group_panels=rng.random() < 0.6,
        range_style=rng.choice(list(RANGE_STYLES)),
        date_fmt=rng.choice(["%Y-%m-%d", "%d/%m/%Y", "%d %b %Y"]),
        si_units=rng.random() < 0.4,
        sex_letter=rng.random() < 0.5,
        result_header=rng.choice(["Result", "Value"]),
        range_header=rng.choice(["Reference Range", "Normal Range", "Ref. Interval"]),
        scanned=rng.random() < scan_rate,
    )


def to_si(s: TestSpec) -> TestSpec:
    if s.si_unit is None:
        return s

    def conv(x: float | None) -> float | None:
        return None if x is None else round(x * s.si_factor, s.si_decimals)

    return replace(
        s,
        unit=s.si_unit,
        low=conv(s.low),
        high=conv(s.high),
        crit_low=conv(s.crit_low),
        crit_high=conv(s.crit_high),
        mean=s.mean * s.si_factor,
        sd=s.sd * s.si_factor,
        decimals=s.si_decimals,
    )


def status_of(value: float, s: TestSpec) -> ResultStatus:
    if s.crit_low is not None and value <= s.crit_low:
        return ResultStatus.CRITICAL_LOW
    if s.crit_high is not None and value >= s.crit_high:
        return ResultStatus.CRITICAL_HIGH
    if s.low is not None and value < s.low:
        return ResultStatus.LOW
    if s.high is not None and value > s.high:
        return ResultStatus.HIGH
    return ResultStatus.NORMAL


T = TypeVar("T")


def maybe(rng: random.Random, value: T) -> T | None:
    """Drop a field with probability P_MISSING."""
    return None if rng.random() < P_MISSING else value


def make_report(rng: random.Random, style: Style, specs: list[TestSpec]) -> LabReport:
    results = []
    for s in specs:
        value = round(max(rng.gauss(s.mean, s.sd), 0.0), s.decimals)
        # Only drop a range if flags are printed, else status would be unknowable.
        drop_range = style.show_flags and rng.random() < 0.1
        results.append(
            LabResult(
                name=s.name,
                value=value,
                unit=None if rng.random() < 0.05 else s.unit,
                reference_range=None if drop_range else ReferenceRange(low=s.low, high=s.high),
                status=status_of(value, s),
                panel=s.panel if style.group_panels else None,
            )
        )
    collected = datetime(2026, 1, 1) + timedelta(
        days=rng.randint(0, 300), hours=rng.randint(6, 11), minutes=rng.randint(0, 59)
    )
    dob = date(1940, 1, 1) + timedelta(days=rng.randint(0, 22000))
    return LabReport(
        lab_name=rng.choice(LABS),
        accession_number=maybe(rng, f"ACC-{rng.randint(100000, 999999)}"),
        patient=Patient(
            name=f"{rng.choice(FIRST)} {rng.choice(LAST)}",
            sex=maybe(rng, rng.choice([Sex.MALE, Sex.FEMALE])),
            date_of_birth=maybe(rng, dob),
            patient_id=maybe(rng, f"P{rng.randint(10000, 99999)}"),
        ),
        ordering_physician=maybe(rng, f"Dr. {rng.choice(FIRST)} {rng.choice(LAST)}"),
        collected_at=collected,
        reported_at=maybe(rng, collected + timedelta(hours=rng.randint(4, 48))),
        results=results,
    )


def fmt(x: float, decimals: int) -> str:
    return f"{x:.{decimals}f}"


def fmt_range(rr: ReferenceRange, decimals: int, style: Style) -> str:
    both, high_only, low_only = RANGE_STYLES[style.range_style]
    lo = None if rr.low is None else fmt(rr.low, decimals)
    hi = None if rr.high is None else fmt(rr.high, decimals)
    if lo is not None and hi is not None:
        return both.format(lo=lo, hi=hi)
    if hi is not None:
        return high_only.format(hi=hi)
    assert lo is not None
    return low_only.format(lo=lo)


def line(*pairs: tuple[str, object | None]) -> str:
    return "    ".join(f"{k}: {v}" for k, v in pairs if v is not None)


def header_lines(report: LabReport, style: Style) -> list[str]:
    p = report.patient

    def d(x: date | datetime | None, extra: str = "") -> str | None:
        return None if x is None else x.strftime(style.date_fmt + extra)

    sex = None
    if p.sex:
        sex = p.sex.value[0].upper() if style.sex_letter else p.sex.value.title()
    lines = [
        line(("Patient", p.name), ("Sex", sex)),
        line(("DOB", d(p.date_of_birth)), ("Patient ID", p.patient_id)),
        line(("Accession", report.accession_number)),
        line(("Ordering Physician", report.ordering_physician)),
        line(("Collected", d(report.collected_at, " %H:%M"))),
        line(("Reported", d(report.reported_at, " %H:%M"))),
    ]
    return [x for x in lines if x]


def render_pdf(report: LabReport, style: Style, specs: list[TestSpec]) -> bytes:
    decimals = {s.name: s.decimals for s in specs}
    headers = {
        "test": "Test",
        "result": style.result_header,
        "flag": "Flag",
        "unit": "Unit",
        "range": style.range_header,
    }
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, report.lab_name, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    for text in header_lines(report, style):
        pdf.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")

    def cells(r: LabResult) -> dict[str, str]:
        d = decimals[r.name]
        rr = r.reference_range
        return {
            "test": r.name,
            "result": fmt(r.value, d),
            "flag": FLAGS[r.status],
            "unit": r.unit or "",
            "range": fmt_range(rr, d, style) if rr else "",
        }

    cols = [
        c for c in COLUMNS.get(style.layout, COLUMNS["table"]) if style.show_flags or c != "flag"
    ]
    for panel in dict.fromkeys(r.panel for r in report.results):
        pdf.ln(4)
        if panel:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, panel, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", size=10)
        group = [r for r in report.results if r.panel == panel]
        if style.layout == "lines":
            for r in group:
                v = cells(r)
                ref = f"(Ref: {v['range']})" if v["range"] else ""
                flag = v["flag"] if style.show_flags else ""
                parts = [v["test"], v["result"], v["unit"], ref, flag]
                pdf.cell(0, 6, "   ".join(x for x in parts if x), new_x="LMARGIN", new_y="NEXT")
        else:
            with pdf.table(col_widths=tuple(WIDTHS[c] for c in cols)) as table:
                header = table.row()
                for c in cols:
                    header.cell(headers[c])
                for r in group:
                    row = table.row()
                    for c in cols:
                        row.cell(cells(r)[c])
    assert pdf.page == 1, "report spilled onto a second page"
    return bytes(pdf.output())


def scan(pdf_bytes: bytes, rng: random.Random) -> Image.Image:
    """Rasterize and degrade: small rotation, blur, speckle noise, grey paper."""
    img = pypdfium2.PdfDocument(pdf_bytes)[0].render(scale=2).to_pil().convert("L")
    img = img.rotate(rng.uniform(-2, 2), expand=True, fillcolor=255)
    img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.4, 1.0)))
    noise = Image.frombytes("L", img.size, rng.randbytes(img.width * img.height))
    return Image.blend(img, noise, rng.uniform(0.05, 0.15))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--scan-rate", type=float, default=0.3, help="fraction as noisy scan PDFs")
    parser.add_argument("--out", type=Path, default=Path("data/synthetic"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    manifest = {}
    for i in range(1, args.count + 1):
        style = roll_style(rng, args.scan_rate)
        chosen = sorted(rng.sample(range(len(CATALOG)), k=rng.randint(4, len(CATALOG))))
        specs = [to_si(CATALOG[j]) if style.si_units else CATALOG[j] for j in chosen]
        report = make_report(rng, style, specs)
        pdf_bytes = render_pdf(report, style, specs)

        stem = args.out / f"report_{i:03d}"
        if style.scanned:
            scan(pdf_bytes, rng).save(stem.with_suffix(".pdf"), "PDF", resolution=144)
        else:
            stem.with_suffix(".pdf").write_bytes(pdf_bytes)
        stem.with_suffix(".json").write_text(report.model_dump_json(indent=2))
        manifest[stem.name] = asdict(style)
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Wrote {args.count} reports to {args.out}")


if __name__ == "__main__":
    main()
