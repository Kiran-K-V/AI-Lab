# model-gateway

Single door to all LLM providers. The agent never calls a provider directly.

## Owns

- Provider abstraction
- Routing by cost, latency, capability, residency, tenant pinning
- Fallbacks, retries, circuit breakers
- Per-tenant budgets and rate limits
- Optional response cache

## Design notes and open decisions

- Provider keys live here or in egress/secrets, never in the runtime.
- Decide: build on LiteLLM/Portkey-style proxy or write own thin router.
- Every call emits a usage record (tokens, cost, latency, route taken).

## Layout

- `budgets/` Token and cost budgets, quotas, rate limits per tenant, user, and run
- `cache/` Optional prompt and response cache
- `fallbacks/` Retry, fallback chains, circuit breakers, timeouts
- `providers/` One driver per provider (OpenAI, Anthropic, Bedrock, Vertex, local)
- `routing/` Routing policies and model capability catalog

## Status

Scaffold only. No implementation yet.
