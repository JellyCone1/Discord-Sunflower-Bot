CREATE TABLE IF NOT EXISTS user_afk (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    guild_id INTEGER,
    afk_status TEXT,
    afk_since DATETIME,
    notify_enabled BOOLEAN,
    updated_at DATETIME
);

-- In SQLite, a column with type INTEGER PRIMARY KEY is an alias for the ROWID (except in WITHOUT ROWID tables) which is always a 64-bit signed integer.
-- [Section 1.2](https://www.sqlite.org/autoinc.html)
-- Also UNIQUE is redundant for PRIMARY KEY columns