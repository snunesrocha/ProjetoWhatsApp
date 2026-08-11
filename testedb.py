import sqlite3
from config import settings

conn = sqlite3.connect(settings.DATABASE_PATH)
print("Banco:", settings.DATABASE_PATH)
print("Tabelas:", conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
print("Total media:", conn.execute("SELECT COUNT(*) FROM media").fetchone()[0])
conn.close()