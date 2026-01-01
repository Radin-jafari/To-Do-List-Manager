CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    priority INTEGER DEFAULT 2, -- 1 = high, 2 = normal, 3 = low
    due_date TEXT,              -- format: YYYY-MM-DD
    done INTEGER DEFAULT 0,     -- 0 = not done, 1 = done
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
