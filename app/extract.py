"""CLI: uv run python -m app.extract report.pdf [--method rules|llm] [--model MODEL]"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from app.pdf import ExtractionError


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Extract a lab report PDF to JSON.")
    parser.add_argument("file", type=Path)
    parser.add_argument("--method", choices=["rules", "llm"], default="rules")
    parser.add_argument("--model", help="Groq model (llm method only)")
    args = parser.parse_args()

    try:
        if args.method == "rules":
            from app import extract_rules

            report = extract_rules.extract(args.file)
        else:
            from app import extract_llm

            report = extract_llm.extract(args.file, model=args.model or extract_llm.DEFAULT_MODEL)
    except (ExtractionError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # API errors, missing key
        print(f"error: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    print(report.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
