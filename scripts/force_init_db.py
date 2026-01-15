#!/usr/bin/env python3
"""
Force database initialization - creates all tables from models
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def force_init():
    """Force recreate all database tables"""
    from app.db.session import init_db
    import app.models  # Import all models

    print("Initializing database with all models...")
    await init_db()
    print("✓ Database initialized successfully!")

    # Verify tables were created
    import sqlite3
    from app.config import settings

    db_path = Path(__file__).parent.parent / "database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("\nCreated tables:")
    for table in tables:
        print(f"  - {table[0]}")

    # Check for payment_status column
    cursor.execute("PRAGMA table_info(prop_firm_registration);")
    columns = cursor.fetchall()

    print("\nprop_firm_registration columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

    if any(col[1] == 'payment_status' for col in columns):
        print("\n✓ payment_status column exists!")
    else:
        print("\n✗ payment_status column NOT found!")

    conn.close()

if __name__ == "__main__":
    asyncio.run(force_init())
