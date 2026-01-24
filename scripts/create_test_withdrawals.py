import sqlite3
import uuid
from datetime import datetime, timedelta

def main():
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()

    print("--- Creating Test Withdrawals ---")

    # Check if wallet exists
    cursor.execute("SELECT id FROM wallet LIMIT 1")
    wallet = cursor.fetchone()

    if not wallet:
        print("No wallet found. Cannot create withdrawals.")
        return

    wallet_id = wallet[0]
    print(f"Using wallet ID: {wallet_id}")

    # Delete existing withdrawals to start fresh
    cursor.execute("DELETE FROM withdrawal_request")
    print("Cleared existing withdrawals.")

    withdrawals = [
        {
            "amount": 150.00,
            "payment_method": "crypto",
            "status": "pending",
            "crypto_wallet_address": "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
            "crypto_network": "eth",
            "crypto_currency": "eth",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "amount": 500.00,
            "payment_method": "bank_transfer",
            "status": "pending",
            "bank_name": "Chase Bank",
            "account_number": "1234567890",
            "account_name": "John Doe",
            "routing_number": "021000021",
            "created_at": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "amount": 200.00,
            "payment_method": "crypto",
            "status": "approved",
            "crypto_wallet_address": "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
            "crypto_network": "eth",
            "crypto_currency": "eth",
            "created_at": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "processed_at": (datetime.now() - timedelta(hours=20)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "amount": 50.00,
            "payment_method": "crypto",
            "status": "rejected",
            "crypto_wallet_address": "0xInvalidAddress",
            "crypto_network": "eth",
            "crypto_currency": "eth",
            "rejection_reason": "Invalid wallet address provided",
            "admin_notes": "User provided an invalid ETH address.",
            "created_at": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "processed_at": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "amount": 1000.00,
            "payment_method": "bank_transfer",
            "status": "completed",
            "bank_name": "Bank of America",
            "account_number": "0987654321",
            "account_name": "John Doe",
            "routing_number": "123456789",
            "created_at": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
            "processed_at": (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S")
        }
    ]

    for w in withdrawals:
        new_id = str(uuid.uuid4())

        # Construct INSERT statement dynamically based on keys
        keys = ["id", "wallet_id"] + list(w.keys())
        values = [new_id, wallet_id] + list(w.values())

        placeholders = ", ".join(["?"] * len(keys))
        columns = ", ".join(keys)

        sql = f"INSERT INTO withdrawal_request ({columns}) VALUES ({placeholders})"

        cursor.execute(sql, values)
        print(f"Created {w['status']} withdrawal ({w['payment_method']}) - ${w['amount']}")

    conn.commit()
    print("Done.")
    conn.close()

if __name__ == "__main__":
    main()
