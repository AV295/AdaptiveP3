-- Seed data for AP3 demo
-- Run this against the 'ap3_db' database.

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    salary INT NOT NULL
);

INSERT INTO employees (name, department, salary) VALUES
    ('Alice', 'Engineering', 120000),
    ('Bob', 'Engineering', 110000),
    ('Carol', 'HR', 80000),
    ('David', 'Finance', 95000),
    ('Eve', 'Finance', 105000)
ON CONFLICT DO NOTHING;
