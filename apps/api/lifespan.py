from contextlib import asynccontextmanager

from fastapi import FastAPI

from infra.db.session import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield

