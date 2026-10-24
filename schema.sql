-- Public sample data for the API demonstration. Run manually, never on startup.
CREATE TABLE IF NOT EXISTS public.records (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    value TEXT NOT NULL,
    status TEXT NOT NULL
);

-- Re-running setup preserves rows that already have these IDs.
INSERT INTO public.records (id, name, value, status) VALUES
    (1, 'Example record A', 'FastAPI', 'active'),
    (2, 'Example record B', 'Prisma Postgres', 'active'),
    (3, 'Example record C', 'Render', 'active')
ON CONFLICT (id) DO NOTHING;
