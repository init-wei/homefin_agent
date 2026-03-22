# HomeFin Agent

面向个人与家庭的财务数据中台 + 智能分析 Agent。

本项目采用 **自建账本核心** 的方式实现家庭财务管理与智能分析，同时设计为 **兼容外部账本映射**，可在未来与 Firefly III、GnuCash、Beancount、Actual Budget 等系统进行导入导出或数据互操作。

项目目标不是做一个单纯的记账 App，也不是直接提供买卖建议的投顾系统，而是构建一个可扩展的家庭财务基础设施，支持：

- 多来源账单导入与统一标准化
- 家庭成员、账户、预算、资产负债统一建模
- 自动分类、去重、转账识别、共享支出处理
- 报表分析、预算执行、财务洞察
- 自然语言问答与 Agent 工具调用
- 与外部账本系统兼容映射

---

# 1. 产品定位

## 1.1 核心定位

HomeFin Agent 是一个：

- **家庭财务数据中台**：归集微信、支付宝、银行卡、信用卡、手工账等多来源数据
- **账务分析系统**：提供月度收支、预算执行、成员支出、资产负债与净值分析
- **智能财务 Agent**：支持自然语言提问、报表解释、预算偏差说明、基础财务建议

## 1.2 非目标

当前阶段不做：

- 自动证券下单
- 高频投资决策
- 完整持牌投顾能力
- 复杂税务规划引擎
- 全自动实时银行 API 聚合平台

---

# 2. 设计原则

## 2.1 自建账本核心

项目采用 **自建统一账本核心模型**，而不是直接绑定现有账本系统作为底座。

原因：

- 需要适配中国本地账单生态（微信、支付宝、银行 PDF/XLS/EML）
- 需要支持家庭成员维度和共享支出语义
- 需要围绕 Agent 工具调用设计可解释的数据接口
- 需要后续兼容多种外部账本映射，而不是受制于其内部模型

## 2.2 兼容外部账本映射

项目提供映射层，对接：

- Firefly III
- GnuCash
- Beancount
- Actual Budget

策略是：

- 核心模型由本项目定义
- 外部账本通过 mapper 进行导入导出
- 不依赖外部账本决定本项目的数据结构

## 2.3 模块化单体优先

第一阶段采用 **模块化单体架构**：

- 便于快速开发和调试
- 降低分布式复杂度
- 未来可以平滑拆分为服务

## 2.4 Agent 只调工具，不直接碰底层数据库

Agent 层只通过明确的工具服务访问数据，例如：

- `query_monthly_summary`
- `query_category_breakdown`
- `query_member_spending`
- `query_budget_status`
- `search_transactions`
- `add_manual_transaction`

这样可以保证：

- 行为可控
- 输出可解释
- 风险边界明确
- 方便测试和审计

---

# 3. 技术栈

## 3.1 后端

推荐技术栈：

- Python 3.12+
- FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- Alembic
- PostgreSQL
- Redis
- Celery 或 Dramatiq
- httpx
- pandas
- openpyxl
- python-magic
- pypdf
- pdfplumber
- mail-parser 或 Python `email` 标准库
- tenacity
- orjson

## 3.2 前端

- Next.js
- TypeScript
- Tailwind CSS
- TanStack Query
- ECharts / Recharts

## 3.3 可选组件

- pgvector：RAG 能力
- rapidfuzz：模糊匹配与去重增强
- pendulum：时间处理
- polars：高性能数据处理
- duckdb：本地分析型查询

---

# 4. 总体架构

项目采用如下分层：

1. **领域核心层**：定义账本世界的核心实体和业务规则
2. **应用服务层**：组织业务用例与流程
3. **基础设施层**：数据库、对象存储、缓存、队列、安全等
4. **接口层**：REST API、CLI、Worker、Agent 对话入口
5. **适配器层**：账单导入器、外部账本映射器、LLM、存储、通知等

数据流核心路径：

`原始账单文件 -> Importer 解析 -> 标准化交易 -> 去重/分类/转账识别 -> 入库 -> 分析服务 -> API/Agent 输出`

---

# 5. 顶层目录结构

```text
homefin_agent/
├─ README.md
├─ pyproject.toml
├─ .env.example
├─ alembic.ini
├─ docker-compose.yml
├─ Makefile
├─ apps/
│  ├─ api/
│  │  ├─ main.py
│  │  ├─ lifespan.py
│  │  ├─ dependencies.py
│  │  ├─ exception_handlers.py
│  │  └─ routers/
│  │     ├─ auth.py
│  │     ├─ households.py
│  │     ├─ members.py
│  │     ├─ accounts.py
│  │     ├─ imports.py
│  │     ├─ transactions.py
│  │     ├─ categories.py
│  │     ├─ budgets.py
│  │     ├─ analytics.py
│  │     ├─ insights.py
│  │     ├─ assets.py
│  │     ├─ chat.py
│  │     └─ health.py
│  ├─ worker/
│  │  ├─ worker.py
│  │  ├─ celery_app.py
│  │  └─ tasks/
│  │     ├─ import_tasks.py
│  │     ├─ analytics_tasks.py
│  │     ├─ insight_tasks.py
│  │     └─ maintenance_tasks.py
│  └─ cli/
│     ├─ main.py
│     ├─ commands/
│     │  ├─ reparse_import.py
│     │  ├─ rebuild_reports.py
│     │  ├─ seed_categories.py
│     │  └─ create_admin.py
│
├─ domain/
│  ├─ enums/
│  │  ├─ account.py
│  │  ├─ transaction.py
│  │  ├─ import_job.py
│  │  ├─ budget.py
│  │  └─ insight.py
│  ├─ entities/
│  │  ├─ user.py
│  │  ├─ household.py
│  │  ├─ member.py
│  │  ├─ institution.py
│  │  ├─ account.py
│  │  ├─ import_job.py
│  │  ├─ raw_statement_record.py
│  │  ├─ transaction.py
│  │  ├─ transaction_split.py
│  │  ├─ category.py
│  │  ├─ rule.py
│  │  ├─ budget.py
│  │  ├─ budget_item.py
│  │  ├─ asset_snapshot.py
│  │  ├─ liability_snapshot.py
│  │  ├─ financial_goal.py
│  │  ├─ insight.py
│  │  ├─ chat_session.py
│  │  └─ chat_message.py
│  ├─ value_objects/
│  │  ├─ money.py
│  │  ├─ date_range.py
│  │  ├─ dedupe_key.py
│  │  ├─ merchant_match.py
│  │  └─ normalized_transaction.py
│  ├─ services/
│  │  ├─ transfer_matcher.py
│  │  ├─ dedupe_service.py
│  │  ├─ recurring_detector.py
│  │  ├─ shared_expense_service.py
│  │  ├─ category_assignment_service.py
│  │  ├─ household_summary_service.py
│  │  ├─ budget_evaluation_service.py
│  │  ├─ net_worth_service.py
│  │  └─ insight_generation_service.py
│  ├─ repositories/
│  │  ├─ user_repository.py
│  │  ├─ household_repository.py
│  │  ├─ member_repository.py
│  │  ├─ account_repository.py
│  │  ├─ import_job_repository.py
│  │  ├─ raw_record_repository.py
│  │  ├─ transaction_repository.py
│  │  ├─ category_repository.py
│  │  ├─ rule_repository.py
│  │  ├─ budget_repository.py
│  │  ├─ asset_repository.py
│  │  ├─ liability_repository.py
│  │  ├─ insight_repository.py
│  │  └─ chat_repository.py
│
├─ application/
│  ├─ dto/
│  │  ├─ auth.py
│  │  ├─ household.py
│  │  ├─ account.py
│  │  ├─ import_job.py
│  │  ├─ transaction.py
│  │  ├─ category.py
│  │  ├─ budget.py
│  │  ├─ analytics.py
│  │  ├─ insight.py
│  │  ├─ asset.py
│  │  └─ chat.py
│  ├─ commands/
│  │  ├─ create_household.py
│  │  ├─ add_member.py
│  │  ├─ create_account.py
│  │  ├─ upload_statement.py
│  │  ├─ import_statement.py
│  │  ├─ create_budget.py
│  │  ├─ add_manual_transaction.py
│  │  ├─ update_transaction.py
│  │  └─ mark_shared_expense.py
│  ├─ queries/
│  │  ├─ get_household_dashboard.py
│  │  ├─ get_monthly_summary.py
│  │  ├─ get_category_breakdown.py
│  │  ├─ get_member_spending.py
│  │  ├─ get_budget_status.py
│  │  ├─ get_transaction_list.py
│  │  ├─ get_net_worth_summary.py
│  │  └─ search_transactions.py
│  ├─ services/
│  │  ├─ household_app_service.py
│  │  ├─ account_app_service.py
│  │  ├─ import_app_service.py
│  │  ├─ transaction_app_service.py
│  │  ├─ category_app_service.py
│  │  ├─ budget_app_service.py
│  │  ├─ analytics_app_service.py
│  │  ├─ insight_app_service.py
│  │  ├─ asset_app_service.py
│  │  └─ chat_app_service.py
│
├─ adapters/
│  ├─ importers/
│  │  ├─ base.py
│  │  ├─ registry.py
│  │  ├─ sniffers.py
│  │  ├─ wechat_csv.py
│  │  ├─ alipay_mobile_csv.py
│  │  ├─ alipay_web_txt.py
│  │  ├─ boc_debit_pdf.py
│  │  ├─ boc_credit_eml.py
│  │  ├─ ccb_xls.py
│  │  ├─ cmb_pdf.py
│  │  ├─ cmbc_pdf.py
│  │  └─ manual_csv_template.py
│  ├─ external_ledgers/
│  │  ├─ base.py
│  │  ├─ firefly_mapper.py
│  │  ├─ gnucash_mapper.py
│  │  ├─ beancount_mapper.py
│  │  └─ actual_budget_mapper.py
│  ├─ llm/
│  │  ├─ base.py
│  │  ├─ openai_provider.py
│  │  ├─ ollama_provider.py
│  │  ├─ gateway.py
│  │  └─ prompts/
│  │     ├─ classify_transaction.md
│  │     ├─ summarize_monthly_report.md
│  │     ├─ explain_budget_overrun.md
│  │     └─ chat_system.md
│  ├─ storage/
│  │  ├─ base.py
│  │  ├─ local_storage.py
│  │  └─ s3_storage.py
│  ├─ cache/
│  │  ├─ base.py
│  │  └─ redis_cache.py
│  └─ notifications/
│     ├─ base.py
│     ├─ email_notifier.py
│     └─ webhook_notifier.py
│
├─ infra/
│  ├─ config/
│  │  ├─ settings.py
│  │  └─ logging.py
│  ├─ db/
│  │  ├─ base.py
│  │  ├─ session.py
│  │  ├─ models/
│  │  │  ├─ user.py
│  │  │  ├─ household.py
│  │  │  ├─ member.py
│  │  │  ├─ institution.py
│  │  │  ├─ account.py
│  │  │  ├─ import_job.py
│  │  │  ├─ raw_statement_record.py
│  │  │  ├─ transaction.py
│  │  │  ├─ transaction_split.py
│  │  │  ├─ category.py
│  │  │  ├─ rule.py
│  │  │  ├─ budget.py
│  │  │  ├─ budget_item.py
│  │  │  ├─ asset_snapshot.py
│  │  │  ├─ liability_snapshot.py
│  │  │  ├─ financial_goal.py
│  │  │  ├─ insight.py
│  │  │  ├─ chat_session.py
│  │  │  └─ chat_message.py
│  │  ├─ repositories/
│  │  │  ├─ sql_user_repository.py
│  │  │  ├─ sql_household_repository.py
│  │  │  ├─ sql_member_repository.py
│  │  │  ├─ sql_account_repository.py
│  │  │  ├─ sql_import_job_repository.py
│  │  │  ├─ sql_raw_record_repository.py
│  │  │  ├─ sql_transaction_repository.py
│  │  │  ├─ sql_category_repository.py
│  │  │  ├─ sql_rule_repository.py
│  │  │  ├─ sql_budget_repository.py
│  │  │  ├─ sql_asset_repository.py
│  │  │  ├─ sql_liability_repository.py
│  │  │  ├─ sql_insight_repository.py
│  │  │  └─ sql_chat_repository.py
│  │  └─ queries/
│  │     ├─ dashboard_queries.py
│  │     ├─ transaction_queries.py
│  │     ├─ analytics_queries.py
│  │     ├─ budget_queries.py
│  │     └─ net_worth_queries.py
│  ├─ queue/
│  │  └─ task_dispatcher.py
│  └─ security/
│     ├─ password.py
│     ├─ jwt.py
│     └─ permissions.py
│
├─ migrations/
│  └─ versions/
│
├─ tests/
│  ├─ unit/
│  │  ├─ domain/
│  │  ├─ application/
│  │  ├─ importers/
│  │  └─ adapters/
│  ├─ integration/
│  │  ├─ api/
│  │  ├─ db/
│  │  └─ worker/
│  └─ fixtures/
│     ├─ statements/
│     │  ├─ wechat/
│     │  ├─ alipay/
│     │  ├─ boc/
│     │  ├─ ccb/
│     │  └─ cmb/
│     └─ seeds/
│
└─ docs/
   ├─ architecture.md
   ├─ data_model.md
   ├─ import_pipeline.md
   ├─ agent_tools.md
   ├─ external_ledger_mapping.md
   └─ api_contracts.md
```

---

# 6. 目录与文件功能说明

## 6.1 根目录

### `README.md`
项目总说明，供开发者与 Codex 快速了解系统目标、结构与开发顺序。

### `pyproject.toml`
管理依赖、格式化、静态检查、测试配置。

### `.env.example`
环境变量模板，例如数据库、缓存、存储、模型网关配置。

### `docker-compose.yml`
本地开发依赖编排：PostgreSQL、Redis、MinIO、API、Worker。

### `Makefile`
常用命令封装：启动、迁移、测试、Lint、格式化。

---

## 6.2 `apps/api/`

HTTP API 层，负责对前端和外部客户端暴露服务。

### `main.py`
FastAPI 应用入口，负责创建 app、挂载路由和中间件。

### `lifespan.py`
应用启动与关闭生命周期管理，初始化数据库、缓存、存储和 LLM 网关。

### `dependencies.py`
依赖注入，统一获取 DB Session、当前用户、当前家庭和应用服务实例。

### `exception_handlers.py`
统一异常转 HTTP 响应。

### `routers/`
资源域路由：

- `auth.py`：登录、注册、用户信息
- `households.py`：家庭创建、更新、家庭概览
- `members.py`：家庭成员管理
- `accounts.py`：账户管理
- `imports.py`：账单上传、导入任务查询、重试解析
- `transactions.py`：交易列表、编辑、拆分、共享支出标记、手工录入
- `categories.py`：分类树与分类管理
- `budgets.py`：预算创建、预算执行情况
- `analytics.py`：月度报表、分类分析、成员支出、现金流趋势
- `insights.py`：财务提醒和洞察
- `assets.py`：资产、负债、净值摘要
- `chat.py`：聊天入口与 Agent 对话
- `health.py`：服务健康检查

---

## 6.3 `apps/worker/`

异步任务处理层。

### `worker.py`
Worker 启动入口。

### `celery_app.py`
Celery 实例配置。

### `tasks/`

- `import_tasks.py`：文件解析、标准化、去重、分类、入库
- `analytics_tasks.py`：报表缓存、重建聚合结果
- `insight_tasks.py`：生成预算提醒、异常消费提醒、还款提醒
- `maintenance_tasks.py`：清理缓存、清理临时文件、维护类任务

---

## 6.4 `apps/cli/`

命令行工具，便于运维与数据修复。

- `reparse_import.py`：重新解析某个导入任务
- `rebuild_reports.py`：重建统计和缓存
- `seed_categories.py`：初始化默认分类
- `create_admin.py`：创建管理员或测试账户

---

## 6.5 `domain/`

领域层是系统核心，不依赖具体数据库与 Web 框架。

### `enums/`
定义各类枚举：账户类型、交易方向、导入任务状态、预算周期、洞察类型等。

### `entities/`
定义领域实体：

- `User`
- `Household`
- `Member`
- `Institution`
- `Account`
- `ImportJob`
- `RawStatementRecord`
- `Transaction`
- `TransactionSplit`
- `Category`
- `Rule`
- `Budget`
- `BudgetItem`
- `AssetSnapshot`
- `LiabilitySnapshot`
- `FinancialGoal`
- `Insight`
- `ChatSession`
- `ChatMessage`

### `value_objects/`
值对象定义：

- `money.py`：金额与币种封装
- `date_range.py`：时间区间
- `dedupe_key.py`：去重键
- `merchant_match.py`：商户匹配结果
- `normalized_transaction.py`：标准化交易中间对象

### `services/`
核心业务规则：

- `transfer_matcher.py`：转账识别
- `dedupe_service.py`：去重逻辑
- `recurring_detector.py`：周期性支出识别
- `shared_expense_service.py`：共享支出与分摊
- `category_assignment_service.py`：分类分配
- `household_summary_service.py`：家庭汇总计算
- `budget_evaluation_service.py`：预算执行判断
- `net_worth_service.py`：净值汇总
- `insight_generation_service.py`：洞察生成

### `repositories/`
仓储抽象接口，定义数据访问契约，不绑定 SQLAlchemy。

---

## 6.6 `application/`

应用层负责组织用例流程。

### `dto/`
各类数据传输对象，作为 API 与服务之间的边界格式。

### `commands/`
写操作命令对象，例如：

- 创建家庭
- 添加成员
- 创建账户
- 上传账单
- 导入账单
- 手工新增交易
- 更新交易
- 标记共享支出

### `queries/`
读操作查询对象，例如：

- 家庭首页概览
- 月度收支
- 分类分布
- 成员支出
- 预算状态
- 交易搜索
- 净值摘要

### `services/`
应用服务，编排多个仓储、领域服务和适配器完成完整用例。

---

## 6.7 `adapters/`

外部世界接入层。

### `importers/`
账单导入器插件体系。

- `base.py`：导入器接口定义
- `registry.py`：导入器注册中心
- `sniffers.py`：来源识别
- `wechat_csv.py`：微信 CSV
- `alipay_mobile_csv.py`：支付宝手机端 CSV
- `alipay_web_txt.py`：支付宝网页 TXT
- `boc_debit_pdf.py`：中国银行借记卡 PDF
- `boc_credit_eml.py`：中国银行信用卡邮件账单
- `ccb_xls.py`：建设银行 XLS/XLSX
- `cmb_pdf.py`：招商银行 PDF
- `cmbc_pdf.py`：民生银行 PDF
- `manual_csv_template.py`：手工模板导入

### `external_ledgers/`
外部账本兼容映射层。

- `base.py`：统一映射接口
- `firefly_mapper.py`：Firefly III 映射
- `gnucash_mapper.py`：GnuCash 映射
- `beancount_mapper.py`：Beancount 映射
- `actual_budget_mapper.py`：Actual Budget 映射

### `llm/`
模型调用层。

- `base.py`：Provider 抽象
- `openai_provider.py`：OpenAI 兼容接口
- `ollama_provider.py`：本地模型接口
- `gateway.py`：统一网关
- `prompts/`：Prompt 模板文件

### `storage/`
对象存储抽象与实现。

### `cache/`
缓存抽象与 Redis 实现。

### `notifications/`
通知抽象与实现，如邮件和 Webhook。

---

## 6.8 `infra/`

基础设施实现层。

### `config/`
- `settings.py`：配置读取
- `logging.py`：日志配置

### `db/`
数据库实现。

- `base.py`：ORM Base
- `session.py`：数据库会话
- `models/`：SQLAlchemy ORM 模型
- `repositories/`：仓储 SQL 实现
- `queries/`：复杂 SQL 与报表查询

### `queue/`
任务分发器，封装 Celery 或其他队列实现。

### `security/`
- 密码哈希
- JWT
- 权限判断

---

## 6.9 `tests/`

测试目录。

- `unit/domain/`：领域规则测试
- `unit/application/`：应用服务测试
- `unit/importers/`：导入器测试
- `unit/adapters/`：适配器测试
- `integration/api/`：接口集成测试
- `integration/db/`：数据库集成测试
- `integration/worker/`：异步任务集成测试
- `fixtures/statements/`：脱敏后的账单样本

---

## 6.10 `docs/`

架构与接口文档：

- `architecture.md`
- `data_model.md`
- `import_pipeline.md`
- `agent_tools.md`
- `external_ledger_mapping.md`
- `api_contracts.md`

---

# 7. 核心数据流设计

## 7.1 导入流程

1. 用户上传账单文件
2. 创建 `ImportJob`
3. 文件保存到对象存储
4. Worker 选择合适的 importer
5. `parse()` 提取原始记录
6. `normalize()` 转为 `NormalizedTransaction`
7. 生成去重键
8. 执行去重、转账识别、分类
9. 写入 `Transaction`
10. 刷新统计与洞察

## 7.2 查询流程

1. 前端或 Agent 发起查询
2. API 进入 application query service
3. 调用 repository / analytics query
4. 返回结构化数据
5. 若为 Agent，对结果进行解释性生成

## 7.3 Agent 流程

1. 用户提出问题
2. Agent 判断意图
3. 调用 tool service
4. 获取结构化结果
5. 由 LLM 做解释、总结或自然语言输出

---

# 8. 核心接口设计

## 8.1 Importer 接口

```python
class StatementImporter(Protocol):
    source_type: str

    def can_handle(self, filename: str, mime_type: str, sample: bytes) -> bool:
        ...

    def parse(self, file_bytes: bytes) -> list[dict]:
        ...

    def normalize(self, raw_record: dict) -> "NormalizedTransaction":
        ...
```

## 8.2 外部账本映射接口

```python
class ExternalLedgerMapper(Protocol):
    ledger_name: str

    def export_accounts(self, accounts: list[Account]) -> object:
        ...

    def export_transactions(self, transactions: list[Transaction]) -> object:
        ...

    def import_accounts(self, payload: object) -> list[Account]:
        ...

    def import_transactions(self, payload: object) -> list[NormalizedTransaction]:
        ...
```

## 8.3 LLM Gateway 接口

```python
class LLMGateway(Protocol):
    async def classify_transaction(self, text: str, context: dict) -> dict:
        ...

    async def summarize_monthly_report(self, report_data: dict) -> str:
        ...

    async def explain_budget_overrun(self, payload: dict) -> str:
        ...

    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        ...
```

## 8.4 Agent Tool 接口

```python
class AgentToolService:
    async def query_monthly_summary(self, household_id: str, month: str) -> dict: ...
    async def query_category_breakdown(self, household_id: str, month: str) -> dict: ...
    async def query_member_spending(self, household_id: str, month: str) -> dict: ...
    async def query_budget_status(self, household_id: str, month: str) -> dict: ...
    async def add_manual_transaction(self, household_id: str, payload: dict) -> dict: ...
    async def search_transactions(self, household_id: str, filters: dict) -> dict: ...
```

---

# 9. 关键实现机制

## 9.1 标准化交易中间对象

所有导入器最终都输出统一结构：

```python
@dataclass
class NormalizedTransaction:
    source_type: str
    source_txn_id: str | None
    account_hint: str | None
    txn_time: datetime
    amount: Decimal
    currency: str
    direction: str
    counterparty: str | None
    description: str | None
    merchant_name: str | None
    raw_payload: dict
```

这是导入器与账本核心的桥梁。

## 9.2 去重机制

建议基于以下字段组合生成 `dedupe_key`：

- household_id
- account_id
- txn_time
- amount
- normalized_counterparty
- normalized_description
- source_txn_id

## 9.3 转账识别

转账识别逻辑应独立于分类逻辑，匹配条件可以包括：

- 同家庭内两个账户
- 金额绝对值相等
- 时间接近
- 一进一出
- 描述包含“转账”“充值”“提现”“还款”等关键词

## 9.4 分类分配优先级

1. 强规则
2. 用户自定义规则
3. 账户默认规则
4. 商户关键词规则
5. LLM 补充建议
6. 待人工确认

## 9.5 外部账本兼容策略

前期只做：

- 导入适配
- 导出适配

不做实时双向同步。

---

# 10. 开发顺序建议

## 阶段 1：账本底座

实现：

- 用户、家庭、成员、账户
- 分类
- 交易
- 导入任务
- 基础数据库与迁移

## 阶段 2：导入系统

实现：

- Importer 抽象
- Importer Registry
- 微信 CSV
- 支付宝手机端 CSV
- 至少一个银行导入器
- 上传与解析任务

## 阶段 3：查询与报表

实现：

- 交易列表
- 分类分析
- 月度收支
- 成员支出
- 家庭汇总

## 阶段 4：规则与预算

实现：

- 规则表
- 自动分类规则
- 预算
- 洞察与提醒

## 阶段 5：Agent 能力

实现：

- Agent Tool Service
- Chat Session / Message
- LLM Gateway
- 基础财务问答

## 阶段 6：外部账本兼容

实现：

- Beancount Mapper
- Firefly III Mapper
- GnuCash Mapper

---

# 11. MVP 验收标准

## 数据导入

- 支持微信、支付宝、至少 1 家银行导入
- 支持去重
- 支持解析失败记录追踪

## 核心账务

- 支持统一交易查询
- 支持分类修改
- 支持成员归属调整
- 支持共享支出标记

## 报表分析

- 支持月度收支摘要
- 支持分类支出分布
- 支持成员支出分布
- 支持预算执行状态

## Agent

- 支持至少 10 类常见问题查询
- 结果基于真实结构化数据
- 不允许凭空编造财务结果

---

# 12. Codex 工作建议

Codex 在读取本 README 后，建议按如下方式展开：

1. 先生成 `domain/`、`application/`、`infra/db/models/` 基础骨架
2. 建立 Alembic 迁移
3. 实现 `ImportJob`、`Transaction`、`Category`、`Account` 全链路
4. 实现第一个 importer：`wechat_csv.py`
5. 实现上传导入与异步任务
6. 实现月度收支查询与交易列表 API
7. 补充测试夹具与单元测试

Codex 不应：

- 在第一阶段直接实现复杂微服务拆分
- 直接让 Agent 绕过应用服务查询数据库
- 将外部账本模型直接作为内部核心模型
- 把分类、去重、转账识别全部混在 importer 中

---

# 13. 后续扩展方向

- 邮箱附件自动拉取
- OCR/PDF 表格抽取增强
- 资产持仓与收益分析
- 家庭净值趋势
- 财务健康评分
- 定期报告自动生成
- 更多银行适配器
- 本地私有化部署增强
- RAG 财务知识库

---

# 14. 结论

HomeFin Agent 的核心价值在于：

- **掌控统一账本核心模型**
- **通过插件式 importer 吸收碎片化账单数据**
- **通过 mapper 兼容外部账本**
- **通过清晰的 tool interface 支撑智能 Agent**

这是一个以账本为底座、以分析为中台、以 Agent 为交互入口的长期可扩展财务系统。
