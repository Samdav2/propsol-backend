import sqlite3

def create_notification_table():
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()

    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification (
            id CHAR(32) NOT NULL,
            user_id CHAR(32),
            admin_id CHAR(32),
            title VARCHAR NOT NULL,
            message VARCHAR NOT NULL,
            type VARCHAR NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(user_id) REFERENCES user (id),
            FOREIGN KEY(admin_id) REFERENCES admin (id)
        )
        """)
        print("Table 'notification' created successfully.")
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_notification_table()
