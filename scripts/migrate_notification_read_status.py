#!/usr/bin/env python3
"""
Script to add is_read column to both database.db and test.db
"""
import sqlite3
from pathlib import Path

def migrate_database(db_name: str):
    """Add is_read column to notification table"""
    db_path = Path(__file__).parent.parent / db_name

    if not db_path.exists():
        print(f"Skipping {db_name} - file does not exist")
        return

    print(f"Migrating {db_name}...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notification';")
        table_exists = cursor.fetchone()

        if not table_exists:
            print(f"  Table 'notification' does not exist in {db_name}")
            return

        # Check if column already exists
        cursor.execute("PRAGMA table_info(notification);")
        columns = [row[1] for row in cursor.fetchall()]

        if 'is_read' in columns:
            print(f"  ✓ Column 'is_read' already exists in {db_name}")
            return

        # Add the column
        print(f"  Adding 'is_read' column to {db_name}...")
        cursor.execute("""
            ALTER TABLE notification
            ADD COLUMN is_read BOOLEAN NOT NULL DEFAULT FALSE;
        """)

        conn.commit()
        print(f"  ✓ Migration successful for {db_name}!")

    except sqlite3.Error as e:
        print(f"  ✗ Migration failed for {db_name}: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database("database.db")
    migrate_database("test.db")
    print("\n✓ All migrations complete!")
