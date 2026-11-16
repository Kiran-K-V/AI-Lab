# egress

All outbound traffic and all secrets. No keys inside the agent or sandbox.

## Owns

- Forward proxy with allowlists
- Secret broker: injects credentials at the proxy, outside the agent
- Data loss checks on outbound payloads
- Full outbound audit

## Design notes and open decisions

- The agent asks for an action. The proxy adds the credential. The agent never sees it.
- Decide: secret store (Vault, cloud KMS/secret manager) and rotation policy.

## Layout

- `allowlists/` Per-tenant and per-tool destination allowlists
- `dlp/` Outbound data loss checks (PII, secrets, canary tokens)
- `proxy/` Forward proxy
- `secrets/` Secret broker and credential injection

## Status

Scaffold only. No implementation yet.
