"""
API Key Rotation Script

Generates a new API key, encrypts it with the Fernet key from FERNET_KEY env var,
stores it in the SQLite database, and deactivates all previous keys.

Usage:
    python -m scripts.rotate_api_keys
    python -m scripts.rotate_api_keys --list

Requires environment variables:
    FERNET_KEY   - Base64-encoded Fernet symmetric key
    API_KEY_DB   - Path to the SQLite database (default: ./data/api_keys.db)
"""

import os
import secrets
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

from cryptography.fernet import Fernet


def generate_new_api_key() -> str:
    return secrets.token_urlsafe(32)


def get_fernet() -> Fernet:
    """Build a Fernet instance from the FERNET_KEY environment variable."""
    fernet_key = os.getenv("FERNET_KEY")
    if not fernet_key:
        print("ERROR: FERNET_KEY environment variable is not set.")
        print(
            "Generate one with:\n"
            '  python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"'
        )
        sys.exit(1)
    return Fernet(fernet_key.encode())


def get_db_path() -> str:
    db_path = os.getenv("API_KEY_DB", os.path.join("data", "api_keys.db"))
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return db_path


def create_api_keys_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS ApiKeys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            revoked_at TEXT
        )"""
    )
    conn.commit()


def rotate_api_key(expiration_days: int = 30) -> str:
    """Generate a new key, encrypt it, store it, and deactivate old keys."""
    db_path = get_db_path()
    fernet = get_fernet()

    conn = sqlite3.connect(db_path)
    create_api_keys_table(conn)

    now = datetime.now()
    expiration = now + timedelta(days=expiration_days)

    # Deactivate all existing active keys
    conn.execute(
        "UPDATE ApiKeys SET is_active = 0, revoked_at = ? WHERE is_active = 1",
        (now.isoformat(),),
    )

    # Generate and encrypt the new key
    new_key = generate_new_api_key()
    encrypted_key = fernet.encrypt(new_key.encode()).decode()

    try:
        conn.execute(
            "INSERT INTO ApiKeys (api_key, created_at, expires_at, is_active) "
            "VALUES (?, ?, ?, 1)",
            (encrypted_key, now.isoformat(), expiration.isoformat()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        print("ERROR: Generated key collided (extremely unlikely). Try again.")
        conn.close()
        sys.exit(1)

    conn.close()

    print(f"New API key generated and stored (expires {expiration.date()})")
    print(f"Plaintext key (save this — it won't be shown again):\n  {new_key}")
    return new_key


def list_keys() -> None:
    """List recent keys in the database (metadata only, no plaintext)."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print("No database found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT id, created_at, expires_at, is_active "
        "FROM ApiKeys ORDER BY id DESC LIMIT 10"
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No keys in database.")
        return

    print(f"{'ID':<5} {'Created':<28} {'Expires':<28} {'Active'}")
    print("-" * 70)
    for row in rows:
        active = "YES" if row[3] else "no"
        print(f"{row[0]:<5} {row[1]:<28} {row[2]:<28} {active}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_keys()
    else:
        rotate_api_key()
