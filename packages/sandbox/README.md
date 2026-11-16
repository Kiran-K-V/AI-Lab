# sandbox

Ephemeral isolated environments for untrusted work.

## Owns

- Sandbox lifecycle: create, run, snapshot, destroy
- Profiles for code, shell, browser, untrusted MCP servers
- Default-deny network
- Resource and time limits

## Design notes and open decisions

- One sandbox per run (or per call). Destroy on finish. No reuse across tenants.
- Decide: Firecracker, gVisor, Kata, or a hosted sandbox provider.
- Files go in and out through a narrow, logged channel.

## Layout

- `images/` Base images and their build definitions
- `manager/` Create, track, and destroy sandboxes
- `network/` Default-deny network rules
- `profiles/` Per-use-case limits and permissions
- `providers/` Backends: Firecracker, gVisor, container, hosted provider

## Status

Scaffold only. No implementation yet.
