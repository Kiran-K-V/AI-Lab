# contracts

Shared, versioned schemas every other package depends on. No logic.

## Owns

- RunContext (tenant, user, run id, scopes, budget)
- ToolCall / ToolResult
- Approval request and decision
- PolicyDecision
- AuditEvent
- Streaming run events

## Design notes and open decisions

- Pick one schema source of truth (JSON Schema, Protobuf, or Pydantic/Zod) and generate the rest.
- Schema changes need a version bump and a compatibility note.

## Layout

- `schemas/` Schema definitions, one file per contract

## Status

Scaffold only. No implementation yet.
