#!/usr/bin/env python3
"""Quick integration check against the Neon PostgreSQL database.

This helper mirrors what the production server expects. It validates
connectivity, schema presence and minimal data seeding so we can confirm
that the hosted instance is ready before deploying the API.

Run with:

    python3 tools/neon_healthcheck.py

Set ``DATABASE_URL`` to override the default Neon connection string.
"""
from __future__ import annotations

import os
import sys
from typing import Any

try:
    import psycopg
    from psycopg.rows import dict_row
except ModuleNotFoundError as exc:  # pragma: no cover - surfaced to CLI
    sys.stderr.write(
        "[neon-healthcheck] Dependência psycopg não encontrada. "
        "Instale com 'python3 -m pip install psycopg[binary] psycopg-pool pillow'\n"
    )
    raise

DEFAULT_URL = (
    "postgresql://neondb_owner:npg_EunfT2mh0Sci@ep-calm-sky-aczofamt-pooler.sa-east-1.aws.neon.tech/Divino%20"
    "?sslmode=require&channel_binding=require"
)

EXPECTED_TABLES = {
    "events",
    "products",
    "orders",
    "newsletter_subscribers",
    "social_links",
    "setlist_tracks",
    "setlist_votes",
    "setlist_comments",
}


class HealthcheckFailure(RuntimeError):
    """Raised when any validation step fails."""


def assert_tables(cur: psycopg.Cursor[Any]) -> None:
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public';
        """
    )
    found = {row["table_name"] for row in cur.fetchall()}
    missing = sorted(EXPECTED_TABLES - found)
    if missing:
        raise HealthcheckFailure(
            "Tabelas ausentes no schema público: " + ", ".join(missing)
        )


def assert_seeded(cur: psycopg.Cursor[Any]) -> None:
    cur.execute("SELECT COUNT(*) AS total FROM events;")
    events = cur.fetchone()["total"]
    if not events:
        raise HealthcheckFailure("A tabela events está vazia — seed não foi executado.")

    cur.execute("SELECT COUNT(*) AS total FROM setlist_tracks;")
    tracks = cur.fetchone()["total"]
    if tracks < 53:
        raise HealthcheckFailure(
            "O catálogo de setlist não possui as 53 faixas esperadas (atual: %d)." % tracks
        )


def ping_database(url: str) -> None:
    print(f"[neon-healthcheck] Conectando em {url.split('@')[-1]}")
    with psycopg.connect(url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            assert_tables(cur)
            assert_seeded(cur)
            cur.execute(
                "SELECT title, date_iso, instagram_url FROM events ORDER BY date_iso LIMIT 3;"
            )
            sample = cur.fetchall()
    print("[neon-healthcheck] ✅ Conexão estável e dados iniciais detectados.")
    for event in sample:
        print(
            f"  - {event['date_iso']:%d/%m} · {event['title']} (Instagram: {event['instagram_url']})"
        )


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL", DEFAULT_URL)
    try:
        ping_database(db_url)
    except HealthcheckFailure as failure:
        sys.stderr.write(f"[neon-healthcheck] ❌ {failure}\n")
        sys.exit(1)
    except psycopg.Error as error:
        sys.stderr.write(f"[neon-healthcheck] ❌ Erro do PostgreSQL: {error}\n")
        sys.exit(2)
    except Exception as exc:  # pragma: no cover - queremos superfície para debug
        sys.stderr.write(f"[neon-healthcheck] ❌ Falha inesperada: {exc}\n")
        sys.exit(3)
