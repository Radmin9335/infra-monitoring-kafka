CREATE TABLE infra_alerts (
    id SERIAL PRIMARY KEY,
    node VARCHAR(50),
    type VARCHAR(10),
    value NUMERIC,
    timestamp TIMESTAMP
);
