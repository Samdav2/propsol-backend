#!/usr/bin/env python3
"""
Database migration script to add payment_status column to prop_firm_registration table
"""
import asyncio
import sqlite3
from pathlib import Path

async def migrate_database():
    """Add payment_status column to prop_firm_registration table"""
    db_path = Path(__file__).parent.parent / "database.db"

    print(f"Migrating database at: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prop_firm_registration';")
        table_exists = cursor.fetchone()

        if not table_exists:
            print("Table 'prop_firm_registration' does not exist. It will be created on next server start.")
            return

        # Check if column already exists
        cursor.execute("PRAGMA table_info(prop_firm_registration);")
        columns = [row[1] for row in cursor.fetchall()]

        if 'payment_status' in columns:
            print("✓ Column 'payment_status' already exists!")
            return

        # Add the column
        print("Adding 'payment_status' column...")
        cursor.execute("""
            ALTER TABLE prop_firm_registration
            ADD COLUMN payment_status VARCHAR NOT NULL DEFAULT 'pending';
        """)

        conn.commit()
        print("✓ Migration successful! Column 'payment_status' added with default value 'pending'")

    except sqlite3.Error as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(migrate_database())
