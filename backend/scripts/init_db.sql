-- Script d'initialisation PostgreSQL
-- Exécuté automatiquement au premier démarrage

-- Créer schema public (par défaut)
CREATE SCHEMA IF NOT EXISTS public;

-- Commenter pour documentation
COMMENT ON SCHEMA public IS 'Schema partagé pour tables communes (tenants, users, etc.)';

-- Extensions utiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Pour recherche texte

-- Log
DO $$
BEGIN
    RAISE NOTICE 'Database stoflow_db initialized successfully';
END $$;
