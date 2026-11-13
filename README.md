# AI-Lab

Lab report extraction. Pydantic schema in `app/models.py`, synthetic report generator in `evals/generate_reports.py`.

```bash
uv sync
uv run python -m evals.generate_reports --count 50 --seed 1 --out data/synthetic/dev
uv run python -m evals.generate_reports --count 50 --seed 2 --out data/synthetic/test
```

Dev and test sets use different seeds, so they share no reports. Each folder has:
- `report_NNN.pdf`: the input. Some are image-only noisy scans (no text layer).
- `report_NNN.json`: the correct answer, exactly as printed (no unit conversion).
- `manifest.json`: the random style of each report (layout, units, range format, ...), for slicing errors.
