import sqlite3

def add_column():
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE prop_firm_registration ADD COLUMN account_status VARCHAR NOT NULL DEFAULT 'pending'")
        print("Column 'account_status' added successfully.")
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_column()
