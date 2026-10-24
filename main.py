import logging
import os
from typing import Annotated

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from psycopg.rows import dict_row
from pydantic import BaseModel

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    raise RuntimeError("Set DATABASE_URL to your Prisma Postgres connection string.")

logger = logging.getLogger(__name__)
app = FastAPI(title="Prisma Postgres Records API", version="1.0.0")


class Record(BaseModel):
    id: int
    name: str
    value: str
    status: str


@app.get("/health")
def health() -> dict[str, str]:
    """Check that the API process is running without querying the database."""
    return {"status": "ok"}


@app.get("/records", response_model=list[Record])
def get_records(
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Fetch a page of public demonstration records, ordered by ID."""
    try:
        with psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row,
            connect_timeout=5,
            prepare_threshold=None,
        ) as connection:
            connection.read_only = True
            connection.execute("SET LOCAL statement_timeout = '5s'")
            return connection.execute(
                "SELECT id, name, value, status FROM public.records "
                "ORDER BY id LIMIT %s OFFSET %s",
                (limit, offset),
            ).fetchall()
    except psycopg.Error as exc:
        logger.warning("Database request failed (%s).", type(exc).__name__)
        raise HTTPException(
            status_code=503, detail="Records are temporarily unavailable."
        ) from None
