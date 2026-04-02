-- Wells Arc Database Schema

CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    account_number TEXT UNIQUE NOT NULL,
    account_type TEXT DEFAULT 'Checking',
    balance REAL DEFAULT 0.0,
    alert_threshold REAL DEFAULT 500.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    merchant_name TEXT NOT NULL,
    amount REAL NOT NULL,
    location TEXT,
    category TEXT,
    timestamp TIMESTAMP NOT NULL,
    status TEXT DEFAULT 'active',         -- active, stopped, disputed, cleared
    flag TEXT DEFAULT 'green',            -- green, yellow, red
    flag_reason TEXT,
    anomaly_score REAL DEFAULT 0.0,
    is_recurring INTEGER DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    role TEXT NOT NULL,                   -- user, assistant
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS transaction_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT NOT NULL,
    action TEXT NOT NULL,                 -- stopped, disputed, dismissed
    actioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id)
);
