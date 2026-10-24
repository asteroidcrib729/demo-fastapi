"""Manually initialize the one production database with public sample records."""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


def main() -> None:
    load_dotenv(Path(__file__).with_name(".env.local"))
    direct_url = os.getenv("DIRECT_URL", "").strip()
    if not direct_url:
        raise SystemExit("Set DIRECT_URL to the production database's direct URL.")

    with psycopg.connect(direct_url, connect_timeout=10) as connection:
        connection.execute(Path(__file__).with_name("schema.sql").read_bytes())
    print("Production database initialized; existing records were preserved.")


if __name__ == "__main__":
    main()
