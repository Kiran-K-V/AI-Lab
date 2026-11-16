# guardrails

Checks at four points. Fail closed. Every decision is audited.

## Owns

- Checkpoint: input
- Checkpoint: tool call
- Checkpoint: tool result
- Checkpoint: output
- Detector plug-ins (injection, PII, policy, toxicity)
- Fail-closed engine

## Design notes and open decisions

- Fail closed: a guardrail error or timeout means block, not allow.
- Tool results are untrusted input. Check them for injection before the model sees them.
- Every decision writes an audit event (allow, block, modify, error).

## Layout

- `checkpoints/` One folder per checkpoint
- `detectors/` Reusable detectors shared by checkpoints
- `engine/` Runs detectors, merges verdicts, enforces fail-closed

## Status

Scaffold only. No implementation yet.
