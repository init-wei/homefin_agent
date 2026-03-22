from fastapi import FastAPI

from apps.api.exception_handlers import register_exception_handlers
from apps.api.lifespan import lifespan
from apps.api.routers import accounts, analytics, budgets, categories, chat, health, households, imports, transactions
from infra.config.settings import get_settings

app = FastAPI(title=get_settings().api_title, lifespan=lifespan)
register_exception_handlers(app)
app.include_router(health.router)
app.include_router(households.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(budgets.router)
app.include_router(transactions.router)
app.include_router(imports.router)
app.include_router(analytics.router)
app.include_router(chat.router)
