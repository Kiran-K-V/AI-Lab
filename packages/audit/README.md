# audit

Append-only audit log shared by guardrails, approvals, policy, egress, and sandbox.

## Owns

- Event writer
- Tamper evidence (hash chain)
- Sinks (DB, object storage, SIEM)
- Query for investigations

## Design notes and open decisions

- Audit write failure on a guarded action must block that action.

## Layout

- `integrity/` Hash chain and tamper checks
- `log/` Event writer and schema use
- `query/` Search and export for investigations and compliance
- `sinks/` Storage and SIEM exporters

## Status

Scaffold only. No implementation yet.
