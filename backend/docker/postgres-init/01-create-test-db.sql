SELECT 'CREATE DATABASE signos_test OWNER ' || current_user
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'signos_test')
\gexec
