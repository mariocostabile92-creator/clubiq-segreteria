import sqlite3

db_path = "clubiq.db"

conn = sqlite3.connect(db_path)
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE clubs ADD COLUMN public_code VARCHAR")
    print("Colonna public_code aggiunta.")
except Exception as e:
    print("Nota colonna:", e)

try:
    cur.execute("CREATE UNIQUE INDEX ix_clubs_public_code ON clubs(public_code)")
    print("Indice public_code creato.")
except Exception as e:
    print("Nota indice:", e)

cur.execute("UPDATE clubs SET public_code = 'CLUBIQTEST' WHERE public_code IS NULL")
conn.commit()

cur.execute("SELECT id, name, public_code FROM clubs")
rows = cur.fetchall()

print("Club trovati:")
for row in rows:
    print(row)

conn.close()