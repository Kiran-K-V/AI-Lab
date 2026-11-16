# tool-gateway

One gateway for every tool and MCP server. Registry, risk tiers, approvals, execution.

## Owns

- Tool registry and MCP catalog
- Risk tiers per tool (read, write, destructive, external)
- Human approval for write actions
- Approval binding: the executed call must match what was approved
- Approval expiry and single use
- Execution through sandbox and egress

## Design notes and open decisions

- Approval is bound to a hash of (tool, canonical args, run, tenant, principal). Any drift voids it.
- Approvals expire. An expired approval means a new request, never a silent retry.
- Check again at execution time, not only at approval time.
- Decide: what happens to an approval if the run was paused for hours.

## Layout

- `approvals/` Human-in-the-loop approval flow for write actions
- `executor/` Runs approved calls
- `mcp-catalog/` Vetted MCP servers: trust level, allowed tools, sandbox profile, pinned version
- `registry/` Tool definitions, schemas, owners, versions, risk tier
- `risk-tiers/` Tier definitions and the rules that map tool + args to a tier

## Status

Scaffold only. No implementation yet.
