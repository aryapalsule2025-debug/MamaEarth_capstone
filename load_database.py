
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SQL_DIR = BASE_DIR / "SQL"
DB_PATH = BASE_DIR / "mamaearth_capstone.db"

schema_file = SQL_DIR / "schema.sql"
seed_file = SQL_DIR / "seed_data.sql"

# Create the database and its tables
connection = sqlite3.connect(DB_PATH)

try:
    connection.execute("PRAGMA foreign_keys = ON;")

    schema_sql = schema_file.read_text(encoding="utf-8-sig")
    connection.executescript(schema_sql)

    seed_sql = seed_file.read_text(encoding="utf-8-sig")
    connection.executescript(seed_sql)

    # Verify the number of rows in each table
    for table in ("customers", "products", "orders"):
        count = connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
        print(f"{table}: {count} rows")

    connection.commit()
    print(f"\nDatabase created: {DB_PATH}")

except Exception:
    connection.rollback()
    raise

finally:
    connection.close()
