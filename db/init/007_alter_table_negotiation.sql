ALTER TABLE negotiations
    ADD COLUMN miles INT,
    ADD COLUMN loadboard_rate NUMERIC,
    ADD COLUMN history TEXT NOT NULL;