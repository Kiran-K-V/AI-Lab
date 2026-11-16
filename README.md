# AI-Lab: Agent Platform Scaffold

Boilerplate for a secure, multi-tenant agent platform.
This repo is a **scaffold only**. Every folder has a README that states its purpose and open decisions. No implementation yet.

## Principles

1. **The agent is untrusted.** It holds no keys, no long-lived credentials, and no direct network access.
2. **One door per concern.** Models go through the model gateway. Tools go through the tool gateway. Traffic leaves through egress.
3. **Fail closed.** If a guardrail, policy check, or audit write fails, the action is blocked.
4. **Identity travels with the run.** Tenant, user, and scopes are in a run-scoped token. Every layer checks it.
5. **Core is SDK-agnostic.** Agent SDKs are adapters. Swap them without touching the platform.

## Map

| # | Topic | Folder |
|---|-------|--------|
| 1 | Agent runtime (SDK-agnostic core + adapters) | [packages/runtime](packages/runtime) |
| 2 | Model gateway (routing, fallbacks, budgets) | [packages/model-gateway](packages/model-gateway) |
| 3 | Tools and MCP (registry, risk tiers, approvals) | [packages/tool-gateway](packages/tool-gateway) |
| 4 | Identity and access (SSO/SCIM, tokens, OBO, policy, tenancy) | [packages/identity](packages/identity) |
| 5 | Sandboxing | [packages/sandbox](packages/sandbox) |
| 6 | Egress and secrets | [packages/egress](packages/egress) |
| 7 | Guardrails | [packages/guardrails](packages/guardrails) |
| 8 | Memory and data (sessions, long-term, ACL-aware RAG) | [packages/memory](packages/memory) |
| 9a | Observability | [packages/observability](packages/observability) |
| 9b | Evals | [packages/evals](packages/evals) |
| + | Shared contracts (added) | [packages/contracts](packages/contracts) |
| + | Audit log (added) | [packages/audit](packages/audit) |

## Layout

```
packages/     the nine topics plus contracts and audit
apps/         deployable entry points (api, approvals-ui, admin-console)
deploy/       local, kubernetes, terraform
docs/         architecture, adr, threat-model, runbooks
examples/     small end-to-end agents
tests/        cross-package: integration, e2e, security
scripts/      dev and CI helpers
```

## Request flow (target)

```
Client
  -> apps/api                      authenticate (SSO), mint run token
  -> runtime (core + adapter)      run loop
       -> guardrails: input
       -> model-gateway            route, fallback, budget  -> provider (via egress)
       -> guardrails: tool call
       -> tool-gateway             registry, risk tier, policy
            -> approvals           human approves write; bound to exact call; expires
            -> preflight           recheck approval, args, policy
            -> sandbox             ephemeral run
            -> egress              proxy adds secrets, allowlist, DLP
       -> guardrails: tool result
       -> memory                   session, long-term, ACL-aware RAG
       -> guardrails: output
  every step -> audit + observability
```

## Additions beyond the original list

- **contracts**: one place for shared schemas so packages stay decoupled.
- **audit**: separate append-only log. Guardrails, approvals, policy, and egress all write to it.
- **apps/approvals-ui**: reviewers need a surface that shows the exact call being approved.
- **tests/security**: prompt injection, sandbox escape, cross-tenant leak, approval replay and drift.
- **docs/threat-model** and **docs/adr**: write decisions down before code.

## Suggested build order

1. `contracts` and `docs/adr` (pick languages, schema tool, policy engine).
2. `runtime/core` with one adapter and the `conformance` suite.
3. `identity` run tokens and `tenancy`.
4. `model-gateway` basics.
5. `tool-gateway` with `approvals` and `preflight`.
6. `sandbox` and `egress` (these two ship together).
7. `guardrails` and `audit`.
8. `memory`.
9. `observability` and `evals` (start the eval harness early, not last).
