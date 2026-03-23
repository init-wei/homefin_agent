# HomeFin Agent Guide

面向后续 Codex / agent 执行的项目说明。此文件描述当前仓库的真实实现状态、关键约束和下一步扩展方式；开发者入门说明放在新的 `README.md`。

## 1. 当前状态

仓库已经从纯设计稿推进到可运行后端骨架，当前实现包含：

- FastAPI API
- 基于 Bearer token 的认证与当前用户注入
- SQLAlchemy 2.x + SQLite/PostgreSQL 兼容模型
- Alembic 初始迁移脚手架
- 账务核心实体：`User`、`Household`、`Member`、`Account`、`Category`、`Transaction`、`Budget`、`ImportJob`
- OpenClaw 身份绑定：`ExternalIdentityBinding`
- Agent 审计：`AgentAuditLog`
- `AgentToolService` 作为唯一工具编排入口
- Python stdio MCP server
- OpenClaw bundle 基础目录、skill、MCP 配置
- 微信 CSV 与一个简化银行 CSV importer
- DB-backed 异步导入队列与 `apps/worker/worker.py`
- 单元测试 + 集成测试

当前还没有实现：

- 规则引擎、自动分类、转账识别
- 外部账本 mapper
- 真正的 OpenClaw hooks / commands 自动化配置
- 成员邀请 / 独立成员管理 API

## 2. 当前目录现实

当前仓库的重要目录与职责：

- `apps/api/`: FastAPI 入口、依赖注入、资源路由
- `apps/mcp/`: Python MCP stdio server
- `apps/worker/`: import job 处理循环与 OpenClaw 事件桥接
- `application/services/`: 用例编排层，后续改动优先放这里
- `adapters/importers/`: 账单导入器
- `adapters/openclaw/`: OpenClaw CLI bridge
- `infra/db/`: ORM 模型、仓储、session
- `migrations/`: Alembic 迁移
- `integrations/openclaw/`: OpenClaw bundle 元数据与 skill
- `tests/`: 当前可运行测试

不要再按旧设计稿假设存在 `apps/cli/`、`docs/`、`adapters/llm/`、`external_ledgers/` 等目录，除非你正在实现它们。

## 3. 核心实现约束

### 3.1 Agent 访问边界

`AgentToolService` 是 HomeFin 暴露给 Agent / MCP / OpenClaw 的唯一工具边界。

- API chat 转 OpenClaw 时，不应绕开它
- MCP tools 必须复用它
- 后续 cron / worker / event-driven agent 调用也应复用它
- 不要让 agent 直接操作 repository 或 ORM model

### 3.2 资源归属必须校验

当前仓库已经开始收紧跨资源写入：

- `Account` 必须属于对应 `Household`
- `Category` 必须属于对应 `Household`
- `Member` 必须属于对应 `Household`
- `Transaction` 修改分类时，`Category` 必须和交易在同一 `Household`
- 绑定 owner 时，`user_id` 必须是 household owner

后续新增写操作时必须延续这个原则，不允许只靠外层 API 参数假定资源同属一个 household。

### 3.3 数据库约束已开始成为真约束

当前 ORM 与 Alembic 已定义这些基础约束：

- `users.email` 唯一
- `transactions.dedupe_key` 唯一
- `external_identity_bindings(provider, external_actor_id, household_id)` 唯一
- `budgets(household_id, month, category_id, member_id)` 唯一
- 多个查询热点索引

后续修改 schema 时：

1. 先改 `infra/db/models.py`
2. 再补 Alembic 迁移
3. 再补测试

不要只改 `create_all()` 路径，不改迁移。

### 3.4 OpenClaw 是可选集成，不是启动前置

当前机器未安装 OpenClaw 也可以开发大部分功能。

- API、DB、import、analytics、AgentToolService、MCP tool 逻辑都能单独开发
- 真正依赖 OpenClaw CLI 的路径只有 chat 转发和 worker 事件发布
- `OpenClawGatewayClient` 现在会把 CLI 缺失封装成结构化 `IntegrationError`

不要把“安装 OpenClaw”当成后端迭代前置步骤，除非当前任务明确是做联调。

## 4. 运行与验证

推荐命令：

```bash
python -m venv .venv
.venv\\Scripts\\python -m pip install -e ".[dev]"
.venv\\Scripts\\python -m pytest
```

常用入口：

```bash
uvicorn apps.api.main:app --reload
python -m apps.mcp.server
python -m apps.worker.worker --once
alembic upgrade head
```

## 5. 当前已实现 API / Tool 范围

REST API 已有：

- `/auth/register`
- `/auth/login`
- `/auth/me`
- `/households/bootstrap`
- `/accounts`
- `/categories`
- `/budgets`
- `/transactions`
- `/imports/statements`
- `/imports/jobs/{job_id}?household_id=...`
- `/analytics/*`
- `/chat/bindings`
- `/chat/messages`
- `/chat/audits`

Agent / MCP 已有工具：

- `query_monthly_summary`
- `query_category_breakdown`
- `query_member_spending`
- `query_budget_status`
- `search_transactions`
- `query_net_worth_summary`
- `add_manual_transaction`
- `update_transaction_category`
- `mark_shared_expense`

权限边界：

- owner: household 级查询 + 有限写入
- member: 仅自己的 member scope 查询，不允许 owner-only 工具

## 6. 后续优先级

如果后续继续扩展，推荐按这个顺序：

1. 导入失败重试 / reprocess
2. 成员邀请 / 身份绑定自助流程
3. 转账识别与自动分类
4. PostgreSQL 本地联调与迁移验证
5. OpenClaw 真联调
6. 更多 importer / 外部账本 mapper

## 7. Codex 工作规则

后续 Codex 任务应遵守：

- 优先沿现有 `application/services` 扩展，不要新长一套平行 service
- 新增数据库字段时同步修改 Alembic
- 新增写操作必须考虑 household / member ownership
- 新增 Agent 工具必须落审计
- 没有 OpenClaw CLI 时，不要把后端任务卡在 OpenClaw 联调上
- 优先补测试，再扩新功能

## 8. 当前测试基线

当前测试覆盖：

- auth register/login/me
- AccessService owner/member scope
- importer 标准化与 dedupe
- AgentToolService 权限与幂等
- 绑定校验
- API 主流程
- 异步导入成功 / 失败
- OpenClaw CLI 缺失时的 API 响应
- worker 事件命令拼装与缺失 CLI 降级
- MCP tool 调用

变更后保持 `15 passed` 或更高，不要降低测试覆盖的核心路径。
