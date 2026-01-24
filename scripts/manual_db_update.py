import sqlite3
import uuid
from datetime import datetime
import os

DB_PATH = "test.db"

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    email = "adoxop1@gmail.com"
    print(f"Finding user {email}...")

    cursor.execute("SELECT id FROM user WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        print(f"User {email} not found!")
        conn.close()
        return

    user_id = user[0]
    print(f"User found: {user_id}")

    # Get wallet
    cursor.execute("SELECT id, available_balance FROM wallet WHERE user_id = ?", (user_id,))
    wallet = cursor.fetchone()

    if not wallet:
        print("Wallet not found, creating...")
        wallet_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        cursor.execute(
            "INSERT INTO wallet (id, user_id, available_balance, locked_balance, total_withdrawn, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (wallet_id, user_id, 0, 0, 0, now, now)
        )
        available_balance = 0
    else:
        wallet_id = wallet[0]
        available_balance = wallet[1]
        print(f"Wallet found: {wallet_id}, Balance: {available_balance}")

    # Add balance
    amount_to_add = 200.00
    new_balance = float(available_balance) + amount_to_add
    print(f"Updating balance to {new_balance}...")

    cursor.execute("UPDATE wallet SET available_balance = ? WHERE id = ?", (new_balance, wallet_id))

    # Create withdrawal request
    print("Creating withdrawal request for $100...")
    withdrawal_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    # Note: SQLite stores UUIDs as strings usually, or bytes.
    # The models use UUID type, which in SQLite via SQLAlchemy is typically CHAR(32) or CHAR(36).
    # Let's assume standard string representation.

    cursor.execute(
        """
        INSERT INTO withdrawal_request (
            id, wallet_id, amount, payment_method, status,
            crypto_wallet_address, crypto_network, crypto_currency,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            withdrawal_id, wallet_id, 100.00, "crypto", "pending",
            "0x71C7656EC7ab88b098defB751B7401B5f6d8976F", "eth", "eth",
            now
        )
    )

    # Deduct from balance
    final_balance = new_balance - 100.00
    print(f"Deducting $100, final balance: {final_balance}...")
    cursor.execute("UPDATE wallet SET available_balance = ? WHERE id = ?", (final_balance, wallet_id))

    conn.commit()
    conn.close()
    print("Done!")

if __name__ == "__main__":
    main()
