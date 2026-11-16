# identity

Who is calling, on whose behalf, and what they may do.

## Owns

- SSO (OIDC/SAML) and SCIM provisioning
- Run-scoped short-lived tokens
- On-behalf-of delegation
- Policy engine integration (OPA or Cedar)
- Multi-tenant isolation rules

## Design notes and open decisions

- The agent never holds a user's long-lived credential.
- A run token carries tenant, user, run id, scopes, and expiry. It dies with the run.
- Decide: OPA (Rego) or Cedar. Keep policy behind one interface so you can swap.

## Layout

- `delegation/` On-behalf-of token exchange
- `policy/` Policy engine integration
- `run-tokens/` Mint, verify, and revoke run-scoped tokens
- `scim/` SCIM user and group provisioning and deprovisioning
- `sso/` OIDC and SAML login, session handling
- `tenancy/` Tenant model and isolation rules (data, compute, keys, quotas)

## Status

Scaffold only. No implementation yet.
