import sqlite3
import os

DB_PATH = "test.db"

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Checking schema...")
    cursor.execute("PRAGMA table_info(withdrawal_request)")
    columns = [info[1] for info in cursor.fetchall()]

    print(f"Current columns: {columns}")

    col = "rejection_reason"
    dtype = "VARCHAR"

    if col not in columns:
        print(f"Adding column {col}...")
        try:
            cursor.execute(f"ALTER TABLE withdrawal_request ADD COLUMN {col} {dtype}")
            print(f"Added {col}")
        except Exception as e:
            print(f"Error adding {col}: {e}")
    else:
        print(f"Column {col} already exists")

    conn.commit()
    conn.close()
    print("Schema update complete!")

if __name__ == "__main__":
    main()
