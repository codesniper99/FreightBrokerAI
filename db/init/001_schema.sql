-- Enable UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS loads (

  -- from your table
  load_id           TEXT UNIQUE PRIMARY KEY NOT NULL,           -- business identifier
  origin            TEXT NOT NULL,                  -- starting location
  destination       TEXT NOT NULL,                  -- delivery location
  pickup_datetime   TIMESTAMPTZ NOT NULL,           -- date/time for pickup
  delivery_datetime TIMESTAMPTZ NOT NULL,           -- date/time for delivery
  equipment_type    TEXT NOT NULL,                  -- type of equipment needed
  loadboard_rate    NUMERIC(10,2),                  -- listed rate
  notes             TEXT,                           -- additional info
  weight            INTEGER,                        -- load weight (kg)
  commodity_type    TEXT,                           -- type of goods
  num_of_pieces     INTEGER,                        -- number of items
  miles             INTEGER,                        -- distance to travel
  dimensions        JSONB                           -- {length,width,height,unit}
);

-- Useful indexes
CREATE INDEX IF NOT EXISTS idx_loads_pickup ON loads (pickup_datetime);
CREATE INDEX IF NOT EXISTS idx_loads_o_d ON loads (origin, destination);
