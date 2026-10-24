import sqlite3
import os

DB_DIRECTORY = 'database'
DB_PATH = os.path.join(DB_DIRECTORY, 'url_shortener.db')
SCHEMA_PATH = 'schema.sql'

# Frozen copy of the schema with the corrected short_code type.
# Used only to rebuild databases created with the old INTEGER declaration.
MIGRATION_SQL = """
BEGIN TRANSACTION;
CREATE TABLE "urls_migrated" (
	"url_id"	INTEGER NOT NULL,
	"url"	TEXT NOT NULL UNIQUE,
	"short_code"	TEXT NOT NULL UNIQUE,
	"created_at"	TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
	"updated_at"	TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
	"access_count"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("url_id" AUTOINCREMENT)
);
INSERT INTO "urls_migrated" (url_id, url, short_code, created_at, updated_at, access_count)
	SELECT url_id, url, short_code, created_at, updated_at, access_count FROM "urls";
DROP TABLE "urls";
ALTER TABLE "urls_migrated" RENAME TO "urls";
COMMIT;
"""


def get_column_type(cursor, table, column):
    """Return the declared type of a column, or None if it does not exist."""
    cursor.execute(f"PRAGMA table_info({table})")
    for row in cursor.fetchall():
        if row[1] == column:
            return row[2].upper()
    return None


def migrate_short_code_to_text(cursor):
    """
    Rebuild the 'urls' table when short_code was declared as INTEGER.

    Older databases were created with an INTEGER declaration. SQLite stores
    the short codes as TEXT anyway thanks to dynamic typing, but the declared
    type is wrong. Rebuilding the table keeps the data and fixes the schema.
    """
    column_type = get_column_type(cursor, "urls", "short_code")

    if column_type is None or column_type == "TEXT":
        return False

    cursor.executescript(MIGRATION_SQL)
    return True


# Create the database directory if it doesn't exist
os.makedirs(DB_DIRECTORY, exist_ok=True)

# Established a connection to the SQLite database
conexion = sqlite3.connect(DB_PATH)
cursor = conexion.cursor()

# Fix databases created before short_code became TEXT
migrated = migrate_short_code_to_text(cursor)

# Read the schema from the schema.sql file
with open(SCHEMA_PATH, 'r', encoding='utf-8') as schema_file:
    schema = schema_file.read()

# Apply the schema to the database
cursor.executescript(schema)

# Save the changes and close the connection
conexion.commit()
conexion.close()

if migrated:
    print("Migrated 'urls' table: short_code is now TEXT.")
print(f"Database ready at {DB_PATH}")
