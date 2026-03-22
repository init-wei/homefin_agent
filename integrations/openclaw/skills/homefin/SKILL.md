# HomeFin Finance Skill

Use this skill whenever the conversation is about household finance data managed by HomeFin Agent.

## Rules

- Always use HomeFin MCP tools before answering factual finance questions.
- Never invent balances, budgets, transactions, or trends that were not returned by a tool.
- If a tool returns `ok=false`, explain the error and ask the user to fix bindings or permissions instead of guessing.
- For write actions, require an explicit user instruction and pass an `idempotency_key`.
- Treat `member` bindings as self-scope only. Never attempt cross-member comparison from a member-scoped session.

## Preferred Tool Order

1. `query_monthly_summary`
2. `query_category_breakdown`
3. `search_transactions`
4. `query_budget_status`
5. `query_net_worth_summary`
6. Write tools only after confirmation

## Session Context

- Session key format: `agent:homefin:<household_id>:<provider>:<external_actor_id>`
- Required binding inputs: `provider`, `external_actor_id`, `household_id`
- Optional routing inputs: `channel`, `route`

