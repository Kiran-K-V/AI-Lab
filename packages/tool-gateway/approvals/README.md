# approvals

Human-in-the-loop approval flow for write actions.

## Layout

- `binding/` Binds an approval to exact call (args hash, run, tenant, principal)
- `expiry/` TTL rules, single-use enforcement, revocation
- `notifiers/` Delivery of approval requests (UI, Slack, email)
- `store/` Persistence for pending and decided approvals

## Status

Scaffold only. No implementation yet.
