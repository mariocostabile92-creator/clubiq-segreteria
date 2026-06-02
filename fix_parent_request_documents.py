import sqlite3

db_path = "clubiq.db"

conn = sqlite3.connect(db_path)
cur = conn.cursor()

columns = [
    ("certificate_file_url", "VARCHAR"),
    ("payment_receipt_url", "VARCHAR"),
]

for name, col_type in columns:
    try:
        cur.execute(f"ALTER TABLE parent_requests ADD COLUMN {name} {col_type}")
        print(f"Colonna {name} aggiunta.")
    except Exception as e:
        print(f"Nota {name}:", e)

conn.commit()

cur.execute("PRAGMA table_info(parent_requests)")
for row in cur.fetchall():
    print(row)

conn.close()