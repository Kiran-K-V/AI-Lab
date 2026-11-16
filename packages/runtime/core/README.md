# core

SDK-agnostic agent core.

## Layout

- `events/` Run event types and the stream that apps and observability consume
- `loop/` Run loop: plan, act, observe, stop
- `ports/` Interfaces the core calls out to (model, tools, memory, guardrails, identity, audit)
- `state/` Run state model and checkpointing

## Status

Scaffold only. No implementation yet.
