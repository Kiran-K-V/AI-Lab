# runtime

Agent runtime. SDK-agnostic core plus thin adapters for each agent SDK.

## Owns

- Run loop, state machine, event stream
- Ports (interfaces) the core needs: model, tools, memory, guardrails, policy
- Adapters that map each SDK onto those ports

## Design notes and open decisions

- The core must not import any agent SDK. Only adapters may.
- Every adapter must pass the same conformance suite.
- Decide: sync vs async run loop, resumable runs, how a run pauses for approval.

## Layout

- `adapters/` One folder per agent SDK
- `conformance/` Shared test suite every adapter must pass
- `core/` SDK-agnostic agent core

## Status

Scaffold only. No implementation yet.
