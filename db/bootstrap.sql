DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bank_reader') THEN
    CREATE ROLE bank_reader LOGIN PASSWORD 'bank_reader_dev_password';
  END IF;
END $$;
GRANT CONNECT ON DATABASE bank TO bank_reader;
GRANT USAGE ON SCHEMA public TO bank_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO bank_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE bank IN SCHEMA public GRANT SELECT ON TABLES TO bank_reader;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'airflow') THEN
    CREATE ROLE airflow LOGIN PASSWORD 'airflow_dev_password';
  END IF;
END $$;
SELECT 'CREATE DATABASE airflow OWNER airflow'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'airflow') \gexec
