CREATE TABLE IF NOT EXISTS negotiations (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    load_id TEXT NOT NULL,
    miles INT,
    loadboard_rate NUMERIC,
    price TEXT,
    user_message TEXT,
    user_requested_price TEXT,
    cur_round INT DEFAULT 0,
    max_rounds INT DEFAULT 3,
    ai_negotiated_price TEXT,
    ai_negotiated_reason TEXT,
    history TEXT NOT NULL,  -- NEW column for full structured back-and-forth
    ts TIMESTAMP DEFAULT NOW(),
    sentiment TEXT
);