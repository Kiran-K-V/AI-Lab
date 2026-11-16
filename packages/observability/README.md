# observability

Traces, metrics, and logs for every run.

## Owns

- Distributed tracing (OpenTelemetry GenAI conventions)
- Metrics: cost, latency, error, approval rate
- Structured logs with redaction
- Dashboards and alerts

## Design notes and open decisions

- Redact secrets and PII before export.
- Trace id flows from API to model, tool, sandbox, and egress.

## Layout

- `dashboards/` Dashboards and alert rules as code
- `logging/` Structured logging and redaction
- `metrics/` Metric definitions and exporters
- `tracing/` Span conventions and exporters

## Status

Scaffold only. No implementation yet.
