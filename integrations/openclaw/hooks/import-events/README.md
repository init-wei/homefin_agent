# Import Event Hook Pack

This directory is reserved for future OpenClaw hook pack definitions that react to:

- `import_completed`
- `import_failed`
- `budget_threshold_exceeded`
- `repayment_due_soon`

In v1, HomeFin emits these via the OpenClaw CLI bridge in `apps/worker/tasks/openclaw_events.py`.

