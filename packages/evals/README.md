# evals

Offline and online evaluation of agent behavior.

## Owns

- Datasets
- Graders (rule-based and LLM judge)
- Suites: quality, safety, regression
- Red team: injection, exfiltration, tenant escape
- CI gate

## Design notes and open decisions

- Eval results must be reproducible: pin model, prompt, tools, and data version.
- Production traces can feed new datasets.

## Layout

- `ci/` CI gate rules and thresholds
- `datasets/` Versioned test cases
- `graders/` Scoring functions
- `redteam/` Adversarial cases and attack harness
- `runners/` Run evals against the runtime
- `suites/` Grouped eval runs (quality, safety, regression)

## Status

Scaffold only. No implementation yet.
