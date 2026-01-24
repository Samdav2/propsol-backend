import sqlite3
import uuid

def main():
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()

    print("--- Resetting DB (Sync) ---")

    # Check if wallet exists
    cursor.execute("SELECT id FROM wallet LIMIT 1")
    wallet = cursor.fetchone()

    if not wallet:
        print("No wallet found. Cannot create withdrawal.")
        return

    wallet_id = wallet[0]
    print(f"Using wallet ID: {wallet_id}")

    # Delete all withdrawals
    cursor.execute("DELETE FROM withdrawal_request")
    print("Deleted all withdrawals.")

    # Create new withdrawal
    # SQLite stores UUIDs as strings usually
    new_id = str(uuid.uuid4())

    # We need to match the columns in the table.
    # Let's inspect columns first to be safe, or just insert with specific columns.
    # withdrawal_request columns: id, wallet_id, amount, payment_method, status, created_at, ...

    cursor.execute("""
        INSERT INTO withdrawal_request (id, wallet_id, amount, payment_method, status, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, (new_id, wallet_id, 100.00, "crypto", "pending"))

    conn.commit()
    print(f"Created new withdrawal with ID: {new_id}")

    conn.close()

if __name__ == "__main__":
    main()
