# memory

Sessions, long-term memory, and ACL-aware retrieval.

## Owns

- Session store (short-term context)
- Long-term memory (facts, preferences) with scope and expiry
- RAG: ingestion, ACL propagation, retrieval with filtering
- Retention and deletion

## Design notes and open decisions

- ACLs are enforced at retrieval time, using the caller's identity, not the agent's.
- Memory is scoped: user, team, tenant. Never cross tenants.
- Memory writes are untrusted-input risks (memory poisoning). Guard them.

## Layout

- `long-term/` Durable memory with scope, provenance, and expiry
- `rag/` Retrieval pipeline
- `retention/` TTL, right-to-delete, export
- `sessions/` Conversation and run session storage
- `stores/` Storage backends (relational, vector, cache)

## Status

Scaffold only. No implementation yet.
