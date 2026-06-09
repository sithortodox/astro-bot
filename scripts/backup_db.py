#!/usr/bin/env python3
"""Backup PostgreSQL database."""

import subprocess
import os
from datetime import datetime
from pathlib import Path

BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"
DB_NAME = os.getenv("POSTGRES_DB", "astro_bot")
DB_USER = os.getenv("POSTGRES_USER", "astro")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")


def create_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"astro_bot_{timestamp}.sql"

    cmd = [
        "pg_dump",
        f"--host={DB_HOST}",
        f"--port={DB_PORT}",
        f"--username={DB_USER}",
        f"--dbname={DB_NAME}",
        f"--file={backup_file}",
        "--verbose",
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = os.getenv("POSTGRES_PASSWORD")

    try:
        subprocess.run(cmd, env=env, check=True, capture_output=True)
        print(f"Backup created: {backup_file}")

        # Remove old backups (keep last 7)
        backups = sorted(BACKUP_DIR.glob("astro_bot_*.sql"))
        for old in backups[:-7]:
            old.unlink()
            print(f"Removed old backup: {old}")

    except subprocess.CalledProcessError as e:
        print(f"Backup failed: {e.stderr.decode()}")
    except FileNotFoundError:
        print("pg_dump not found. Install postgresql-client.")


if __name__ == "__main__":
    create_backup()
