BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "urls" (
	"url_id"	INTEGER NOT NULL,
	"url"	TEXT NOT NULL UNIQUE,
	"short_code"	TEXT NOT NULL UNIQUE,
	"created_at"	TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
	"updated_at"	TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
	"access_count"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("url_id" AUTOINCREMENT)
);
COMMIT;
