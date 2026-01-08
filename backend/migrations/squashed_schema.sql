
\restrict Hboc06VsLwF69LAYeYxqTdQtgzwRvAaHkE7YIqfJg1yelCGRbZuRFQaIurSU9QS




CREATE SCHEMA product_attributes;



CREATE SCHEMA public;



COMMENT ON SCHEMA public IS 'Schema partagé pour tables communes (tenants, users, etc.)';



CREATE SCHEMA template_tenant;



CREATE TYPE public.account_type AS ENUM (
    'individual',
    'professional'
);



CREATE TYPE public.business_type AS ENUM (
    'resale',
    'dropshipping',
    'artisan',
    'retail',
    'other'
);



CREATE TYPE public.datadomestatus AS ENUM (
    'OK',
    'FAILED',
    'UNKNOWN'
);



CREATE TYPE public.estimated_products AS ENUM (
    '0-50',
    '50-200',
    '200-500',
    '500+'
);



CREATE TYPE public.gender AS ENUM (
    'male',
    'female',
    'unisex'
);



CREATE TYPE public.jobstatus AS ENUM (
    'pending',
    'running',
    'paused',
    'completed',
    'failed',
    'cancelled',
    'expired'
);



CREATE TYPE public.platform_type AS ENUM (
    'VINTED',
    'EBAY',
    'ETSY'
);



CREATE TYPE public.product_status AS ENUM (
    'DRAFT',
    'PENDING_REVIEW',
    'APPROVED',
    'REJECTED',
    'SCHEDULED',
    'PUBLISHED',
    'SUSPENDED',
    'FLAGGED',
    'SOLD',
    'ARCHIVED'
);



CREATE TYPE public.publication_status AS ENUM (
    'PENDING',
    'SUCCESS',
    'FAILED'
);



CREATE TYPE public.subscription_tier AS ENUM (
    'FREE',
    'STARTER',
    'PRO',
    'ENTERPRISE'
);



CREATE TYPE public.taskstatus AS ENUM (
    'pending',
    'processing',
    'success',
    'failed',
    'timeout',
    'cancelled'
);



CREATE TYPE public.user_role AS ENUM (
    'ADMIN',
    'USER',
    'SUPPORT'
);



CREATE TYPE public.userrole AS ENUM (
    'admin',
    'user',
    'support'
);



CREATE TYPE template_tenant.batch_job_status AS ENUM (
    'pending',
    'running',
    'completed',
    'partially_failed',
    'failed',
    'cancelled'
);



CREATE TYPE template_tenant.marketplace_task_type AS ENUM (
    'plugin_http',
    'direct_http',
    'db_operation',
    'file_operation'
);



CREATE FUNCTION public.get_vinted_category(p_category character varying, p_gender character varying, p_fit character varying DEFAULT NULL::character varying, p_length character varying DEFAULT NULL::character varying, p_rise character varying DEFAULT NULL::character varying, p_material character varying DEFAULT NULL::character varying, p_pattern character varying DEFAULT NULL::character varying, p_neckline character varying DEFAULT NULL::character varying, p_sleeve_length character varying DEFAULT NULL::character varying) RETURNS integer
    LANGUAGE plpgsql
    AS $$
        BEGIN
            RETURN vinted.get_vinted_category(
                p_category, p_gender, p_fit, p_length, p_rise,
                p_material, p_pattern, p_neckline, p_sleeve_length
            );
        END;
        $$;





CREATE TABLE product_attributes.brands (
    name character varying(100) NOT NULL,
    description text,
    vinted_id text,
    monitoring boolean DEFAULT false NOT NULL,
    sector_jeans character varying(20),
    sector_jacket character varying(20)
);



COMMENT ON COLUMN product_attributes.brands.name IS 'Nom de la marque (EN)';



COMMENT ON COLUMN product_attributes.brands.description IS 'Description de la marque';



COMMENT ON COLUMN product_attributes.brands.vinted_id IS 'ID Vinted pour intégration marketplace';



COMMENT ON COLUMN product_attributes.brands.monitoring IS 'Marque surveillée (tracking spécial)';



COMMENT ON COLUMN product_attributes.brands.sector_jeans IS 'Segment de marché pour les jeans: BUDGET, STANDARD, HYPE, PREMIUM, ULTRA PREMIUM';



COMMENT ON COLUMN product_attributes.brands.sector_jacket IS 'Segment de marché pour les vestes: BUDGET, STANDARD, HYPE, PREMIUM, ULTRA PREMIUM';



CREATE TABLE product_attributes.categories (
    name_en character varying(100) NOT NULL,
    parent_category character varying(100),
    name_fr character varying(255),
    name_de character varying(255),
    name_it character varying(255),
    name_es character varying(255),
    name_nl character varying(255),
    name_pl character varying(255),
    genders character varying(20)[]
);



COMMENT ON COLUMN product_attributes.categories.name_en IS 'Nom de la catégorie (EN)';



COMMENT ON COLUMN product_attributes.categories.parent_category IS 'Catégorie parente (self-reference)';



COMMENT ON COLUMN product_attributes.categories.name_fr IS 'Nom de la catégorie (FR)';



COMMENT ON COLUMN product_attributes.categories.name_de IS 'Nom de la catégorie (DE)';



COMMENT ON COLUMN product_attributes.categories.name_it IS 'Nom de la catégorie (IT)';



COMMENT ON COLUMN product_attributes.categories.name_es IS 'Nom de la catégorie (ES)';



COMMENT ON COLUMN product_attributes.categories.name_nl IS 'Nom de la catégorie (NL)';



COMMENT ON COLUMN product_attributes.categories.name_pl IS 'Nom de la catégorie (PL)';



COMMENT ON COLUMN product_attributes.categories.genders IS 'Available genders for this category';



CREATE TABLE product_attributes.closures (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);



COMMENT ON COLUMN product_attributes.closures.name_en IS 'Type de fermeture (EN)';



COMMENT ON COLUMN product_attributes.closures.name_fr IS 'Type de fermeture (FR)';



COMMENT ON COLUMN product_attributes.closures.name_de IS 'Type de fermeture (DE)';



COMMENT ON COLUMN product_attributes.closures.name_it IS 'Type de fermeture (IT)';



COMMENT ON COLUMN product_attributes.closures.name_es IS 'Type de fermeture (ES)';



COMMENT ON COLUMN product_attributes.closures.name_nl IS 'Type de fermeture (NL)';



COMMENT ON COLUMN product_attributes.closures.name_pl IS 'Type de fermeture (PL)';



CREATE TABLE product_attributes.colors (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100),
    hex_code character varying(7),
    vinted_id integer,
    parent_color character varying(100)
);



COMMENT ON COLUMN product_attributes.colors.name_en IS 'Nom de la couleur (EN)';



COMMENT ON COLUMN product_attributes.colors.name_fr IS 'Nom de la couleur (FR)';



COMMENT ON COLUMN product_attributes.colors.name_de IS 'Nom de la couleur (DE)';



COMMENT ON COLUMN product_attributes.colors.name_it IS 'Nom de la couleur (IT)';



COMMENT ON COLUMN product_attributes.colors.name_es IS 'Nom de la couleur (ES)';



COMMENT ON COLUMN product_attributes.colors.name_nl IS 'Nom de la couleur (NL)';



COMMENT ON COLUMN product_attributes.colors.name_pl IS 'Nom de la couleur (PL)';



COMMENT ON COLUMN product_attributes.colors.hex_code IS 'Code couleur hexadécimal (#RRGGBB)';



CREATE TABLE product_attributes.condition_sups (
    name_en character varying(255) NOT NULL,
    name_fr character varying(255),
    name_de character varying(255),
    name_it character varying(255),
    name_es character varying(255),
    name_nl character varying(255),
    name_pl character varying(255)
);



CREATE TABLE product_attributes.conditions (
    note integer NOT NULL,
    name_en character varying(100) NOT NULL,
    name_fr character varying(100) NOT NULL,
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100),
    vinted_id bigint,
    ebay_condition text,
    coefficient numeric(4,3) DEFAULT 1.000,
    CONSTRAINT conditions_new_note_check CHECK (((note >= 0) AND (note <= 10)))
);



CREATE TABLE product_attributes.decades (
    name_en character varying(100) NOT NULL
);



COMMENT ON COLUMN product_attributes.decades.name_en IS 'Décennie (EN)';



CREATE TABLE product_attributes.dim1 (
    value integer NOT NULL,
    CONSTRAINT dim1_value_positive CHECK ((value > 0))
);



COMMENT ON TABLE product_attributes.dim1 IS 'Chest / Shoulders (cm) - Tour de poitrine / Épaules (cm)';



CREATE TABLE product_attributes.dim2 (
    value integer NOT NULL,
    CONSTRAINT dim2_value_positive CHECK ((value > 0))
);



COMMENT ON TABLE product_attributes.dim2 IS 'Total length (cm) - Longueur totale (cm)';



CREATE TABLE product_attributes.dim3 (
    value integer NOT NULL,
    CONSTRAINT dim3_value_positive CHECK ((value > 0))
);



COMMENT ON TABLE product_attributes.dim3 IS 'Sleeve length (cm) - Longueur manche (cm)';



CREATE TABLE product_attributes.dim4 (
    value integer NOT NULL,
    CONSTRAINT dim4_value_positive CHECK ((value > 0))
);



COMMENT ON TABLE product_attributes.dim4 IS 'Waist (cm) - Tour de taille (cm)';



CREATE TABLE product_attributes.dim5 (
    value integer NOT NULL,
    CONSTRAINT dim5_value_positive CHECK ((value > 0))
);



COMMENT ON TABLE product_attributes.dim5 IS 'Hips (cm) - Tour de hanches (cm)';



CREATE TABLE product_attributes.dim6 (
    value integer NOT NULL,
    CONSTRAINT dim6_value_positive CHECK ((value > 0))
);



COMMENT ON TABLE product_attributes.dim6 IS 'Inseam (cm) - Entrejambe (cm)';



CREATE TABLE product_attributes.fits (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);



COMMENT ON COLUMN product_attributes.fits.name_en IS 'Coupe (EN)';



COMMENT ON COLUMN product_attributes.fits.name_fr IS 'Coupe (FR)';



COMMENT ON COLUMN product_attributes.fits.name_de IS 'Coupe (DE)';



COMMENT ON COLUMN product_attributes.fits.name_it IS 'Coupe (IT)';



COMMENT ON COLUMN product_attributes.fits.name_es IS 'Coupe (ES)';



COMMENT ON COLUMN product_attributes.fits.name_nl IS 'Coupe (NL)';



COMMENT ON COLUMN product_attributes.fits.name_pl IS 'Coupe (PL)';



CREATE TABLE product_attributes.genders (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100),
    vinted_id integer,
    ebay_gender character varying(50),
    etsy_gender character varying(50)
);



COMMENT ON COLUMN product_attributes.genders.name_en IS 'Genre (EN)';



COMMENT ON COLUMN product_attributes.genders.name_fr IS 'Genre (FR)';



COMMENT ON COLUMN product_attributes.genders.name_de IS 'Genre (DE)';



COMMENT ON COLUMN product_attributes.genders.name_it IS 'Genre (IT)';



COMMENT ON COLUMN product_attributes.genders.name_es IS 'Genre (ES)';



COMMENT ON COLUMN product_attributes.genders.name_nl IS 'Genre (NL)';



COMMENT ON COLUMN product_attributes.genders.name_pl IS 'Genre (PL)';



COMMENT ON COLUMN product_attributes.genders.vinted_id IS 'ID genre Vinted';



COMMENT ON COLUMN product_attributes.genders.ebay_gender IS 'Genre eBay correspondant';



COMMENT ON COLUMN product_attributes.genders.etsy_gender IS 'Genre Etsy correspondant';



CREATE TABLE product_attributes.lengths (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    description text,
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);



COMMENT ON COLUMN product_attributes.lengths.name_en IS 'Nom de la longueur (EN)';



COMMENT ON COLUMN product_attributes.lengths.name_fr IS 'Nom de la longueur (FR)';



COMMENT ON COLUMN product_attributes.lengths.description IS 'Description de la longueur';



COMMENT ON COLUMN product_attributes.lengths.name_de IS 'Nom de la longueur (DE)';



COMMENT ON COLUMN product_attributes.lengths.name_it IS 'Nom de la longueur (IT)';



COMMENT ON COLUMN product_attributes.lengths.name_es IS 'Nom de la longueur (ES)';



COMMENT ON COLUMN product_attributes.lengths.name_nl IS 'Nom de la longueur (NL)';



COMMENT ON COLUMN product_attributes.lengths.name_pl IS 'Nom de la longueur (PL)';



CREATE TABLE product_attributes.linings (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);



CREATE TABLE product_attributes.materials (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100),
    vinted_id integer
);



COMMENT ON COLUMN product_attributes.materials.name_en IS 'Matière (EN)';



COMMENT ON COLUMN product_attributes.materials.name_fr IS 'Matière (FR)';



COMMENT ON COLUMN product_attributes.materials.name_de IS 'Matière (DE)';



COMMENT ON COLUMN product_attributes.materials.name_it IS 'Matière (IT)';



COMMENT ON COLUMN product_attributes.materials.name_es IS 'Matière (ES)';



COMMENT ON COLUMN product_attributes.materials.name_nl IS 'Matière (NL)';



COMMENT ON COLUMN product_attributes.materials.name_pl IS 'Matière (PL)';



COMMENT ON COLUMN product_attributes.materials.vinted_id IS 'Vinted material ID';



CREATE TABLE product_attributes.necklines (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    description text,
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);



COMMENT ON COLUMN product_attributes.necklines.name_en IS 'Nom de l''encolure (EN)';



COMMENT ON COLUMN product_attributes.necklines.name_fr IS 'Nom de l''encolure (FR)';



COMMENT ON COLUMN product_attributes.necklines.description IS 'Description de l''encolure';



COMMENT ON COLUMN product_attributes.necklines.name_de IS 'Nom de l''encolure (DE)';



COMMENT ON COLUMN product_attributes.necklines.name_it IS 'Nom de l''encolure (IT)';



COMMENT ON COLUMN product_attributes.necklines.name_es IS 'Nom de l''encolure (ES)';



COMMENT ON COLUMN product_attributes.necklines.name_nl IS 'Nom de l''encolure (NL)';



COMMENT ON COLUMN product_attributes.necklines.name_pl IS 'Nom de l''encolure (PL)';



CREATE TABLE product_attributes.origins (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);



COMMENT ON COLUMN product_attributes.origins.name_en IS 'Origine/Provenance (EN)';



COMMENT ON COLUMN product_attributes.origins.name_fr IS 'Origine/Provenance (FR)';



COMMENT ON COLUMN product_attributes.origins.name_de IS 'Origine/Provenance (DE)';



COMMENT ON COLUMN product_attributes.origins.name_it IS 'Origine/Provenance (IT)';



COMMENT ON COLUMN product_attributes.origins.name_es IS 'Origine/Provenance (ES)';



COMMENT ON COLUMN product_attributes.origins.name_nl IS 'Origine/Provenance (NL)';



COMMENT ON COLUMN product_attributes.origins.name_pl IS 'Origine/Provenance (PL)';



CREATE TABLE product_attributes.patterns (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    description text,
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);



COMMENT ON COLUMN product_attributes.patterns.name_en IS 'Nom du motif (EN)';



COMMENT ON COLUMN product_attributes.patterns.name_fr IS 'Nom du motif (FR)';



COMMENT ON COLUMN product_attributes.patterns.description IS 'Description du motif';



COMMENT ON COLUMN product_attributes.patterns.name_de IS 'Nom du motif (DE)';



COMMENT ON COLUMN product_attributes.patterns.name_it IS 'Nom du motif (IT)';



COMMENT ON COLUMN product_attributes.patterns.name_es IS 'Nom du motif (ES)';



COMMENT ON COLUMN product_attributes.patterns.name_nl IS 'Nom du motif (NL)';



COMMENT ON COLUMN product_attributes.patterns.name_pl IS 'Nom du motif (PL)';



CREATE TABLE product_attributes.rises (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);



COMMENT ON COLUMN product_attributes.rises.name_en IS 'Hauteur de taille (EN)';



COMMENT ON COLUMN product_attributes.rises.name_fr IS 'Hauteur de taille (FR)';



COMMENT ON COLUMN product_attributes.rises.name_de IS 'Hauteur de taille (DE)';



COMMENT ON COLUMN product_attributes.rises.name_it IS 'Hauteur de taille (IT)';



COMMENT ON COLUMN product_attributes.rises.name_es IS 'Hauteur de taille (ES)';



COMMENT ON COLUMN product_attributes.rises.name_nl IS 'Hauteur de taille (NL)';



COMMENT ON COLUMN product_attributes.rises.name_pl IS 'Hauteur de taille (PL)';



CREATE TABLE product_attributes.seasons (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);



COMMENT ON COLUMN product_attributes.seasons.name_en IS 'Saison (EN)';



COMMENT ON COLUMN product_attributes.seasons.name_fr IS 'Saison (FR)';



COMMENT ON COLUMN product_attributes.seasons.name_de IS 'Saison (DE)';



COMMENT ON COLUMN product_attributes.seasons.name_it IS 'Saison (IT)';



COMMENT ON COLUMN product_attributes.seasons.name_es IS 'Saison (ES)';



COMMENT ON COLUMN product_attributes.seasons.name_nl IS 'Saison (NL)';



COMMENT ON COLUMN product_attributes.seasons.name_pl IS 'Saison (PL)';



CREATE TABLE product_attributes.sizes_normalized (
    name_en character varying(100) NOT NULL,
    ebay_size character varying(50),
    etsy_size character varying(50),
    vinted_women_id integer,
    vinted_men_id integer
);



COMMENT ON COLUMN product_attributes.sizes_normalized.name_en IS 'Taille (EN)';



COMMENT ON COLUMN product_attributes.sizes_normalized.ebay_size IS 'Taille eBay correspondante';



COMMENT ON COLUMN product_attributes.sizes_normalized.etsy_size IS 'Taille Etsy correspondante';



CREATE TABLE product_attributes.sizes_original (
    name character varying(100) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);



CREATE TABLE product_attributes.sleeve_lengths (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);



COMMENT ON COLUMN product_attributes.sleeve_lengths.name_en IS 'Longueur de manche (EN)';



COMMENT ON COLUMN product_attributes.sleeve_lengths.name_fr IS 'Longueur de manche (FR)';



COMMENT ON COLUMN product_attributes.sleeve_lengths.name_de IS 'Longueur de manche (DE)';



COMMENT ON COLUMN product_attributes.sleeve_lengths.name_it IS 'Longueur de manche (IT)';



COMMENT ON COLUMN product_attributes.sleeve_lengths.name_es IS 'Longueur de manche (ES)';



COMMENT ON COLUMN product_attributes.sleeve_lengths.name_nl IS 'Longueur de manche (NL)';



COMMENT ON COLUMN product_attributes.sleeve_lengths.name_pl IS 'Longueur de manche (PL)';



CREATE TABLE product_attributes.sports (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    description text,
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);



COMMENT ON COLUMN product_attributes.sports.name_en IS 'Nom du sport (EN)';



COMMENT ON COLUMN product_attributes.sports.name_fr IS 'Nom du sport (FR)';



COMMENT ON COLUMN product_attributes.sports.description IS 'Description du sport';



COMMENT ON COLUMN product_attributes.sports.name_de IS 'Nom du sport (DE)';



COMMENT ON COLUMN product_attributes.sports.name_it IS 'Nom du sport (IT)';



COMMENT ON COLUMN product_attributes.sports.name_es IS 'Nom du sport (ES)';



COMMENT ON COLUMN product_attributes.sports.name_nl IS 'Nom du sport (NL)';



COMMENT ON COLUMN product_attributes.sports.name_pl IS 'Nom du sport (PL)';



CREATE TABLE product_attributes.stretches (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);



CREATE TABLE product_attributes.trends (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);



COMMENT ON COLUMN product_attributes.trends.name_en IS 'Tendance/Style (EN)';



COMMENT ON COLUMN product_attributes.trends.name_fr IS 'Tendance/Style (FR)';



COMMENT ON COLUMN product_attributes.trends.name_de IS 'Tendance/Style (DE)';



COMMENT ON COLUMN product_attributes.trends.name_it IS 'Tendance/Style (IT)';



COMMENT ON COLUMN product_attributes.trends.name_es IS 'Tendance/Style (ES)';



COMMENT ON COLUMN product_attributes.trends.name_nl IS 'Tendance/Style (NL)';



COMMENT ON COLUMN product_attributes.trends.name_pl IS 'Tendance/Style (PL)';



CREATE TABLE product_attributes.unique_features (
    name_en character varying(255) NOT NULL,
    name_fr character varying(255),
    name_de character varying(255),
    name_it character varying(255),
    name_es character varying(255),
    name_nl character varying(255),
    name_pl character varying(255)
);



COMMENT ON COLUMN product_attributes.unique_features.name_en IS 'Caractéristique unique (EN)';



COMMENT ON COLUMN product_attributes.unique_features.name_fr IS 'Caractéristique unique (FR)';



COMMENT ON COLUMN product_attributes.unique_features.name_de IS 'Caractéristique unique (DE)';



COMMENT ON COLUMN product_attributes.unique_features.name_it IS 'Caractéristique unique (IT)';



COMMENT ON COLUMN product_attributes.unique_features.name_es IS 'Caractéristique unique (ES)';



COMMENT ON COLUMN product_attributes.unique_features.name_nl IS 'Caractéristique unique (NL)';



COMMENT ON COLUMN product_attributes.unique_features.name_pl IS 'Caractéristique unique (PL)';



CREATE VIEW product_attributes.vw_dimension_info AS
 SELECT 'dim1'::text AS dimension,
    'Chest / Shoulders'::text AS name_en,
    'Tour de poitrine / Épaules'::text AS name_fr,
    'cm'::text AS unit,
    30 AS min_value,
    80 AS max_value
UNION ALL
 SELECT 'dim2'::text AS dimension,
    'Total length'::text AS name_en,
    'Longueur totale'::text AS name_fr,
    'cm'::text AS unit,
    40 AS min_value,
    120 AS max_value
UNION ALL
 SELECT 'dim3'::text AS dimension,
    'Sleeve length'::text AS name_en,
    'Longueur manche'::text AS name_fr,
    'cm'::text AS unit,
    20 AS min_value,
    80 AS max_value
UNION ALL
 SELECT 'dim4'::text AS dimension,
    'Waist'::text AS name_en,
    'Tour de taille'::text AS name_fr,
    'cm'::text AS unit,
    25 AS min_value,
    60 AS max_value
UNION ALL
 SELECT 'dim5'::text AS dimension,
    'Hips'::text AS name_en,
    'Tour de hanches'::text AS name_fr,
    'cm'::text AS unit,
    30 AS min_value,
    80 AS max_value
UNION ALL
 SELECT 'dim6'::text AS dimension,
    'Inseam'::text AS name_en,
    'Entrejambe'::text AS name_fr,
    'cm'::text AS unit,
    20 AS min_value,
    100 AS max_value;



CREATE TABLE public.admin_audit_logs (
    id integer NOT NULL,
    admin_id integer,
    action character varying(50) NOT NULL,
    resource_type character varying(50) NOT NULL,
    resource_id character varying(100),
    resource_name character varying(255),
    details json,
    ip_address character varying(45),
    user_agent character varying(500),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);



COMMENT ON COLUMN public.admin_audit_logs.action IS 'Action type: CREATE, UPDATE, DELETE, TOGGLE_ACTIVE, UNLOCK';



COMMENT ON COLUMN public.admin_audit_logs.resource_type IS 'Resource type: user, brand, category, color, material';



COMMENT ON COLUMN public.admin_audit_logs.resource_id IS 'Primary key of the affected resource';



COMMENT ON COLUMN public.admin_audit_logs.resource_name IS 'Human-readable name of the resource';



COMMENT ON COLUMN public.admin_audit_logs.details IS 'Changed fields, before/after values';



COMMENT ON COLUMN public.admin_audit_logs.ip_address IS 'IP address of the admin';



COMMENT ON COLUMN public.admin_audit_logs.user_agent IS 'User agent of the admin browser';



CREATE SEQUENCE public.admin_audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE public.admin_audit_logs_id_seq OWNED BY public.admin_audit_logs.id;



CREATE TABLE public.ai_credits (
    id integer NOT NULL,
    user_id integer NOT NULL,
    ai_credits_purchased integer DEFAULT 0 NOT NULL,
    ai_credits_used_this_month integer DEFAULT 0 NOT NULL,
    last_reset_date timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);



COMMENT ON COLUMN public.ai_credits.user_id IS 'Utilisateur propriétaire';



COMMENT ON COLUMN public.ai_credits.ai_credits_purchased IS 'Crédits IA achetés (cumulables, ne s''épuisent pas)';



COMMENT ON COLUMN public.ai_credits.ai_credits_used_this_month IS 'Crédits IA utilisés ce mois-ci';



COMMENT ON COLUMN public.ai_credits.last_reset_date IS 'Date du dernier reset mensuel';



CREATE SEQUENCE public.ai_credits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE public.ai_credits_id_seq OWNED BY public.ai_credits.id;



CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);



CREATE TABLE public.clothing_prices (
    brand character varying(100) NOT NULL,
    category character varying(255) NOT NULL,
    base_price numeric(10,2) NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_base_price_positive CHECK ((base_price >= (0)::numeric))
);



COMMENT ON TABLE public.clothing_prices IS 'Prix de base par brand/category pour calcul automatique';



COMMENT ON COLUMN public.clothing_prices.brand IS 'Marque (FK product_attributes.brands.name)';



COMMENT ON COLUMN public.clothing_prices.category IS 'Catégorie (FK product_attributes.categories.name_en)';



COMMENT ON COLUMN public.clothing_prices.base_price IS 'Prix de base en euros';



COMMENT ON COLUMN public.clothing_prices.updated_at IS 'Date de dernière mise à jour du prix';



CREATE TABLE public.doc_articles (
    id integer NOT NULL,
    category_id integer NOT NULL,
    slug character varying(200) NOT NULL,
    title character varying(200) NOT NULL,
    summary character varying(500),
    content text NOT NULL,
    display_order integer DEFAULT 0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);



COMMENT ON COLUMN public.doc_articles.category_id IS 'Parent category ID';



COMMENT ON COLUMN public.doc_articles.slug IS 'URL-friendly identifier';



COMMENT ON COLUMN public.doc_articles.title IS 'Article title';



COMMENT ON COLUMN public.doc_articles.summary IS 'Short excerpt';



COMMENT ON COLUMN public.doc_articles.content IS 'Markdown content';



COMMENT ON COLUMN public.doc_articles.display_order IS 'Order within category';



COMMENT ON COLUMN public.doc_articles.is_active IS 'Whether visible';



CREATE SEQUENCE public.doc_articles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE public.doc_articles_id_seq OWNED BY public.doc_articles.id;



CREATE TABLE public.doc_categories (
    id integer NOT NULL,
    slug character varying(100) NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    icon character varying(50),
    display_order integer DEFAULT 0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);



COMMENT ON COLUMN public.doc_categories.slug IS 'URL-friendly identifier';



COMMENT ON COLUMN public.doc_categories.name IS 'Display name';



COMMENT ON COLUMN public.doc_categories.description IS 'Short description';



COMMENT ON COLUMN public.doc_categories.icon IS 'PrimeIcons class';



COMMENT ON COLUMN public.doc_categories.display_order IS 'Order in navigation';



COMMENT ON COLUMN public.doc_categories.is_active IS 'Whether visible';



CREATE SEQUENCE public.doc_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE public.doc_categories_id_seq OWNED BY public.doc_categories.id;



CREATE TABLE public.migration_errors (
    id integer NOT NULL,
    schema_name character varying(100) NOT NULL,
    product_id integer NOT NULL,
    migration_name character varying(255) NOT NULL,
    error_type character varying(100) NOT NULL,
    error_details text,
    migrated_at timestamp without time zone DEFAULT now() NOT NULL
);



CREATE SEQUENCE public.migration_errors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE public.migration_errors_id_seq OWNED BY public.migration_errors.id;



CREATE TABLE public.permissions (
    id integer NOT NULL,
    code character varying(100) NOT NULL,
    name character varying(255) NOT NULL,
    description character varying(500),
    category character varying(50) NOT NULL,
    is_active boolean DEFAULT true NOT NULL
);



COMMENT ON COLUMN public.permissions.code IS 'Unique permission code (e.g., ''products:create'')';



COMMENT ON COLUMN public.permissions.name IS 'Human-readable permission name';



COMMENT ON COLUMN public.permissions.description IS 'Description of what this permission allows';



COMMENT ON COLUMN public.permissions.category IS 'Permission category for grouping';



COMMENT ON COLUMN public.permissions.is_active IS 'Whether this permission is active';



CREATE SEQUENCE public.permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE public.permissions_id_seq OWNED BY public.permissions.id;



CREATE TABLE public.revoked_tokens (
    token_hash character varying(255) NOT NULL,
    revoked_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL
);



CREATE TABLE public.role_permissions (
    id integer NOT NULL,
    role public.userrole NOT NULL,
    permission_id integer NOT NULL
);



COMMENT ON COLUMN public.role_permissions.role IS 'User role';



COMMENT ON COLUMN public.role_permissions.permission_id IS 'Permission ID';



CREATE SEQUENCE public.role_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE public.role_permissions_id_seq OWNED BY public.role_permissions.id;



CREATE TABLE public.subscription_features (
    id integer NOT NULL,
    subscription_quota_id integer NOT NULL,
    feature_text character varying(200) NOT NULL,
    display_order integer DEFAULT 0 NOT NULL
);



CREATE SEQUENCE public.subscription_features_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE public.subscription_features_id_seq OWNED BY public.subscription_features.id;



CREATE TABLE public.subscription_quotas (
    id integer NOT NULL,
    tier public.subscription_tier NOT NULL,
    max_products integer NOT NULL,
    max_platforms integer NOT NULL,
    ai_credits_monthly integer NOT NULL,
    price numeric(10,2) DEFAULT 0.00 NOT NULL,
    display_name character varying(50) DEFAULT ''::character varying NOT NULL,
    description character varying(200),
    annual_discount_percent integer DEFAULT 20 NOT NULL,
    is_popular boolean DEFAULT false NOT NULL,
    cta_text character varying(100),
    display_order integer DEFAULT 0 NOT NULL
);



COMMENT ON COLUMN public.subscription_quotas.max_products IS 'Nombre maximum de produits actifs';



COMMENT ON COLUMN public.subscription_quotas.max_platforms IS 'Nombre maximum de plateformes connectées';



COMMENT ON COLUMN public.subscription_quotas.ai_credits_monthly IS 'Crédits IA mensuels';



COMMENT ON COLUMN public.subscription_quotas.price IS 'Prix mensuel de l''abonnement en euros';



CREATE SEQUENCE public.subscription_quotas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE public.subscription_quotas_id_seq OWNED BY public.subscription_quotas.id;



CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    full_name character varying(255) NOT NULL,
    role public.user_role NOT NULL,
    is_active boolean NOT NULL,
    last_login timestamp with time zone,
    subscription_tier public.subscription_tier NOT NULL,
    subscription_status character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    business_name character varying(255),
    account_type public.account_type DEFAULT 'individual'::public.account_type NOT NULL,
    business_type public.business_type,
    estimated_products public.estimated_products,
    siret character varying(14),
    vat_number character varying(20),
    phone character varying(20),
    country character varying(2) DEFAULT 'FR'::character varying NOT NULL,
    language character varying(2) DEFAULT 'fr'::character varying NOT NULL,
    subscription_tier_id integer NOT NULL,
    current_products_count integer DEFAULT 0 NOT NULL,
    current_platforms_count integer DEFAULT 0 NOT NULL,
    stripe_customer_id character varying(255),
    stripe_subscription_id character varying(255),
    failed_login_attempts integer DEFAULT 0 NOT NULL,
    last_failed_login timestamp with time zone,
    locked_until timestamp with time zone,
    email_verified boolean DEFAULT false NOT NULL,
    email_verification_token character varying(64),
    email_verification_expires timestamp with time zone,
    password_changed_at timestamp with time zone
);



COMMENT ON COLUMN public.users.subscription_status IS 'active, suspended, cancelled';



COMMENT ON COLUMN public.users.business_name IS 'Nom de l''entreprise ou de la boutique';



COMMENT ON COLUMN public.users.account_type IS 'Type de compte: individual (particulier) ou professional (entreprise)';



COMMENT ON COLUMN public.users.business_type IS 'Type d''activité: resale, dropshipping, artisan, retail, other';



COMMENT ON COLUMN public.users.estimated_products IS 'Nombre de produits estimé: 0-50, 50-200, 200-500, 500+';



COMMENT ON COLUMN public.users.siret IS 'Numéro SIRET (France) - uniquement pour les professionnels';



COMMENT ON COLUMN public.users.vat_number IS 'Numéro de TVA intracommunautaire - uniquement pour les professionnels';



COMMENT ON COLUMN public.users.phone IS 'Numéro de téléphone';



COMMENT ON COLUMN public.users.country IS 'Code pays ISO 3166-1 alpha-2 (FR, BE, CH, etc.)';



COMMENT ON COLUMN public.users.language IS 'Code langue ISO 639-1 (fr, en, etc.)';



COMMENT ON COLUMN public.users.subscription_tier_id IS 'FK vers subscription_quotas';



COMMENT ON COLUMN public.users.current_products_count IS 'Nombre actuel de produits actifs de l''utilisateur';



COMMENT ON COLUMN public.users.current_platforms_count IS 'Nombre actuel de plateformes connectées';



COMMENT ON COLUMN public.users.stripe_customer_id IS 'ID du customer Stripe (cus_xxx)';



COMMENT ON COLUMN public.users.stripe_subscription_id IS 'ID de la subscription Stripe active (sub_xxx)';



COMMENT ON COLUMN public.users.failed_login_attempts IS 'Nombre de tentatives de connexion échouées consécutives';



COMMENT ON COLUMN public.users.last_failed_login IS 'Date de la dernière tentative de connexion échouée';



COMMENT ON COLUMN public.users.locked_until IS 'Date jusqu''à laquelle le compte est verrouillé';



COMMENT ON COLUMN public.users.email_verified IS 'Email vérifié par l''utilisateur';



COMMENT ON COLUMN public.users.email_verification_token IS 'Token de vérification d''email';



COMMENT ON COLUMN public.users.email_verification_expires IS 'Date d''expiration du token de vérification';



COMMENT ON COLUMN public.users.password_changed_at IS 'Date du dernier changement de mot de passe';



CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;



CREATE VIEW public.vw_mapping_issues AS
 SELECT 'VINTED_NOT_MAPPED'::text AS issue_type,
    (vc.id)::text AS identifier,
    ((((vc.title)::text || ' ('::text) || (vc.gender)::text) || ')'::text) AS description
   FROM (vinted.categories vc
     LEFT JOIN vinted.mapping vm ON ((vc.id = vm.vinted_id)))
  WHERE ((vc.is_active = true) AND (vm.id IS NULL))
UNION ALL
 SELECT 'COUPLE_NOT_MAPPED'::text AS issue_type,
    (((c.name_en)::text || ' + '::text) || g.gender) AS identifier,
    ((('Aucun mapping pour '::text || (c.name_en)::text) || ' + '::text) || g.gender) AS description
   FROM (product_attributes.categories c
     CROSS JOIN ( VALUES ('men'::text), ('women'::text), ('boys'::text), ('girls'::text)) g(gender))
  WHERE ((g.gender = ANY ((c.genders)::text[])) AND (c.parent_category IS NOT NULL) AND ((c.name_en)::text <> ALL ((ARRAY['tops'::character varying, 'bottoms'::character varying, 'outerwear'::character varying, 'dresses-jumpsuits'::character varying, 'formalwear'::character varying, 'sportswear'::character varying, 'clothing'::character varying])::text[])) AND (NOT (EXISTS ( SELECT 1
           FROM vinted.mapping vm
          WHERE (((vm.my_category)::text = (c.name_en)::text) AND ((vm.my_gender)::text = g.gender))))))
UNION ALL
 SELECT 'NO_DEFAULT'::text AS issue_type,
    (((mapping.my_category)::text || ' + '::text) || (mapping.my_gender)::text) AS identifier,
    ((('Aucun défaut défini pour '::text || (mapping.my_category)::text) || ' + '::text) || (mapping.my_gender)::text) AS description
   FROM vinted.mapping
  GROUP BY mapping.my_category, mapping.my_gender
 HAVING (count(*) FILTER (WHERE (mapping.is_default = true)) = 0)
UNION ALL
 SELECT 'MULTIPLE_DEFAULTS'::text AS issue_type,
    (((mapping.my_category)::text || ' + '::text) || (mapping.my_gender)::text) AS identifier,
    (((((count(*) FILTER (WHERE (mapping.is_default = true)))::text || ' défauts pour '::text) || (mapping.my_category)::text) || ' + '::text) || (mapping.my_gender)::text) AS description
   FROM vinted.mapping
  GROUP BY mapping.my_category, mapping.my_gender
 HAVING (count(*) FILTER (WHERE (mapping.is_default = true)) > 1)
UNION ALL
 SELECT 'ORPHAN_VINTED_ID'::text AS issue_type,
    (vm.vinted_id)::text AS identifier,
    (((((('vinted_id '::text || vm.vinted_id) || ' non trouvé dans vinted_categories ('::text) || (vm.my_category)::text) || '/'::text) || (vm.my_gender)::text) || ')'::text) AS description
   FROM (vinted.mapping vm
     LEFT JOIN vinted.categories vc ON ((vm.vinted_id = vc.id)))
  WHERE (vc.id IS NULL)
UNION ALL
 SELECT 'ORPHAN_MY_CATEGORY'::text AS issue_type,
    vm.my_category AS identifier,
    (('my_category "'::text || (vm.my_category)::text) || '" non trouvé dans categories'::text) AS description
   FROM (vinted.mapping vm
     LEFT JOIN product_attributes.categories c ON (((vm.my_category)::text = (c.name_en)::text)))
  WHERE (c.name_en IS NULL)
  GROUP BY vm.my_category
UNION ALL
 SELECT 'GENDER_MISMATCH'::text AS issue_type,
    (vm.vinted_id)::text AS identifier,
    ((((('vinted_id '::text || vm.vinted_id) || ': mapping='::text) || (vm.vinted_gender)::text) || ', actual='::text) || (vc.gender)::text) AS description
   FROM (vinted.mapping vm
     JOIN vinted.categories vc ON ((vm.vinted_id = vc.id)))
  WHERE ((vm.vinted_gender)::text <> (vc.gender)::text)
UNION ALL
 SELECT 'INVALID_MY_GENDER'::text AS issue_type,
    (((vm.my_category)::text || ' + '::text) || (vm.my_gender)::text) AS identifier,
    ((((((vm.my_gender)::text || ' non autorisé pour '::text) || (vm.my_category)::text) || ' (autorisés: '::text) || array_to_string(c.genders, ', '::text)) || ')'::text) AS description
   FROM (vinted.mapping vm
     JOIN product_attributes.categories c ON (((vm.my_category)::text = (c.name_en)::text)))
  WHERE (NOT ((vm.my_gender)::text = ANY ((c.genders)::text[])));



CREATE TABLE template_tenant.ai_generation_logs (
    id integer NOT NULL,
    product_id integer NOT NULL,
    model character varying(100) NOT NULL,
    prompt_tokens integer NOT NULL,
    completion_tokens integer NOT NULL,
    total_tokens integer NOT NULL,
    total_cost numeric(10,6) NOT NULL,
    cached boolean NOT NULL,
    generation_time_ms integer NOT NULL,
    error_message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);



COMMENT ON COLUMN template_tenant.ai_generation_logs.product_id IS 'ID du produit (FK products.id)';



COMMENT ON COLUMN template_tenant.ai_generation_logs.model IS 'Modèle utilisé (gpt-4o-mini, etc.)';



COMMENT ON COLUMN template_tenant.ai_generation_logs.prompt_tokens IS 'Tokens utilisés dans le prompt';



COMMENT ON COLUMN template_tenant.ai_generation_logs.completion_tokens IS 'Tokens générés dans la réponse';



COMMENT ON COLUMN template_tenant.ai_generation_logs.total_tokens IS 'Total tokens (prompt + completion)';



COMMENT ON COLUMN template_tenant.ai_generation_logs.total_cost IS 'Coût total en $ (6 decimales)';



COMMENT ON COLUMN template_tenant.ai_generation_logs.cached IS 'Résultat depuis cache ou API';



COMMENT ON COLUMN template_tenant.ai_generation_logs.generation_time_ms IS 'Temps de génération en ms';



COMMENT ON COLUMN template_tenant.ai_generation_logs.error_message IS 'Message d''erreur si échec';



CREATE SEQUENCE template_tenant.ai_generation_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.ai_generation_logs_id_seq OWNED BY template_tenant.ai_generation_logs.id;



CREATE TABLE template_tenant.batch_jobs (
    id integer NOT NULL,
    batch_id character varying(100) NOT NULL,
    marketplace character varying(50) NOT NULL,
    action_code character varying(50) NOT NULL,
    total_count integer DEFAULT 0 NOT NULL,
    completed_count integer DEFAULT 0 NOT NULL,
    failed_count integer DEFAULT 0 NOT NULL,
    cancelled_count integer DEFAULT 0 NOT NULL,
    status template_tenant.batch_job_status DEFAULT 'pending'::template_tenant.batch_job_status NOT NULL,
    priority integer DEFAULT 3 NOT NULL,
    created_by_user_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone
);



COMMENT ON TABLE template_tenant.batch_jobs IS 'Groups multiple marketplace jobs into a single batch operation';



CREATE SEQUENCE template_tenant.batch_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.batch_jobs_id_seq OWNED BY template_tenant.batch_jobs.id;



CREATE TABLE template_tenant.ebay_credentials (
    id integer NOT NULL,
    ebay_user_id character varying(255),
    access_token text,
    refresh_token text,
    access_token_expires_at timestamp with time zone,
    refresh_token_expires_at timestamp with time zone,
    sandbox_mode boolean DEFAULT false NOT NULL,
    is_connected boolean DEFAULT false NOT NULL,
    last_sync timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    username character varying(255),
    email character varying(255),
    account_type character varying(50),
    business_name character varying(255),
    first_name character varying(255),
    last_name character varying(255),
    phone character varying(50),
    address text,
    marketplace character varying(50),
    feedback_score integer,
    feedback_percentage double precision,
    seller_level character varying(50),
    registration_date character varying(50)
);



COMMENT ON COLUMN template_tenant.ebay_credentials.ebay_user_id IS 'ID utilisateur eBay';



COMMENT ON COLUMN template_tenant.ebay_credentials.access_token IS 'OAuth2 Access Token (expire 2h)';



COMMENT ON COLUMN template_tenant.ebay_credentials.refresh_token IS 'OAuth2 Refresh Token (expire 18 mois)';



COMMENT ON COLUMN template_tenant.ebay_credentials.access_token_expires_at IS 'Date d''expiration du access_token';



COMMENT ON COLUMN template_tenant.ebay_credentials.refresh_token_expires_at IS 'Date d''expiration du refresh_token';



COMMENT ON COLUMN template_tenant.ebay_credentials.sandbox_mode IS 'True si utilise eBay Sandbox';



COMMENT ON COLUMN template_tenant.ebay_credentials.is_connected IS 'True si les credentials sont valides';



COMMENT ON COLUMN template_tenant.ebay_credentials.last_sync IS 'Dernière synchronisation réussie';



COMMENT ON COLUMN template_tenant.ebay_credentials.username IS 'Username eBay (ex: shop.ton.outfit)';



COMMENT ON COLUMN template_tenant.ebay_credentials.email IS 'Email du compte eBay';



COMMENT ON COLUMN template_tenant.ebay_credentials.account_type IS 'Type de compte: BUSINESS ou INDIVIDUAL';



COMMENT ON COLUMN template_tenant.ebay_credentials.business_name IS 'Nom de l''entreprise (si BUSINESS)';



COMMENT ON COLUMN template_tenant.ebay_credentials.first_name IS 'Prénom (si INDIVIDUAL)';



COMMENT ON COLUMN template_tenant.ebay_credentials.last_name IS 'Nom (si INDIVIDUAL)';



COMMENT ON COLUMN template_tenant.ebay_credentials.phone IS 'Numéro de téléphone';



COMMENT ON COLUMN template_tenant.ebay_credentials.address IS 'Adresse complète';



COMMENT ON COLUMN template_tenant.ebay_credentials.marketplace IS 'Marketplace d''inscription (EBAY_FR, EBAY_US, etc.)';



COMMENT ON COLUMN template_tenant.ebay_credentials.feedback_score IS 'Score de feedback';



COMMENT ON COLUMN template_tenant.ebay_credentials.feedback_percentage IS 'Pourcentage de feedback positif';



COMMENT ON COLUMN template_tenant.ebay_credentials.seller_level IS 'Niveau vendeur (top_rated, above_standard, standard, below_standard)';



COMMENT ON COLUMN template_tenant.ebay_credentials.registration_date IS 'Date d''inscription sur eBay';



CREATE SEQUENCE template_tenant.ebay_credentials_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.ebay_credentials_id_seq OWNED BY template_tenant.ebay_credentials.id;



CREATE TABLE template_tenant.ebay_orders (
    id bigint NOT NULL,
    order_id text NOT NULL,
    marketplace_id text,
    buyer_username text,
    buyer_email text,
    shipping_name text,
    shipping_address text,
    shipping_city text,
    shipping_postal_code text,
    shipping_country text,
    total_price double precision,
    currency text,
    shipping_cost double precision,
    order_fulfillment_status text,
    order_payment_status text,
    creation_date timestamp with time zone,
    paid_date timestamp with time zone,
    tracking_number text,
    shipping_carrier text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);



CREATE SEQUENCE template_tenant.ebay_orders_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.ebay_orders_id_seq OWNED BY template_tenant.ebay_orders.id;



CREATE TABLE template_tenant.ebay_orders_products (
    id bigint NOT NULL,
    order_id text NOT NULL,
    line_item_id text,
    sku text,
    sku_original text,
    title text,
    quantity integer DEFAULT 1,
    unit_price double precision,
    total_price double precision,
    currency text,
    legacy_item_id text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);



CREATE SEQUENCE template_tenant.ebay_orders_products_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.ebay_orders_products_id_seq OWNED BY template_tenant.ebay_orders_products.id;



CREATE TABLE template_tenant.ebay_products (
    id integer NOT NULL,
    ebay_sku character varying(100) NOT NULL,
    product_id integer,
    title text,
    description text,
    price numeric(10,2),
    currency character varying(3) DEFAULT 'EUR'::character varying NOT NULL,
    brand character varying(100),
    size character varying(50),
    color character varying(50),
    material character varying(100),
    category_id character varying(50),
    condition character varying(50),
    condition_description text,
    quantity integer DEFAULT 1 NOT NULL,
    availability_type character varying(50) DEFAULT 'IN_STOCK'::character varying,
    marketplace_id character varying(20) DEFAULT 'EBAY_FR'::character varying NOT NULL,
    ebay_listing_id bigint,
    ebay_offer_id bigint,
    image_urls text,
    aspects text,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    listing_format character varying(50),
    listing_duration character varying(20),
    package_weight_value numeric(10,2),
    package_weight_unit character varying(10),
    published_at timestamp with time zone,
    last_synced_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    package_length_value numeric(10,2),
    package_length_unit character varying(10),
    package_width_value numeric(10,2),
    package_width_unit character varying(10),
    package_height_value numeric(10,2),
    package_height_unit character varying(10),
    merchant_location_key character varying(50),
    secondary_category_id character varying(50),
    lot_size integer,
    quantity_limit_per_buyer integer,
    listing_description text,
    sold_quantity integer,
    available_quantity integer
);



COMMENT ON TABLE template_tenant.ebay_products IS 'Produits eBay importés depuis Inventory API';



COMMENT ON COLUMN template_tenant.ebay_products.ebay_sku IS 'SKU unique eBay (inventory item)';



COMMENT ON COLUMN template_tenant.ebay_products.product_id IS 'FK optionnelle vers Product Stoflow (1:1)';



COMMENT ON COLUMN template_tenant.ebay_products.image_urls IS 'JSON des URLs d images';



COMMENT ON COLUMN template_tenant.ebay_products.aspects IS 'JSON des aspects eBay (Brand, Color, Size, etc.)';



COMMENT ON COLUMN template_tenant.ebay_products.merchant_location_key IS 'Inventory location identifier';



COMMENT ON COLUMN template_tenant.ebay_products.secondary_category_id IS 'Secondary category if dual-listed';



COMMENT ON COLUMN template_tenant.ebay_products.lot_size IS 'Number of items in lot listing';



COMMENT ON COLUMN template_tenant.ebay_products.quantity_limit_per_buyer IS 'Max quantity per buyer';



COMMENT ON COLUMN template_tenant.ebay_products.listing_description IS 'Listing description (may differ from product)';



COMMENT ON COLUMN template_tenant.ebay_products.sold_quantity IS 'Number of units sold';



COMMENT ON COLUMN template_tenant.ebay_products.available_quantity IS 'Available quantity for purchase';



CREATE SEQUENCE template_tenant.ebay_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.ebay_products_id_seq OWNED BY template_tenant.ebay_products.id;



CREATE TABLE template_tenant.ebay_products_marketplace (
    sku_derived character varying(50) NOT NULL,
    product_id integer NOT NULL,
    marketplace_id character varying(20) NOT NULL,
    ebay_offer_id bigint,
    ebay_listing_id bigint,
    status character varying(20) DEFAULT 'draft'::character varying NOT NULL,
    error_message text,
    published_at timestamp with time zone,
    sold_at timestamp with time zone,
    last_sync_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);



CREATE TABLE template_tenant.ebay_promoted_listings (
    id integer NOT NULL,
    campaign_id character varying(50) NOT NULL,
    campaign_name character varying(255),
    marketplace_id character varying(20) NOT NULL,
    product_id integer NOT NULL,
    sku_derived character varying(50) NOT NULL,
    ad_id character varying(50) NOT NULL,
    listing_id character varying(50),
    bid_percentage numeric(5,2) NOT NULL,
    ad_status character varying(20) DEFAULT 'ACTIVE'::character varying NOT NULL,
    total_clicks integer DEFAULT 0 NOT NULL,
    total_impressions integer DEFAULT 0 NOT NULL,
    total_sales integer DEFAULT 0 NOT NULL,
    total_sales_amount numeric(10,2) DEFAULT '0'::numeric NOT NULL,
    total_ad_fees numeric(10,2) DEFAULT '0'::numeric NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);



CREATE SEQUENCE template_tenant.ebay_promoted_listings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.ebay_promoted_listings_id_seq OWNED BY template_tenant.ebay_promoted_listings.id;



CREATE TABLE template_tenant.etsy_credentials (
    id integer NOT NULL,
    access_token text,
    refresh_token text,
    access_token_expires_at timestamp with time zone,
    refresh_token_expires_at timestamp with time zone,
    shop_id character varying(255),
    shop_name character varying(255),
    shop_url character varying(500),
    user_id_etsy character varying(255),
    email character varying(255),
    is_connected boolean DEFAULT false NOT NULL,
    last_sync timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);



CREATE SEQUENCE template_tenant.etsy_credentials_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.etsy_credentials_id_seq OWNED BY template_tenant.etsy_credentials.id;



CREATE TABLE template_tenant.marketplace_jobs (
    id integer NOT NULL,
    batch_id character varying(50),
    action_type_id integer NOT NULL,
    product_id bigint,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    priority integer DEFAULT 3 NOT NULL,
    error_message text,
    retry_count integer DEFAULT 0 NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    result_data jsonb,
    marketplace character varying(50) DEFAULT 'vinted'::character varying NOT NULL,
    batch_job_id integer,
    input_data jsonb,
    max_retries integer DEFAULT 3 NOT NULL,
    idempotency_key character varying(64),
    CONSTRAINT valid_status CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'running'::character varying, 'paused'::character varying, 'completed'::character varying, 'failed'::character varying, 'cancelled'::character varying, 'expired'::character varying])::text[])))
);



COMMENT ON COLUMN template_tenant.marketplace_jobs.input_data IS 'Job input parameters';



COMMENT ON COLUMN template_tenant.marketplace_jobs.max_retries IS 'Maximum retry attempts';



COMMENT ON COLUMN template_tenant.marketplace_jobs.idempotency_key IS 'Unique key to prevent duplicate publications (format: pub_<product_id>_<uuid>)';



CREATE TABLE template_tenant.marketplace_tasks (
    id integer NOT NULL,
    task_type character varying(100),
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    payload jsonb DEFAULT '{}'::jsonb NOT NULL,
    result jsonb,
    error_message text,
    product_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    retry_count integer DEFAULT 0 NOT NULL,
    max_retries integer DEFAULT 3 NOT NULL,
    platform character varying(50),
    http_method character varying(10),
    path character varying(500),
    job_id integer,
    description character varying(500)
);



CREATE TABLE template_tenant.pending_instructions (
    id character varying(36) NOT NULL,
    user_id integer NOT NULL,
    action character varying(100) NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    result jsonb,
    error text,
    created_at timestamp with time zone NOT NULL,
    completed_at timestamp with time zone,
    expires_at timestamp with time zone
);



CREATE SEQUENCE template_tenant.plugin_tasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.plugin_tasks_id_seq OWNED BY template_tenant.marketplace_tasks.id;



CREATE TABLE template_tenant.product_colors (
    product_id integer NOT NULL,
    color character varying(100) NOT NULL,
    is_primary boolean DEFAULT false NOT NULL
);



CREATE TABLE template_tenant.product_condition_sups (
    product_id integer NOT NULL,
    condition_sup character varying(100) NOT NULL
);



CREATE TABLE template_tenant.product_images (
    id integer NOT NULL,
    product_id integer NOT NULL,
    image_path character varying(1000) NOT NULL,
    display_order integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);



COMMENT ON COLUMN template_tenant.product_images.product_id IS 'ID du produit (FK products.id, cascade delete)';



COMMENT ON COLUMN template_tenant.product_images.image_path IS 'Chemin relatif de l''image';



COMMENT ON COLUMN template_tenant.product_images.display_order IS 'Ordre d''affichage (0 = première)';



CREATE SEQUENCE template_tenant.product_images_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.product_images_id_seq OWNED BY template_tenant.product_images.id;



CREATE TABLE template_tenant.product_materials (
    product_id integer NOT NULL,
    material character varying(100) NOT NULL,
    percentage integer,
    CONSTRAINT product_materials_percentage_check CHECK (((percentage >= 0) AND (percentage <= 100)))
);



CREATE TABLE template_tenant.products (
    id integer NOT NULL,
    sku character varying(100),
    title character varying(500) NOT NULL,
    description text NOT NULL,
    price numeric(10,2) NOT NULL,
    category character varying(255) NOT NULL,
    brand character varying(100),
    size_original character varying(100),
    fit character varying(100),
    gender character varying(100),
    season character varying(100),
    rise character varying(100),
    closure character varying(100),
    sleeve_length character varying(100),
    origin character varying(100),
    decade character varying(100),
    trend character varying(100),
    location character varying(100),
    model character varying(100),
    dim1 integer,
    dim2 integer,
    dim3 integer,
    dim4 integer,
    dim5 integer,
    dim6 integer,
    stock_quantity integer NOT NULL,
    images text,
    status public.product_status NOT NULL,
    scheduled_publish_at timestamp with time zone,
    published_at timestamp with time zone,
    sold_at timestamp with time zone,
    deleted_at timestamp with time zone,
    integration_metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    pricing_edit character varying(100),
    pricing_rarity character varying(100),
    pricing_quality character varying(100),
    pricing_details character varying(100),
    pricing_style character varying(100),
    marking text,
    sport character varying(100),
    neckline character varying(100),
    length character varying(100),
    pattern character varying(100),
    condition integer,
    size_normalized character varying(100),
    unique_feature jsonb,
    stretch character varying(100),
    version_number integer DEFAULT 1 NOT NULL,
    CONSTRAINT check_stock_positive CHECK ((stock_quantity >= 0))
);



COMMENT ON COLUMN template_tenant.products.sku IS 'SKU du produit';



COMMENT ON COLUMN template_tenant.products.title IS 'Titre du produit';



COMMENT ON COLUMN template_tenant.products.description IS 'Description complète';



COMMENT ON COLUMN template_tenant.products.price IS 'Prix de vente';



COMMENT ON COLUMN template_tenant.products.category IS 'Catégorie (FK product_attributes.categories.name_en)';



COMMENT ON COLUMN template_tenant.products.brand IS 'Marque (FK product_attributes.brands.name)';



COMMENT ON COLUMN template_tenant.products.size_original IS 'Taille étiquette (FK product_attributes.sizes.name_en)';



COMMENT ON COLUMN template_tenant.products.fit IS 'Coupe (FK product_attributes.fits.name_en)';



COMMENT ON COLUMN template_tenant.products.gender IS 'Genre (FK product_attributes.genders.name_en)';



COMMENT ON COLUMN template_tenant.products.season IS 'Saison (FK product_attributes.seasons.name_en)';



COMMENT ON COLUMN template_tenant.products.rise IS 'Hauteur de taille (pantalons)';



COMMENT ON COLUMN template_tenant.products.closure IS 'Type de fermeture';



COMMENT ON COLUMN template_tenant.products.sleeve_length IS 'Longueur de manche';



COMMENT ON COLUMN template_tenant.products.origin IS 'Origine/provenance';



COMMENT ON COLUMN template_tenant.products.decade IS 'Décennie (vintage)';



COMMENT ON COLUMN template_tenant.products.trend IS 'Tendance';



COMMENT ON COLUMN template_tenant.products.location IS 'Localisation';



COMMENT ON COLUMN template_tenant.products.model IS 'Modèle';



COMMENT ON COLUMN template_tenant.products.dim1 IS 'Dimension 1 (cm)';



COMMENT ON COLUMN template_tenant.products.dim2 IS 'Dimension 2 (cm)';



COMMENT ON COLUMN template_tenant.products.dim3 IS 'Dimension 3 (cm)';



COMMENT ON COLUMN template_tenant.products.dim4 IS 'Dimension 4 (cm)';



COMMENT ON COLUMN template_tenant.products.dim5 IS 'Dimension 5 (cm)';



COMMENT ON COLUMN template_tenant.products.dim6 IS 'Dimension 6 (cm)';



COMMENT ON COLUMN template_tenant.products.images IS 'Images URLs (JSON array)';



COMMENT ON COLUMN template_tenant.products.pricing_edit IS 'Édition limitée/exclusive';



COMMENT ON COLUMN template_tenant.products.pricing_rarity IS 'Rareté du produit';



COMMENT ON COLUMN template_tenant.products.pricing_quality IS 'Qualité exceptionnelle';



COMMENT ON COLUMN template_tenant.products.pricing_details IS 'Détails valorisants';



COMMENT ON COLUMN template_tenant.products.pricing_style IS 'Style iconique';



COMMENT ON COLUMN template_tenant.products.marking IS 'Marquages/logos';



COMMENT ON COLUMN template_tenant.products.sport IS 'Sport (FK product_attributes.sports)';



COMMENT ON COLUMN template_tenant.products.neckline IS 'Encolure (FK product_attributes.necklines)';



COMMENT ON COLUMN template_tenant.products.length IS 'Longueur (FK product_attributes.lengths)';



COMMENT ON COLUMN template_tenant.products.pattern IS 'Motif (FK product_attributes.patterns)';



CREATE SEQUENCE template_tenant.products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.products_id_seq OWNED BY template_tenant.products.id;



CREATE TABLE template_tenant.publication_history (
    id integer NOT NULL,
    product_id integer NOT NULL,
    status public.publication_status NOT NULL,
    platform_product_id character varying(100),
    error_message text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);



COMMENT ON COLUMN template_tenant.publication_history.product_id IS 'ID du produit (FK products.id)';



COMMENT ON COLUMN template_tenant.publication_history.status IS 'Statut de la publication';



COMMENT ON COLUMN template_tenant.publication_history.platform_product_id IS 'ID du produit sur la plateforme';



COMMENT ON COLUMN template_tenant.publication_history.error_message IS 'Message d''erreur si échec';



COMMENT ON COLUMN template_tenant.publication_history.metadata IS 'Métadonnées supplémentaires';



CREATE SEQUENCE template_tenant.publication_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.publication_history_id_seq OWNED BY template_tenant.publication_history.id;



CREATE TABLE template_tenant.vinted_connection (
    vinted_user_id integer NOT NULL,
    login character varying(255) NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    last_sync timestamp with time zone DEFAULT now() NOT NULL,
    is_connected boolean DEFAULT true NOT NULL,
    disconnected_at timestamp with time zone,
    last_datadome_ping timestamp with time zone,
    datadome_status public.datadomestatus DEFAULT 'UNKNOWN'::public.datadomestatus NOT NULL,
    item_count integer,
    total_items_count integer,
    given_item_count integer,
    taken_item_count integer,
    followers_count integer,
    feedback_count integer,
    feedback_reputation double precision,
    positive_feedback_count integer,
    negative_feedback_count integer,
    is_business boolean,
    is_on_holiday boolean,
    stats_updated_at timestamp with time zone
);



COMMENT ON COLUMN template_tenant.vinted_connection.vinted_user_id IS 'ID utilisateur Vinted (PK)';



COMMENT ON COLUMN template_tenant.vinted_connection.login IS 'Login/username Vinted';



COMMENT ON COLUMN template_tenant.vinted_connection.user_id IS 'FK vers public.users.id';



CREATE SEQUENCE template_tenant.vinted_connection_vinted_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.vinted_connection_vinted_user_id_seq OWNED BY template_tenant.vinted_connection.vinted_user_id;



CREATE TABLE template_tenant.vinted_conversations (
    conversation_id bigint NOT NULL,
    opposite_user_id bigint,
    opposite_user_login character varying(255),
    opposite_user_photo_url text,
    last_message_preview text,
    is_unread boolean DEFAULT false NOT NULL,
    unread_count integer DEFAULT 0 NOT NULL,
    item_count integer DEFAULT 1 NOT NULL,
    item_id bigint,
    item_title character varying(255),
    item_photo_url text,
    transaction_id bigint,
    updated_at_vinted timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_synced_at timestamp with time zone
);



COMMENT ON COLUMN template_tenant.vinted_conversations.conversation_id IS 'Vinted conversation ID (PK)';



COMMENT ON COLUMN template_tenant.vinted_conversations.opposite_user_id IS 'Other participant Vinted ID';



COMMENT ON COLUMN template_tenant.vinted_conversations.opposite_user_login IS 'Other participant username';



COMMENT ON COLUMN template_tenant.vinted_conversations.opposite_user_photo_url IS 'Other participant avatar URL';



COMMENT ON COLUMN template_tenant.vinted_conversations.last_message_preview IS 'Preview of last message';



COMMENT ON COLUMN template_tenant.vinted_conversations.is_unread IS 'Has unread messages';



COMMENT ON COLUMN template_tenant.vinted_conversations.unread_count IS 'Number of unread messages';



COMMENT ON COLUMN template_tenant.vinted_conversations.item_count IS 'Number of items in conversation';



COMMENT ON COLUMN template_tenant.vinted_conversations.item_id IS 'Main item Vinted ID';



COMMENT ON COLUMN template_tenant.vinted_conversations.item_title IS 'Main item title';



COMMENT ON COLUMN template_tenant.vinted_conversations.item_photo_url IS 'Main item photo URL';



COMMENT ON COLUMN template_tenant.vinted_conversations.transaction_id IS 'Linked transaction ID';



COMMENT ON COLUMN template_tenant.vinted_conversations.updated_at_vinted IS 'Last update on Vinted';



COMMENT ON COLUMN template_tenant.vinted_conversations.created_at IS 'Local creation date';



COMMENT ON COLUMN template_tenant.vinted_conversations.updated_at IS 'Local update date';



COMMENT ON COLUMN template_tenant.vinted_conversations.last_synced_at IS 'Last sync with Vinted';



CREATE SEQUENCE template_tenant.vinted_conversations_conversation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.vinted_conversations_conversation_id_seq OWNED BY template_tenant.vinted_conversations.conversation_id;



CREATE TABLE template_tenant.vinted_error_logs (
    id integer NOT NULL,
    product_id integer NOT NULL,
    operation character varying(20) NOT NULL,
    error_type character varying(50) NOT NULL,
    error_message text NOT NULL,
    error_details text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);



COMMENT ON COLUMN template_tenant.vinted_error_logs.operation IS 'Type d''opération: publish, update, delete';



COMMENT ON COLUMN template_tenant.vinted_error_logs.error_type IS 'Type d''erreur: mapping_error, api_error, image_error, validation_error';



COMMENT ON COLUMN template_tenant.vinted_error_logs.error_message IS 'Message d''erreur principal';



COMMENT ON COLUMN template_tenant.vinted_error_logs.error_details IS 'Détails supplémentaires (JSON, traceback, etc.)';



CREATE SEQUENCE template_tenant.vinted_error_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.vinted_error_logs_id_seq OWNED BY template_tenant.vinted_error_logs.id;



CREATE TABLE template_tenant.vinted_job_stats (
    id integer NOT NULL,
    action_type_id integer NOT NULL,
    date date NOT NULL,
    total_jobs integer DEFAULT 0 NOT NULL,
    success_count integer DEFAULT 0 NOT NULL,
    failure_count integer DEFAULT 0 NOT NULL,
    avg_duration_ms integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);



CREATE SEQUENCE template_tenant.vinted_job_stats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.vinted_job_stats_id_seq OWNED BY template_tenant.vinted_job_stats.id;



CREATE SEQUENCE template_tenant.vinted_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.vinted_jobs_id_seq OWNED BY template_tenant.marketplace_jobs.id;



CREATE TABLE template_tenant.vinted_messages (
    id integer NOT NULL,
    conversation_id bigint NOT NULL,
    vinted_message_id bigint,
    entity_type character varying(50) DEFAULT 'message'::character varying NOT NULL,
    sender_id bigint,
    sender_login character varying(255),
    body text,
    title text,
    subtitle text,
    offer_price character varying(20),
    offer_status character varying(100),
    is_from_current_user boolean DEFAULT false NOT NULL,
    created_at_vinted timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);



COMMENT ON COLUMN template_tenant.vinted_messages.conversation_id IS 'FK to vinted_conversations';



COMMENT ON COLUMN template_tenant.vinted_messages.vinted_message_id IS 'Vinted message ID';



COMMENT ON COLUMN template_tenant.vinted_messages.entity_type IS 'message, offer_request_message, status_message, action_message';



COMMENT ON COLUMN template_tenant.vinted_messages.sender_id IS 'Sender Vinted ID';



COMMENT ON COLUMN template_tenant.vinted_messages.sender_login IS 'Sender username';



COMMENT ON COLUMN template_tenant.vinted_messages.body IS 'Message text content';



COMMENT ON COLUMN template_tenant.vinted_messages.title IS 'Title for status/action messages';



COMMENT ON COLUMN template_tenant.vinted_messages.subtitle IS 'Subtitle for status/action messages';



COMMENT ON COLUMN template_tenant.vinted_messages.offer_price IS 'Offer price (e.g., 8.0)';



COMMENT ON COLUMN template_tenant.vinted_messages.offer_status IS 'Offer status title';



COMMENT ON COLUMN template_tenant.vinted_messages.is_from_current_user IS 'Sent by current user';



COMMENT ON COLUMN template_tenant.vinted_messages.created_at_vinted IS 'Creation time on Vinted';



CREATE SEQUENCE template_tenant.vinted_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE template_tenant.vinted_messages_id_seq OWNED BY template_tenant.vinted_messages.id;



CREATE TABLE template_tenant.vinted_products (
    vinted_id bigint NOT NULL,
    title text,
    description text,
    price numeric(10,2),
    currency character varying(3) DEFAULT 'EUR'::character varying NOT NULL,
    brand character varying(100),
    size character varying(50),
    color character varying(50),
    category character varying(200),
    status character varying(20) DEFAULT 'published'::character varying NOT NULL,
    condition character varying(50),
    is_draft boolean DEFAULT false NOT NULL,
    is_closed boolean DEFAULT false NOT NULL,
    view_count integer DEFAULT 0 NOT NULL,
    favourite_count integer DEFAULT 0 NOT NULL,
    url text,
    photos_data text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    total_price numeric(10,2),
    brand_id integer,
    size_id integer,
    catalog_id integer,
    condition_id integer,
    material character varying(100),
    measurements character varying(100),
    measurement_width integer,
    measurement_length integer,
    manufacturer_labelling text,
    is_reserved boolean DEFAULT false NOT NULL,
    is_hidden boolean DEFAULT false NOT NULL,
    seller_id bigint,
    seller_login character varying(100),
    service_fee numeric(10,2),
    buyer_protection_fee numeric(10,2),
    shipping_price numeric(10,2),
    published_at timestamp with time zone,
    product_id integer,
    color1_id integer,
    color2_id integer,
    color2 character varying(50) DEFAULT NULL::character varying,
    status_id integer,
    is_unisex boolean DEFAULT false,
    measurement_unit character varying(20) DEFAULT NULL::character varying,
    item_attributes jsonb
);



COMMENT ON TABLE template_tenant.vinted_products IS 'Produits Vinted (standalone, pas de FK vers products)';



COMMENT ON COLUMN template_tenant.vinted_products.vinted_id IS 'ID unique Vinted';



COMMENT ON COLUMN template_tenant.vinted_products.photos_data IS 'JSON des photos [{id, url, ...}]';



COMMENT ON COLUMN template_tenant.vinted_products.total_price IS 'Prix total avec frais';



COMMENT ON COLUMN template_tenant.vinted_products.brand_id IS 'ID Vinted de la marque';



COMMENT ON COLUMN template_tenant.vinted_products.size_id IS 'ID Vinted de la taille';



COMMENT ON COLUMN template_tenant.vinted_products.catalog_id IS 'ID Vinted de la catégorie';



COMMENT ON COLUMN template_tenant.vinted_products.condition_id IS 'ID Vinted de létat';



COMMENT ON COLUMN template_tenant.vinted_products.material IS 'Matière';



COMMENT ON COLUMN template_tenant.vinted_products.measurements IS 'Dimensions texte (l X cm / L Y cm)';



COMMENT ON COLUMN template_tenant.vinted_products.measurement_width IS 'Largeur en cm';



COMMENT ON COLUMN template_tenant.vinted_products.measurement_length IS 'Longueur en cm';



COMMENT ON COLUMN template_tenant.vinted_products.manufacturer_labelling IS 'Étiquetage du fabricant';



COMMENT ON COLUMN template_tenant.vinted_products.is_reserved IS 'Est réservé';



COMMENT ON COLUMN template_tenant.vinted_products.is_hidden IS 'Est masqué';



COMMENT ON COLUMN template_tenant.vinted_products.seller_id IS 'ID vendeur Vinted';



COMMENT ON COLUMN template_tenant.vinted_products.seller_login IS 'Login vendeur';



COMMENT ON COLUMN template_tenant.vinted_products.service_fee IS 'Frais de service';



COMMENT ON COLUMN template_tenant.vinted_products.buyer_protection_fee IS 'Frais protection acheteur';



COMMENT ON COLUMN template_tenant.vinted_products.shipping_price IS 'Frais de port';



COMMENT ON COLUMN template_tenant.vinted_products.published_at IS 'Date de publication sur Vinted (from image timestamp)';



ALTER TABLE ONLY public.admin_audit_logs ALTER COLUMN id SET DEFAULT nextval('public.admin_audit_logs_id_seq'::regclass);



ALTER TABLE ONLY public.ai_credits ALTER COLUMN id SET DEFAULT nextval('public.ai_credits_id_seq'::regclass);



ALTER TABLE ONLY public.doc_articles ALTER COLUMN id SET DEFAULT nextval('public.doc_articles_id_seq'::regclass);



ALTER TABLE ONLY public.doc_categories ALTER COLUMN id SET DEFAULT nextval('public.doc_categories_id_seq'::regclass);



ALTER TABLE ONLY public.migration_errors ALTER COLUMN id SET DEFAULT nextval('public.migration_errors_id_seq'::regclass);



ALTER TABLE ONLY public.permissions ALTER COLUMN id SET DEFAULT nextval('public.permissions_id_seq'::regclass);



ALTER TABLE ONLY public.role_permissions ALTER COLUMN id SET DEFAULT nextval('public.role_permissions_id_seq'::regclass);



ALTER TABLE ONLY public.subscription_features ALTER COLUMN id SET DEFAULT nextval('public.subscription_features_id_seq'::regclass);



ALTER TABLE ONLY public.subscription_quotas ALTER COLUMN id SET DEFAULT nextval('public.subscription_quotas_id_seq'::regclass);



ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.ai_generation_logs ALTER COLUMN id SET DEFAULT nextval('template_tenant.ai_generation_logs_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.batch_jobs ALTER COLUMN id SET DEFAULT nextval('template_tenant.batch_jobs_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.ebay_credentials ALTER COLUMN id SET DEFAULT nextval('template_tenant.ebay_credentials_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.ebay_orders ALTER COLUMN id SET DEFAULT nextval('template_tenant.ebay_orders_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.ebay_orders_products ALTER COLUMN id SET DEFAULT nextval('template_tenant.ebay_orders_products_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.ebay_products ALTER COLUMN id SET DEFAULT nextval('template_tenant.ebay_products_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.ebay_promoted_listings ALTER COLUMN id SET DEFAULT nextval('template_tenant.ebay_promoted_listings_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.etsy_credentials ALTER COLUMN id SET DEFAULT nextval('template_tenant.etsy_credentials_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.marketplace_jobs ALTER COLUMN id SET DEFAULT nextval('template_tenant.vinted_jobs_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.marketplace_tasks ALTER COLUMN id SET DEFAULT nextval('template_tenant.plugin_tasks_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.product_images ALTER COLUMN id SET DEFAULT nextval('template_tenant.product_images_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.products ALTER COLUMN id SET DEFAULT nextval('template_tenant.products_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.publication_history ALTER COLUMN id SET DEFAULT nextval('template_tenant.publication_history_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.vinted_connection ALTER COLUMN vinted_user_id SET DEFAULT nextval('template_tenant.vinted_connection_vinted_user_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.vinted_conversations ALTER COLUMN conversation_id SET DEFAULT nextval('template_tenant.vinted_conversations_conversation_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.vinted_error_logs ALTER COLUMN id SET DEFAULT nextval('template_tenant.vinted_error_logs_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.vinted_job_stats ALTER COLUMN id SET DEFAULT nextval('template_tenant.vinted_job_stats_id_seq'::regclass);



ALTER TABLE ONLY template_tenant.vinted_messages ALTER COLUMN id SET DEFAULT nextval('template_tenant.vinted_messages_id_seq'::regclass);



COPY product_attributes.brands (name, description, vinted_id, monitoring, sector_jeans, sector_jacket) FROM stdin;
Zara	\N	\N	f	\N	\N
H&M	\N	\N	f	\N	\N
Uniqlo	\N	\N	f	\N	\N
esprit	\N	\N	f	\N	\N
pure oxygen	\N	\N	f	\N	\N
wonderful	\N	\N	f	\N	\N
2pac	\N	\N	f	\N	\N
aem'kei nyc	\N	\N	f	\N	\N
arm jeans	\N	\N	f	\N	\N
bastard	\N	\N	f	\N	\N
baz 40	\N	\N	f	\N	\N
blueskin	\N	\N	f	\N	\N
champion	\N	\N	f	\N	\N
chaps	\N	\N	f	\N	\N
citizens of humanity	\N	\N	f	\N	\N
denime	\N	\N	f	\N	\N
frame	\N	\N	f	\N	\N
freeman	\N	\N	f	\N	\N
hawk	\N	\N	f	\N	\N
hugo boss	\N	\N	f	\N	\N
izac	\N	\N	f	\N	\N
keegan	\N	\N	f	\N	\N
kolapso	\N	\N	f	\N	\N
left field nyc	\N	\N	f	\N	\N
napapijri	\N	\N	f	\N	\N
nylaus	\N	\N	f	\N	\N
outback	\N	\N	f	\N	\N
pepe jeans	\N	\N	f	\N	\N
rag & bone	\N	\N	f	\N	\N
reebok	\N	\N	f	\N	\N
reell	\N	\N	f	\N	\N
roy jeans	\N	\N	f	\N	\N
sohk	\N	\N	f	\N	\N
tela genova	\N	\N	f	\N	\N
victorinox	\N	\N	f	\N	\N
Adidas	\N	14	f	\N	\N
Nike	\N	53	f	\N	\N
a.p.c.	\N	251	f	\N	\N
acronym	\N	712647	f	\N	\N
adidas	\N	14	f	\N	\N
affliction	\N	272035	f	\N	\N
akademiks	\N	130046	f	\N	\N
and wander	\N	1512834	f	\N	\N
arc'teryx	\N	319730	f	\N	\N
auralee	\N	2053426	f	\N	\N
avirex	\N	4565	f	\N	\N
battenwear	\N	1102097	f	\N	\N
ben davis	\N	85872	f	\N	\N
bershka	\N	140	f	\N	\N
blind	\N	56158	f	\N	\N
brixton	\N	56682	f	\N	\N
bugle boy	\N	306806	f	\N	\N
burberrys	\N	364	f	\N	\N
calvin klein	\N	255	f	\N	\N
carhartt	\N	362	f	\N	\N
celio	\N	2615	f	\N	\N
chevignon	\N	12205	f	\N	\N
coogi	\N	21359	f	\N	\N
crooks & castles	\N	48527	f	\N	\N
denham	\N	102502	f	\N	\N
dickies	\N	65	f	\N	\N
diesel	\N	161	f	\N	\N
dime	\N	326479	f	\N	\N
dynam	\N	24329	f	\N	\N
ecko unltd	\N	30575	f	\N	\N
ed hardy	\N	1761	f	\N	\N
edwin	\N	4471	f	\N	\N
element	\N	2037	f	\N	\N
energie	\N	15985	f	\N	\N
engineered garments	\N	609050	f	\N	\N
enyce	\N	76428	f	\N	\N
foot korner	\N	381270	f	\N	\N
freenote cloth	\N	2125308	f	\N	\N
fubu	\N	57822	f	\N	\N
g-star raw	\N	2782756	f	\N	\N
g-unit	\N	42813	f	\N	\N
gant jeans	\N	6075	f	\N	\N
gap	\N	6	f	\N	\N
gramicci	\N	896209	f	\N	\N
guess	\N	20	f	\N	\N
heron preston	\N	389625	f	\N	\N
houdini	\N	379143	f	\N	\N
huf	\N	14185	f	\N	\N
indigofera	\N	742615	f	\N	\N
iron heart	\N	492896	f	\N	\N
jackwolfskin	\N	147650	f	\N	\N
japan blue	\N	451051	f	\N	\N
jizo	\N	10037867	f	\N	\N
kangaroo poo	\N	779366	f	\N	\N
kapital	\N	576107	f	\N	\N
karl kani	\N	13989	f	\N	\N
kiko kostadinov	\N	5821136	f	\N	\N
klättermusen	\N	1638071	f	\N	\N
lacoste	\N	304	f	\N	\N
lagerfeld	\N	103	f	\N	\N
lee	\N	63	f	\N	\N
lemaire	\N	295938	f	\N	\N
levi's	\N	10	f	\N	\N
levi's made & crafted	\N	5982593	f	\N	\N
maharishi	\N	326054	f	\N	\N
maison mihara yasuhiro	\N	2514944	f	\N	\N
majestic	\N	5725	f	\N	\N
marni	\N	12251	f	\N	\N
mecca	\N	238862	f	\N	\N
mlb	\N	77420	f	\N	\N
mont bell	\N	15088880	f	\N	\N
montbell	\N	615130	f	\N	\N
nascar	\N	185574	f	\N	\N
neighborhood	\N	330747	f	\N	\N
nfl	\N	33275	f	\N	\N
nigel cabourn	\N	696416	f	\N	\N
nike	\N	53	f	\N	\N
no fear	\N	26101	f	\N	\N
nudie jeans	\N	95256	f	\N	\N
obey	\N	2069	f	\N	\N
oni arai	\N	17653347	f	\N	\N
orslow	\N	373463	f	\N	\N
palace	\N	139960	f	\N	\N
pass port	\N	15497435	f	\N	\N
passport	\N	27217	f	\N	\N
phat farm	\N	207738	f	\N	\N
poetic collective	\N	924571	f	\N	\N
pointer	\N	27275	f	\N	\N
polar skate	\N	375147	f	\N	\N
pop trading company	\N	906755	f	\N	\N
puma	\N	535	f	\N	\N
pure blue japan	\N	859861	f	\N	\N
ralph lauren	\N	88	f	\N	\N
rare humans	\N	5582686	f	\N	\N
rica lewis	\N	506	f	\N	\N
robin's jean	\N	129064	f	\N	\N
rocawear	\N	29507	f	\N	\N
rogue territory	\N	770322	f	\N	\N
résolute	\N	862485	f	\N	\N
3sixteen	\N	623847	f	\N	\N
acne studios	\N	180798	f	\N	\N
anchor blue	\N	44519	f	\N	\N
bape	\N	4691320	f	\N	\N
big train	\N	2496245	f	\N	\N
butter goods	\N	901821	f	\N	\N
corteiz	\N	3036449	f	\N	\N
divided	\N	15452320	f	\N	\N
ecko unltd.	\N	30575	f	\N	\N
evisu	\N	214088	f	\N	\N
full count	\N	2890372	f	\N	\N
goldwin	\N	330213	f	\N	\N
homecore	\N	209540	f	\N	\N
izod	\N	238478	f	\N	\N
jnco	\N	290909	f	\N	\N
kiabi	\N	60	f	\N	\N
lee cooper	\N	407	f	\N	\N
levi's vintage clothing	\N	5983207	f	\N	\N
momotaro	\N	358913	f	\N	\N
naked & famous denim	\N	1148437	f	\N	\N
norrøna	\N	356632	f	\N	\N
our legacy	\N	218132	f	\N	\N
pelle pelle	\N	6989	f	\N	\N
polar skate co.	\N	7006283	f	\N	\N
red pepper	\N	717159	f	\N	\N
samurai	\N	278324	f	\N	\N
sean john	\N	56628	f	\N	\N
service works	\N	3364686	f	\N	\N
snow peak	\N	666350	f	\N	\N
south pole	\N	12235	f	\N	\N
southpole	\N	12235	f	\N	\N
stan ray	\N	449441	f	\N	\N
starter	\N	28365	f	\N	\N
state property	\N	335771	f	\N	\N
studio d'artisan	\N	458183	f	\N	\N
stuka	\N	288610	f	\N	\N
stüssy	\N	441	f	\N	\N
sugar cane	\N	178936	f	\N	\N
sunnei	\N	834075	f	\N	\N
supreme	\N	14969	f	\N	\N
tcb jeans	\N	1945864	f	\N	\N
tellason	\N	379872	f	\N	\N
the flat head	\N	2182295	f	\N	\N
the north face	\N	2319	f	\N	\N
timberland	\N	44	f	\N	\N
tommy hilfiger	\N	94	f	\N	\N
tribal	\N	126096	f	\N	\N
true religion	\N	9075	f	\N	\N
unbranded	\N	14803	f	\N	\N
under armour	\N	52035	f	\N	\N
universal works	\N	378695	f	\N	\N
vans	\N	139	f	\N	\N
veilance	\N	3388210	f	\N	\N
vokal	\N	300441	f	\N	\N
volcom	\N	66	f	\N	\N
warehouse	\N	7441	f	\N	\N
wrangler	\N	259	f	\N	\N
wrung	\N	6937	f	\N	\N
wtaps	\N	320615	f	\N	\N
wu-wear	\N	334532	f	\N	\N
yardsale	\N	273608	f	\N	\N
zoo york	\N	10401	f	\N	\N
\.



COPY product_attributes.categories (name_en, parent_category, name_fr, name_de, name_it, name_es, name_nl, name_pl, genders) FROM stdin;
other	\N	Autre	Sonstiges	Altro	Otro	Overig	Inne	\N
body suit	tops	Body	Body	Body	Body	Body	Body	{women}
fleece jacket	tops	Polaire	Fleecejacke	Giacca in pile	Chaqueta polar	Fleecevest	Bluza polarowa	{men,women,boys,girls}
clothing	\N	Vêtements	Kleidung	Abbigliamento	Ropa	Kleding	Odzież	{men,women,boys,girls}
tops	clothing	Hauts	Oberteile	Top	Tops	Tops	Góry	{men,women,boys,girls}
t-shirt	tops	T-shirt	T-Shirt	T-shirt	Camiseta	T-shirt	T-shirt	{men,women,boys,girls}
tank-top	tops	Débardeur	Tanktop	Canotta	Camiseta de tirantes	Tanktop	Top na ramiączkach	{men,women,boys,girls}
shirt	tops	Chemise	Hemd	Camicia	Camisa	Overhemd	Koszula	{men,women,boys,girls}
blouse	tops	Blouse	Bluse	Blusa	Blusa	Blouse	Bluzka	{women,girls}
top	tops	Top	Top	Top	Top	Top	Top	{women,girls}
corset	tops	Corset	Korsett	Corsetto	Corsé	Korset	Gorset	{women}
bustier	tops	Bustier	Bustier	Bustier	Bustier	Bustier	Bustier	{women}
camisole	tops	Caraco	Unterhemd	Canottiera	Camisola	Hemdje	Koszulka na ramiączkach	{women}
crop-top	tops	Crop top	Crop-Top	Crop top	Crop top	Crop top	Crop top	{women,girls}
polo	tops	Polo	Polo	Polo	Polo	Polo	Polo	{men,women,boys,girls}
sweater	tops	Pull	Pullover	Maglione	Jersey	Trui	Sweter	{men,women,boys,girls}
cardigan	tops	Cardigan	Cardigan	Cardigan	Cárdigan	Vest	Kardigan	{men,women,boys,girls}
sweatshirt	tops	Sweat	Sweatshirt	Felpa	Sudadera	Sweater	Bluza	{men,women,boys,girls}
hoodie	tops	Hoodie	Hoodie	Felpa con cappuccio	Sudadera con capucha	Hoodie	Bluza z kapturem	{men,women,boys,girls}
overshirt	tops	Surchemise	Überhemd	Sovracamicia	Sobrecamisa	Overshirt	Koszula wierzchnia	{men,women}
bottoms	clothing	Bas	Unterteile	Pantaloni	Partes de abajo	Broeken	Doły	{men,women,boys,girls}
pants	bottoms	Pantalon	Hose	Pantaloni	Pantalones	Broek	Spodnie	{men,women,boys,girls}
jeans	bottoms	Jean	Jeans	Jeans	Vaqueros	Jeans	Jeansy	{men,women,boys,girls}
chinos	bottoms	Chino	Chinos	Chinos	Chinos	Chino	Chinosy	{men,women,boys,girls}
joggers	bottoms	Jogging	Jogginghose	Pantaloni sportivi	Pantalones jogger	Joggingbroek	Spodnie dresowe	{men,women,boys,girls}
cargo-pants	bottoms	Pantalon cargo	Cargohose	Pantaloni cargo	Pantalones cargo	Cargobroek	Spodnie cargo	{men,women,boys,girls}
dress-pants	bottoms	Pantalon habillé	Stoffhose	Pantaloni eleganti	Pantalones de vestir	Nette broek	Spodnie wizytowe	{men,women,boys,girls}
shorts	bottoms	Short	Shorts	Shorts	Pantalones cortos	Shorts	Szorty	{men,women,boys,girls}
bermuda	bottoms	Bermuda	Bermuda	Bermuda	Bermudas	Bermuda	Bermudy	{men,women,boys,girls}
skirt	bottoms	Jupe	Rock	Gonna	Falda	Rok	Spódnica	{women,girls}
leggings	bottoms	Legging	Leggings	Leggings	Leggings	Legging	Legginsy	{women,girls,boys}
culottes	bottoms	Jupe-culotte	Hosenrock	Gonna pantalone	Falda pantalón	Culotte	Spódnico-spodnie	{women,girls}
outerwear	clothing	Vêtements d'extérieur	Oberbekleidung	Capispalla	Ropa de abrigo	Bovenkleding	Odzież wierzchnia	{men,women,boys,girls}
jacket	outerwear	Veste	Jacke	Giacca	Chaqueta	Jas	Kurtka	{men,women,boys,girls}
bomber	outerwear	Blouson	Bomberjacke	Bomber	Bomber	Bomberjas	Bomber	{men,women,boys,girls}
puffer	outerwear	Doudoune	Pufferjacke	Piumino	Abrigo acolchado	Pufferjack	Kurtka puchowa	{men,women,boys,girls}
coat	outerwear	Manteau	Mantel	Cappotto	Abrigo	Jas	Płaszcz	{men,women,boys,girls}
trench	outerwear	Trench	Trenchcoat	Trench	Gabardina	Trenchcoat	Trencz	{men,women,boys,girls}
parka	outerwear	Parka	Parka	Parka	Parka	Parka	Parka	{men,women,boys,girls}
raincoat	outerwear	Imperméable	Regenmantel	Impermeabile	Impermeable	Regenjas	Płaszcz przeciwdeszczowy	{men,women,boys,girls}
windbreaker	outerwear	Coupe-vent	Windbreaker	Giacca a vento	Cortavientos	Windbreaker	Wiatrówka	{men,women,boys,girls}
blazer	outerwear	Blazer	Blazer	Blazer	Blazer	Blazer	Blezer	{men,women,boys,girls}
vest	outerwear	Gilet	Weste	Gilet	Chaleco	Bodywarmer	Kamizelka	{men,women,boys,girls}
half-zip	outerwear	Demi-zip	Halfzip	Mezza zip	Media cremallera	Halfzip	Półzamek	{men,women,boys,girls}
cape	outerwear	Cape	Cape	Mantella	Capa	Cape	Peleryna	{women,girls}
poncho	outerwear	Poncho	Poncho	Poncho	Poncho	Poncho	Ponczo	{men,women,boys,girls}
kimono	outerwear	Kimono	Kimono	Kimono	Kimono	Kimono	Kimono	{women}
formalwear	clothing	Costumes et tenues habillées	Festliche Kleidung	Abbigliamento formale	Ropa formal	Formele kleding	Strój formalny	{men,women,boys,girls}
suit	formalwear	Costume	Anzug	Abito	Traje	Pak	Garnitur	{men,women}
tuxedo	formalwear	Smoking	Smoking	Smoking	Esmoquin	Smoking	Smoking	{men}
sportswear	clothing	Vêtements de sport	Sportbekleidung	Abbigliamento sportivo	Ropa deportiva	Sportkleding	Odzież sportowa	{men,women,boys,girls}
bikini	sportswear	Bikini	Bikini	Bikini	Bikini	Bikini	Bikini	{women,girls}
sports-bra	sportswear	Brassière de sport	Sport-BH	Reggiseno sportivo	Sujetador deportivo	Sportbeha	Biustonosz sportowy	{women,girls}
sports-top	sportswear	T-shirt de sport	Sport-Top	Top sportivo	Top deportivo	Sporttop	Top sportowy	{men,women,boys,girls}
sports-jersey	sportswear	Maillot de sport	Sporttrikot	Maglia sportiva	Camiseta deportiva	Sportshirt	Koszulka sportowa	{men,women,boys,girls}
sports-shorts	sportswear	Short de sport	Sporthose	Shorts sportivi	Pantalones cortos deportivos	Sportshorts	Spodenki sportowe	{men,women,boys,girls}
sports-leggings	sportswear	Legging de sport	Sportleggings	Leggings sportivi	Leggings deportivos	Sportlegging	Legginsy sportowe	{women,girls}
dress	\N	Robe	Kleid	Vestito	Vestido	Jurk	Sukienka	{women,girls}
romper	\N	Combishort	Playsuit	Tutina	Mono corto	Playsuit	Kombinezon krótki	{women,girls}
overalls	\N	Salopette	Latzhose	Salopette	Peto	Tuinbroek	Ogrodniczki	{men,women,boys,girls}
swim suit	sportswear	Maillot de bain	Badeanzug	Costume da bagno	Bañador	Badpak	Kostium kąpielowy	{men,women,boys,girls}
track suit	sportswear	Survêtement	Trainingsanzug	Tuta	Chándal	Trainingspak	Dres	{men,women,boys,girls}
jump suit	\N	Combinaison	Jumpsuit	Tuta intera	Mono	Jumpsuit	Kombinezon	{men,women,boys,girls}
waistcoat	formalwear	Gilet de costume	Weste	Gilet	Chaleco de traje	Gilet	Kamizelka do garnituru	{men,boys,girls}
\.



COPY product_attributes.closures (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
Button fly	Braguette à boutons	Knopfleiste	Patta con bottoni	Bragueta de botones	Knoopsluiting	Rozporek na guziki
Buttons	Boutons	Knöpfe	Bottoni	Botones	Knopen	Guziki
Elastic	Élastique	Gummibund	Elastico	Elástico	Elastiek	Guma
Laces	Lacets	Schnürung	Lacci	Cordones	Veters	Sznurowanie
Pull-on	Enfilable	Schlupf	Pull-on	Sin cierre	Pull-on	Wciągany
Zip fly	Braguette zippée	Reißverschluss	Patta con zip	Bragueta de cremallera	Ritssluiting	Rozporek na zamek
Zipper	Fermeture éclair	Reißverschluss	Cerniera	Cremallera	Rits	Zamek błyskawiczny
Hook and eye	Agrafe	Haken und Öse	Gancio e occhiello	Corchete	Haak en oog	Haftka
Snap buttons	Boutons-pression	Druckknöpfe	Bottoni a pressione	Botones de presión	Drukknopen	Zatrzaski
Toggle	Brandebourg	Knebelknopf	Alamaro	Botón de palanca	Toggle	Szpila
Velcro	Velcro	Klettverschluss	Velcro	Velcro	Klittenband	Rzep
Drawstring	Cordon de serrage	Kordelzug	Coulisse	Cordón ajustable	Trekkoord	Ściągacz
\.



COPY product_attributes.colors (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl, hex_code, vinted_id, parent_color) FROM stdin;
Klein blue	\N	Klein-Blau	Blu Klein	Azul Klein	Klein blauw	Błękit Klein	#002FA7	\N	Blue
Vanilla yellow	\N	Vanillegelb	Giallo vaniglia	Amarillo vainilla	Vanillegeel	Waniliowy	#F3E5AB	\N	Yellow
Charcoal	Gris anthracite	Anthrazit	Antracite	Gris marengo	Antraciet	Antracytowy	\N	3	Gray
Silver	Argenté	Silber	Argento	Plata	Zilver	Srebrny	\N	13	Gray
Tan	Hâle	Hellbraun	Cuoio	Bronceado	Lichtbruin	Jasnobrązowy	\N	2	Brown
Camel	Camel	Camel	Cammello	Camello	Camel	Camelowy	\N	2	Brown
Cognac	Cognac	Cognac	Cognac	Coñac	Cognac	Koniakowy	\N	2	Brown
Burgundy	Bordeaux	Burgund	Borgogna	Burdeos	Bordeaux	Bordowy	\N	23	Red
Coral	Corail	Koralle	Corallo	Coral	Koraal	Koralowy	\N	22	Orange
Mustard	Moutarde	Senfgelb	Senape	Mostaza	Mosterd	Musztardowy	\N	29	Yellow
Gold	Doré	Gold	Oro	Dorado	Goud	Złoty	\N	14	Yellow
Olive	Olive	Oliv	Verde oliva	Oliva	Olijfgroen	Oliwkowy	\N	16	Green
Khaki	Kaki	Khaki	Kaki	Caqui	Kaki	Khaki	\N	16	Green
Mint	Menthe	Mint	Menta	Menta	Mint	Miętowy	\N	30	Green
Navy	Bleu marine	Marineblau	Blu navy	Azul marino	Marineblauw	Granatowy	\N	27	Blue
Light-blue	Bleu clair	Hellblau	Azzurro	Azul claro	Lichtblauw	Jasnoniebieski	\N	26	Blue
Teal	Bleu canard	Petrol	Verde petrolio	Verde azulado	Teal	Morski	\N	17	Blue
Turquoise	Turquoise	Türkis	Turchese	Turquesa	Turquoise	Turkusowy	\N	17	Blue
Lavender	Lavande	Lavendel	Lavanda	Lavanda	Lavendel	Lawendowy	\N	25	Purple
Fuchsia	Fuchsia	Fuchsia	Fucsia	Fucsia	Fuchsia	Fuksjowy	\N	5	Pink
Metallic	Métallique	Metallic	Metallizzato	Metálico	Metallic	Metaliczny	#C0C0C0	\N	\N
Beige	Beige	Beige	Beige	Beige	Beige	Beżowy	\N	4	\N
Black	Noir	Schwarz	Nero	Negro	Zwart	Czarny	\N	1	\N
Blue	Bleu	Blau	Blu	Azul	Blauw	Niebieski	\N	9	\N
Brown	Marron	Braun	Marrone	Marrón	Bruin	Brązowy	\N	2	\N
Cream	Crème	Creme	Crema	Crema	Crème	Kremowy	\N	20	\N
Gray	Gris	Grau	Grigio	Gris	Grijs	Szary	\N	3	\N
Green	Vert	Grün	Verde	Verde	Groen	Zielony	\N	10	\N
Multicolor	Multicolore	Mehrfarbig	Multicolore	Multicolor	Meerkleurig	Wielokolorowy	\N	15	\N
Orange	Orange	Orange	Arancione	Naranja	Oranje	Pomarańczowy	\N	11	\N
Pink	Rose	Rosa	Rosa	Rosa	Roze	Różowy	\N	24	\N
Purple	Violet	Lila	Viola	Morado	Paars	Fioletowy	\N	6	\N
Red	Rouge	Rot	Rosso	Rojo	Rood	Czerwony	\N	7	\N
White	Blanc	Weiß	Bianco	Blanco	Wit	Biały	\N	12	\N
Yellow	Jaune	Gelb	Giallo	Amarillo	Geel	Żółty	\N	8	\N
Off-white	Blanc cassé	Offwhite	Bianco sporco	Blanco roto	Gebroken wit	Złamana biel	#FAF9F6	\N	White
Ivory	Ivoire	Elfenbein	Avorio	Marfil	Ivoorwit	Kość słoniowa	#FFFFF0	\N	White
Sand	Sable	Sand	Sabbia	Arena	Zand	Piaskowy	#C2B280	\N	Beige
Nude	Nude	Nude	Nude	Nude	Nude	Nude	#E3BC9A	\N	Beige
Slate	Ardoise	Schiefergrau	Ardesia	Pizarra	Leisteen	Łupkowy	#708090	\N	Gray
Taupe	Taupe	Taupe	Tortora	Topo	Taupe	Taupe	#483C32	\N	Gray
Mocha	Moka	Mokka	Moka	Moca	Mokka	Mokka	#967969	\N	Brown
Chocolate	Chocolat	Schokobraun	Cioccolato	Chocolate	Chocolade	Czekoladowy	#7B3F00	\N	Brown
Espresso	Expresso	Espresso	Espresso	Expreso	Espresso	Espresso	#4E312D	\N	Brown
Cinnamon	Cannelle	Zimt	Cannella	Canela	Kaneel	Cynamonowy	#D2691E	\N	Brown
Wine	Vin	Weinrot	Vinaccia	Vino	Wijnrood	Wino	#722F37	\N	Red
Cherry red	Rouge cerise	Kirschrot	Rosso ciliegia	Rojo cereza	Kersenrood	Wiśniowy	#DE3163	\N	Red
Rust	Rouille	Rostbraun	Ruggine	Óxido	Roest	Rdzawy	#B7410E	\N	Red
Terracotta	Terracotta	Terrakotta	Terracotta	Terracota	Terracotta	Terakota	#E2725B	\N	Orange
Burnt orange	Orange brûlé	Gebranntes Orange	Arancione bruciato	Naranja quemado	Verbrand oranje	Spalona pomarańcz	#CC5500	\N	Orange
Peach	Pêche	Pfirsich	Pesca	Melocotón	Perzik	Brzoskwiniowy	#FFCBA4	\N	Orange
Butter yellow	Jaune beurre	Buttergelb	Giallo burro	Amarillo mantequilla	Botergeel	Maślany	#FFFAA0	\N	Yellow
Sage	Sauge	Salbei	Salvia	Salvia	Salie	Szałwiowy	#9DC183	\N	Green
Emerald	Émeraude	Smaragd	Smeraldo	Esmeralda	Smaragd	Szmaragdowy	#50C878	\N	Green
Forest green	Vert forêt	Waldgrün	Verde foresta	Verde bosque	Bosgroen	Leśna zieleń	#228B22	\N	Green
Cobalt	Cobalt	Kobaltblau	Blu cobalto	Azul cobalto	Kobaltblauw	Kobaltowy	#0047AB	\N	Blue
Powder blue	Bleu poudré	Puderblau	Blu polvere	Azul empolvado	Poederblauw	Pudrowy błękit	#B0E0E6	\N	Blue
Lilac	Lilas	Flieder	Lilla	Lila	Lila	Liliowy	#C8A2C8	\N	Purple
Plum	Prune	Pflaume	Prugna	Ciruela	Pruim	Śliwkowy	#8E4585	\N	Purple
Eggplant	Aubergine	Aubergine	Melanzana	Berenjena	Aubergine	Bakłażanowy	#614051	\N	Purple
Mauve	Mauve	Malve	Malva	Malva	Mauve	Różowofioletowy	#E0B0FF	\N	Purple
Blush	Rose poudré	Altrosa	Rosa cipria	Rosa empolvado	Blush	Pudrowy róż	#DE5D83	\N	Pink
Dusty pink	Vieux rose	Altrosa	Rosa antico	Rosa empolvado	Oudroze	Brudny róż	#D4A5A5	\N	Pink
Hot pink	Rose vif	Pink	Rosa acceso	Rosa intenso	Felroze	Intensywny róż	#FF69B4	\N	Pink
Rose gold	Or rose	Roségold	Oro rosa	Oro rosa	Roségoud	Różowe złoto	#B76E79	\N	Metallic
Bronze	Bronze	Bronze	Bronzo	Bronce	Brons	Brązowy	#CD7F32	\N	Metallic
\.



COPY product_attributes.condition_sups (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
Faded	Délavé	Ausgeblichen	Sbiadito	Desteñido	Vervaagd	Wyblakły
Resewn	Recousu	Neu genäht	Ricucito	Recosido	Opnieuw genaaid	Przeszyty
Stretched	Étiré	Ausgeleiert	Sformato	Estirado	Uitgerekt	Rozciągnięty
Worn	Porté	Abgetragen	Usurato	Desgastado	Versleten	Zużyty
Damaged button	Bouton endommagé	Beschädigter Knopf	Bottone danneggiato	Botón dañado	Beschadigde knoop	Uszkodzony guzik
Damaged patch	Patch endommagé	Beschädigter Aufnäher	Toppa danneggiata	Parche dañado	Beschadigde patch	Uszkodzona łata
Frayed hems	Ourlets effilochés	Ausgefranste Säume	Orli sfilacciati	Dobladillos deshilachados	Gerafelde zomen	Postrzępione brzegi
General wear	Usure générale	Allgemeine Abnutzung	Usura generale	Desgaste general	Algemene slijtage	Ogólne zużycie
Hem undone	Ourlet défait	Saum aufgegangen	Orlo scucito	Dobladillo descosido	Losgekomen zoom	Odpruty rąbek
Hemmed/shortened	Ourlé/Raccourci	Gesäumt/gekürzt	Orlo/accorciato	Dobladillo/acortado	Gezoomd/ingekort	Obszyte/skrócone
Knee wear	Usure aux genoux	Knieabnutzung	Usura alle ginocchia	Desgaste en rodillas	Knieslijtage	Zużycie na kolanach
Light discoloration	Légère décoloration	Leichte Verfärbung	Leggero scolorimento	Ligera decoloración	Lichte verkleuring	Lekkie odbarwienie
Marked discoloration	Décoloration marquée	Deutliche Verfärbung	Scolorimento marcato	Decoloración marcada	Duidelijke verkleuring	Wyraźne odbarwienie
Missing button	Bouton manquant	Fehlender Knopf	Bottone mancante	Botón faltante	Ontbrekende knoop	Brakujący guzik
Missing patch	Patch manquant	Fehlender Aufnäher	Toppa mancante	Parche faltante	Ontbrekende patch	Brakująca łata
Multiple holes	Plusieurs trous	Mehrere Löcher	Diversi buchi	Varios agujeros	Meerdere gaten	Wiele dziur
Multiple stains	Plusieurs taches	Mehrere Flecken	Diverse macchie	Varias manchas	Meerdere vlekken	Wiele plam
Pilling	Boulochage	Pilling	Pilling	Bolitas	Pilling	Mechacenie
Seam to fix	Couture à réparer	Naht zu reparieren	Cucitura da riparare	Costura a reparar	Naad te repareren	Szew do naprawy
Single stain	Tache unique	Einzelner Fleck	Macchia singola	Mancha única	Enkele vlek	Pojedyncza plama
Small hole	Petit trou	Kleines Loch	Piccolo buco	Pequeño agujero	Klein gaatje	Mała dziura
Snag	Accroc	Ziehfaden	Smagliatura	Enganchón	Haakje	Zaciągnięcie
Tapered	Ajusté	Verjüngt	Rastremato	Estrechado	Getailleerd	Zwężony
Torn	Déchiré	Gerissen	Strappato	Rasgado	Gescheurd	Rozdarty
Vintage patina	Patine vintage	Vintage-Patina	Patina vintage	Pátina vintage	Vintage patina	Patyna vintage
Vintage wear	Usure vintage	Vintage-Abnutzung	Usura vintage	Desgaste vintage	Vintage slijtage	Zużycie vintage
Waist altered	Taille modifiée	Taille geändert	Vita modificata	Cintura ajustada	Taille aangepast	Zmieniony pas
Zipper to replace	Fermeture à remplacer	Reißverschluss zu ersetzen	Cerniera da sostituire	Cremallera a reemplazar	Rits te vervangen	Zamek do wymiany
New With Tags (NWT)	Neuf Avec Étiquettes (NWT)	Neu mit Etikett (NWT)	Nuovo con cartellino (NWT)	Nuevo con etiquetas (NWT)	Nieuw met labels (NWT)	Nowy z metkami (NWT)
New Without Tags (NWOT)	Neuf Sans Étiquettes (NWOT)	Neu ohne Etikett (NWOT)	Nuovo senza cartellino (NWOT)	Nuevo sin etiquetas (NWOT)	Nieuw zonder labels (NWOT)	Nowy bez metek (NWOT)
Deadstock (NOS)	Stock Mort (NOS)	Deadstock (NOS)	Deadstock (NOS)	Stock antiguo nuevo (NOS)	Deadstock (NOS)	Deadstock (NOS)
Color bleeding	Dégorgement de couleur	Farbübertragung	Sanguinamento colore	Sangrado de color	Kleurafgifte	Farbowanie
Sun fading	Décoloration solaire	Sonnenverfärbung	Scolorimento solare	Decoloración solar	Zonverkleuring	Wyblakłe od słońca
Moth holes	Trous de mites	Mottenlöcher	Buchi di tarme	Agujeros de polilla	Motgaatjes	Dziury od moli
Odor	Odeur	Geruch	Odore	Olor	Geur	Zapach
Elastic worn	Élastique usé	Gummi ausgeleiert	Elastico usurato	Elástico gastado	Elastiek versleten	Zużyta guma
Lining damaged	Doublure abîmée	Futter beschädigt	Fodera danneggiata	Forro dañado	Voering beschadigd	Uszkodzona podszewka
\.



COPY product_attributes.conditions (note, name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl, vinted_id, ebay_condition, coefficient) FROM stdin;
10	New	Neuf	Neu	Nuovo	Nuevo	Nieuw	Nowy	6	NEW	1.000
9	Like new	Comme neuf	Wie neu	Come nuovo	Como nuevo	Als nieuw	Jak nowy	1	PRE_OWNED_EXCELLENT	0.950
8	Excellent	Excellent état	Ausgezeichnet	Eccellente	Excelente	Uitstekend	Doskonały	2	PRE_OWNED_EXCELLENT	0.900
7	Very good	Très bon état	Sehr gut	Molto buono	Muy bueno	Zeer goed	Bardzo dobry	2	PRE_OWNED_GOOD	0.850
6	Good	Bon état	Gut	Buono	Bueno	Goed	Dobry	3	PRE_OWNED_GOOD	0.800
5	Shows wear	Traces d'usure visibles	Gebrauchsspuren	Segni di usura	Señales de uso	Gebruikssporen	Ślady użytkowania	3	PRE_OWNED_FAIR	0.700
4	Acceptable	État acceptable	Akzeptabel	Accettabile	Aceptable	Acceptabel	Akceptowalny	4	PRE_OWNED_FAIR	0.600
3	Poor	Mauvais état	Schlecht	Scarso	Malo	Slecht	Zły	4	PRE_OWNED_POOR	0.500
2	Very poor	Très mauvais état	Sehr schlecht	Molto scarso	Muy malo	Zeer slecht	Bardzo zły	4	PRE_OWNED_POOR	0.400
1	For parts only	Pour pièces uniquement	Nur für Teile	Solo per parti	Solo para piezas	Alleen voor onderdelen	Tylko na części	4	FOR_PARTS_OR_NOT_WORKING	0.300
0	Major defects	Défauts majeurs	Große Mängel	Difetti maggiori	Defectos mayores	Grote gebreken	Poważne wady	4	FOR_PARTS_OR_NOT_WORKING	0.200
\.



COPY product_attributes.decades (name_en) FROM stdin;
50s
60s
70s
80s
90s
2000s
2010s
2020s
\.



COPY product_attributes.dim1 (value) FROM stdin;
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
\.



COPY product_attributes.dim2 (value) FROM stdin;
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98
99
100
101
102
103
104
105
106
107
108
109
110
111
112
113
114
115
116
117
118
119
120
\.



COPY product_attributes.dim3 (value) FROM stdin;
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
\.



COPY product_attributes.dim4 (value) FROM stdin;
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
\.



COPY product_attributes.dim5 (value) FROM stdin;
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
\.



COPY product_attributes.dim6 (value) FROM stdin;
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98
99
100
\.



COPY product_attributes.fits (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
Slim	Slim	Slim	Slim	Slim	Slim	Slim
Regular	Regular	Regular	Regular	Regular	Regular	Regular
Relaxed	Relaxed	Relaxed	Relaxed	Relaxed	Relaxed	Relaxed
Oversized	Oversize	Oversized	Oversize	Oversize	Oversized	Oversize
Tight	Moulant	Eng	Aderente	Ajustado	Strak	Obcisły
Loose	Loose	Weit	Ampio	Holgado	Ruim	Luźny
Athletic	Athlétique	Athletisch	Atletico	Atlético	Atletisch	Atletyczny
Baggy	Baggy	Baggy	Baggy	Baggy	Baggy	Baggy
Bootcut	Bootcut	Bootcut	Bootcut	Bootcut	Bootcut	Bootcut
Flare	Évasé	Schlaghose	Svasato	Acampanado	Flared	Dzwony
Skinny	Skinny	Skinny	Skinny	Skinny	Skinny	Skinny
Straight	Droit	Gerade	Dritto	Recto	Recht	Prosty
Balloon	Balloon	Ballon	Palloncino	Globo	Ballon	Balonowy
\.



COPY product_attributes.genders (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl, vinted_id, ebay_gender, etsy_gender) FROM stdin;
Boys	Garçon	Jungen	Bambini	Niños	Jongens	Chłopcy	\N	\N	\N
Girls	Fille	Mädchen	Bambine	Niñas	Meisjes	Dziewczynki	\N	\N	\N
Men	Homme	Herren	Uomo	Hombre	Heren	Mężczyźni	\N	\N	\N
Unisex	Unisexe	Unisex	Unisex	Unisex	Unisex	Unisex	\N	\N	\N
Women	Femme	Damen	Donna	Mujer	Dames	Kobiety	\N	\N	\N
\.



COPY product_attributes.lengths (name_en, name_fr, description, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
Ankle	Cheville	\N	Knöchellang	Alla caviglia	Tobillero	Enkellang	Do kostki
Capri	Capri	\N	Capri	Capri	Capri	Capri	Capri
Cropped	Raccourci	\N	Cropped	Cropped	Cropped	Cropped	Skrócony
Extra long	Extra long	\N	Extralang	Extra lungo	Extra largo	Extra lang	Ekstra długi
Floor length	Longueur sol	\N	Bodenlang	Lunghezza pavimento	Largo al suelo	Vloerlang	Do ziemi
Knee length	Mi-long	\N	Knielang	Al ginocchio	Hasta la rodilla	Knielang	Do kolan
Long	Long	\N	Lang	Lungo	Largo	Lang	Długi
Maxi	Maxi	\N	Maxi	Maxi	Maxi	Maxi	Maxi
Midi	Midi	\N	Midi	Midi	Midi	Midi	Midi
Mini	Mini	\N	Mini	Mini	Mini	Mini	Mini
Regular	Standard	\N	Regular	Regolare	Regular	Normaal	Standardowy
Short	Court	\N	Kurz	Corto	Corto	Kort	Krótki
\.



COPY product_attributes.linings (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
Unlined	Sans doublure	Ungefüttert	Senza fodera	Sin forro	Ongevoerd	Bez podszewki
Fully lined	Entièrement doublé	Voll gefüttert	Foderato completamente	Completamente forrado	Volledig gevoerd	Całkowicie podszyte
Partially lined	Partiellement doublé	Teilweise gefüttert	Parzialmente foderato	Parcialmente forrado	Gedeeltelijk gevoerd	Częściowo podszyte
Fleece lined	Doublure polaire	Fleecegefüttert	Foderato in pile	Forro polar	Fleece gevoerd	Podszewka polarowa
\.



COPY product_attributes.materials (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl, vinted_id) FROM stdin;
Crochet	Crochet	Häkelstoff	Uncinetto	Crochet	Gehaakt	Szydełkowy	\N
Lace	Dentelle	Spitze	Pizzo	Encaje	Kant	Koronka	\N
Technical fabric	Tissu technique	Funktionsstoff	Tessuto tecnico	Tejido técnico	Technische stof	Tkanina techniczna	\N
Silk	Soie	Seide	Seta	Seda	Zijde	Jedwab	49
Cotton	Coton	Baumwolle	Cotone	Algodón	Katoen	Bawełna	44
Polyester	Polyester	Polyester	Poliestere	Poliéster	Polyester	Poliester	45
Wool	Laine	Wolle	Lana	Lana	Wol	Wełna	46
Leather	Cuir	Leder	Pelle	Cuero	Leer	Skóra	43
Denim	Denim	Denim	Denim	Denim	Denim	Denim	303
Linen	Lin	Leinen	Lino	Lino	Linnen	Len	146
Cashmere	Cachemire	Kaschmir	Cashmere	Cachemir	Kasjmier	Kaszmir	123
Velvet	Velours	Samt	Velluto	Terciopelo	Fluweel	Aksamit	466
Suede	Daim	Wildleder	Scamosciato	Ante	Suède	Zamsz	298
Nylon	Nylon	Nylon	Nylon	Nailon	Nylon	Nylon	52
Viscose	Viscose	Viskose	Viscosa	Viscosa	Viscose	Wiskoza	48
Acrylic	Acrylique	Acryl	Acrilico	Acrílico	Acryl	Akryl	149
Spandex	Élasthanne	Elasthan	Spandex	Spandex	Spandex	Spandex	53
Fleece	Polaire	Fleece	Pile	Forro polar	Fleece	Polar	120
Corduroy	Velours côtelé	Cord	Velluto a coste	Pana	Ribfluweel	Sztruks	299
Elastane	Élasthanne	Elasthan	Elastan	Elastano	Elastaan	Elastan	53
Flannel	Flanelle	Flanell	Flanella	Franela	Flanel	Flanela	451
Hemp	Chanvre	Hanf	Canapa	Cáñamo	Hennep	Konopie	\N
Lyocell	Lyocell	Lyocell	Lyocell	Lyocell	Lyocell	Lyocell	\N
Modal	Modal	Modal	Modal	Modal	Modal	Modal	\N
Rayon	Rayonne	Rayon	Rayon	Rayón	Rayon	Wiskoza sztuczna	\N
Satin	Satin	Satin	Raso	Satén	Satijn	Satyna	311
Tweed	Tweed	Tweed	Tweed	Tweed	Tweed	Tweed	465
\.



COPY product_attributes.necklines (name_en, name_fr, description, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
Boat neck	Col bateau	\N	Bootausschnitt	Scollo a barca	Cuello barco	Boothals	Dekolt łódka
Collared	Col chemise	\N	Mit Kragen	Con colletto	Con cuello	Met kraag	Z kołnierzem
Cowl neck	Col bénitier	\N	Wasserfallausschnitt	Collo a cascata	Cuello drapeado	Cowlhals	Dekolt wodospad
Crew neck	Col rond	\N	Rundhalsausschnitt	Girocollo	Cuello redondo	Ronde hals	Okrągły dekolt
Halter	Col licou	\N	Neckholder	Collo all'americana	Cuello halter	Halter	Wiązany na szyi
Henley	Col tunisien	\N	Henley-Kragen	Collo serafino	Cuello panadero	Henley	Henley
Hood	Capuche	\N	Kapuze	Cappuccio	Capucha	Capuchon	Kaptur
Mandarin collar	Col mao	\N	Stehkragen	Collo alla coreana	Cuello mao	Maokraag	Kołnierz stójka
Mock neck	Col montant	\N	Stehkragen	Collo alto	Cuello alto	Opstaande kraag	Półgolf
Notch lapel	Revers cranté	\N	Fallrevers	Rever classico	Solapa de muesca	Inkeping revers	Klapa z wcięciem
Off-shoulder	Épaules dénudées	\N	Schulterfrei	Spalle scoperte	Hombros descubiertos	Off-shoulder	Opadające ramiona
Peak lapel	Revers pointu	\N	Spitzrevers	Rever a punta	Solapa de pico	Puntige revers	Klapa szpicowa
Polo collar	Col polo	\N	Polokragen	Collo polo	Cuello polo	Polokraag	Kołnierz polo
Round neck	Col rond	\N	Rundhals	Scollo tondo	Cuello redondo	Ronde hals	Okrągły dekolt
Scoop neck	Col échancré	\N	U-Ausschnitt	Scollo ampio	Cuello redondo amplio	Lage ronde hals	Głęboki dekolt
Shawl collar	Col châle	\N	Schalkragen	Collo a scialle	Cuello chal	Sjaalkraag	Kołnierz szalowy
Square neck	Col carré	\N	Karree-Ausschnitt	Scollo quadrato	Cuello cuadrado	Vierkante hals	Dekolt karo
Turtleneck	Col roulé	\N	Rollkragen	Collo alto	Cuello alto	Coltrui	Golf
V-neck	Col V	\N	V-Ausschnitt	Scollo a V	Cuello en V	V-hals	Dekolt V
Funnel neck	Col cheminée	\N	Trichterkragen	Collo a imbuto	Cuello chimenea	Tunnelkraag	Kołnierz lejek
\.



COPY product_attributes.origins (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
Australia	Australie	Australien	Australia	Australia	Australië	Australia
Bahrain	Bahreïn	Bahrain	Bahrein	Baréin	Bahrein	Bahrajn
Bangladesh	Bangladesh	Bangladesch	Bangladesh	Bangladés	Bangladesh	Bangladesz
Belgium	Belgique	Belgien	Belgio	Bélgica	België	Belgia
Brazil	Brésil	Brasilien	Brasile	Brasil	Brazilië	Brazylia
Brunei	Brunei	Brunei	Brunei	Brunéi	Brunei	Brunei
Cambodia	Cambodge	Kambodscha	Cambogia	Camboya	Cambodja	Kambodża
Canada	Canada	Kanada	Canada	Canadá	Canada	Kanada
China	Chine	China	Cina	China	China	Chiny
Colombia	Colombie	Kolumbien	Colombia	Colombia	Colombia	Kolumbia
Costa rica	Costa Rica	Costa Rica	Costa Rica	Costa Rica	Costa Rica	Kostaryka
Dominican republic	République Dominicaine	Dominikanische Republik	Repubblica Dominicana	República Dominicana	Dominicaanse Republiek	Dominikana
Egypt	Égypte	Ägypten	Egitto	Egipto	Egypte	Egipt
El salvador	El Salvador	El Salvador	El Salvador	El Salvador	El Salvador	Salwador
France	France	Frankreich	Francia	Francia	Frankrijk	Francja
Germany	Allemagne	Deutschland	Germania	Alemania	Duitsland	Niemcy
Guatemala	Guatemala	Guatemala	Guatemala	Guatemala	Guatemala	Gwatemala
Haiti	Haïti	Haiti	Haiti	Haití	Haïti	Haiti
Honduras	Honduras	Honduras	Honduras	Honduras	Honduras	Honduras
Hong kong	Hong Kong	Hongkong	Hong Kong	Hong Kong	Hongkong	Hongkong
India	Inde	Indien	India	India	India	Indie
Indonesia	Indonésie	Indonesien	Indonesia	Indonesia	Indonesië	Indonezja
Italy	Italie	Italien	Italia	Italia	Italië	Włochy
Japan	Japon	Japan	Giappone	Japón	Japan	Japonia
Jordan	Jordanie	Jordanien	Giordania	Jordania	Jordanië	Jordania
Kenya	Kenya	Kenia	Kenya	Kenia	Kenia	Kenia
Malaysia	Malaisie	Malaysia	Malesia	Malasia	Maleisië	Malezja
Malta	Malte	Malta	Malta	Malta	Malta	Malta
Mauritius	Maurice	Mauritius	Mauritius	Mauricio	Mauritius	Mauritius
Mexico	Mexique	Mexiko	Messico	México	Mexico	Meksyk
Morocco	Maroc	Marokko	Marocco	Marruecos	Marokko	Maroko
Netherlands	Pays-Bas	Niederlande	Paesi Bassi	Países Bajos	Nederland	Holandia
Nicaragua	Nicaragua	Nicaragua	Nicaragua	Nicaragua	Nicaragua	Nikaragua
Norway	Norvège	Norwegen	Norvegia	Noruega	Noorwegen	Norwegia
Pakistan	Pakistan	Pakistan	Pakistan	Pakistán	Pakistan	Pakistan
Philippines	Philippines	Philippinen	Filippine	Filipinas	Filipijnen	Filipiny
Poland	Pologne	Polen	Polonia	Polonia	Polen	Polska
Portugal	Portugal	Portugal	Portogallo	Portugal	Portugal	Portugalia
Slovakia	Slovaquie	Slowakei	Slovacchia	Eslovaquia	Slowakije	Słowacja
South korea	Corée du Sud	Südkorea	Corea del Sud	Corea del Sur	Zuid-Korea	Korea Południowa
Spain	Espagne	Spanien	Spagna	España	Spanje	Hiszpania
Taiwan	Taïwan	Taiwan	Taiwan	Taiwán	Taiwan	Tajwan
Tunisia	Tunisie	Tunesien	Tunisia	Túnez	Tunesië	Tunezja
Turkey	Turquie	Türkei	Turchia	Turquía	Turkije	Turcja
Turkmenistan	Turkménistan	Turkmenistan	Turkmenistan	Turkmenistán	Turkmenistan	Turkmenistan
United kingdom	Royaume-Uni	Vereinigtes Königreich	Regno Unito	Reino Unido	Verenigd Koninkrijk	Wielka Brytania
Usa	États-Unis	USA	USA	EE. UU.	VS	USA
Vietnam	Vietnam	Vietnam	Vietnam	Vietnam	Vietnam	Wietnam
\.



COPY product_attributes.patterns (name_en, name_fr, description, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
Abstract	Abstrait	\N	Abstrakt	Astratto	Abstracto	Abstract	Abstrakcyjny
Animal print	Imprimé animal	\N	Animal-Print	Stampa animalier	Estampado animal	Dierenprint	Print zwierzęcy
Camouflage	Camouflage	\N	Camouflage	Camouflage	Camuflaje	Camouflage	Kamuflaż
Checkered	Carreaux	\N	Kariert	A quadri	Cuadros	Geruit	Kratka
Color block	Color block	\N	Color Block	Color block	Color block	Colorblock	Color block
Floral	Floral	\N	Blumenmuster	Floreale	Floral	Bloemen	Kwiatowy
Geometric	Géométrique	\N	Geometrisch	Geometrico	Geométrico	Geometrisch	Geometryczny
Graphic	Graphique	\N	Grafisch	Grafico	Gráfico	Grafisch	Graficzny
Herringbone	Chevrons	\N	Fischgrat	Spina di pesce	Espiguilla	Visgraat	Jodełka
Houndstooth	Pied-de-poule	\N	Hahnentritt	Pied de poule	Pata de gallo	Pied-de-poule	Pepitka
Ombre	Ombré	\N	Ombré	Sfumato	Degradado	Ombré	Ombre
Paisley	Cachemire	\N	Paisley	Paisley	Cachemir	Paisley	Paisley
Plaid	Tartan	\N	Karo	Tartan	Tartán	Tartan	Tartan
Polka dot	Pois	\N	Punkte	Pois	Lunares	Stippen	Grochy
Solid	Uni	\N	Unifarben	Tinta unita	Liso	Effen	Jednolity
Striped	Rayé	\N	Gestreift	A righe	Rayas	Gestreept	Paski
Tie-dye	Tie-dye	\N	Batik	Tie-dye	Tie-dye	Tie-dye	Tie-dye
Tropical	Tropical	\N	Tropisch	Tropicale	Tropical	Tropisch	Tropikalny
\.



COPY product_attributes.rises (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
High-rise	Taille haute	High-Rise	Vita alta	Tiro alto	Hoge taille	Wysoki stan
Low-rise	Taille basse	Low-Rise	Vita bassa	Tiro bajo	Lage taille	Niski stan
Mid-rise	Taille moyenne	Mid-Rise	Vita media	Tiro medio	Middelhoge taille	Średni stan
Regular rise	Taille normale	Regular Rise	Vita normale	Tiro normal	Normale taille	Normalny stan
Super low-rise	Taille très basse	Super Low-Rise	Vita molto bassa	Tiro muy bajo	Zeer lage taille	Bardzo niski stan
Ultra high-rise	Taille très haute	Ultra High-Rise	Vita molto alta	Tiro muy alto	Zeer hoge taille	Bardzo wysoki stan
\.



COPY product_attributes.seasons (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
Spring	Printemps	Frühling	Primavera	Primavera	Lente	Wiosna
Summer	Été	Sommer	Estate	Verano	Zomer	Lato
Autumn	Automne	Herbst	Autunno	Otoño	Herfst	Jesień
Winter	Hiver	Winter	Inverno	Invierno	Winter	Zima
All seasons	Toutes saisons	Ganzjährig	Tutte le stagioni	Todas las temporadas	Alle seizoenen	Wszystkie pory roku
\.



COPY product_attributes.sizes_normalized (name_en, ebay_size, etsy_size, vinted_women_id, vinted_men_id) FROM stdin;
36	\N	\N	\N	\N
38	\N	\N	\N	\N
40	\N	\N	\N	\N
42	\N	\N	\N	\N
44	\N	\N	\N	\N
46	\N	\N	\N	\N
48	\N	\N	\N	\N
50	\N	\N	\N	\N
XXXL	\N	\N	\N	\N
One Size	\N	\N	\N	\N
one-size	\N	\N	\N	\N
W24/L26	\N	\N	\N	\N
W24/L36	\N	\N	\N	\N
W26/L36	\N	\N	\N	\N
W28/L14	\N	\N	\N	\N
W28/L38	\N	\N	\N	\N
W30/L22	\N	\N	\N	\N
W32/L22	\N	\N	\N	\N
W34/L40	\N	\N	\N	\N
W42/L36	\N	\N	\N	\N
W44/L26	\N	\N	\N	\N
W48/L30	\N	\N	\N	\N
W11/L1	\N	\N	\N	\N
W11/L11	\N	\N	\N	\N
W111/L11	\N	\N	\N	\N
3XL	\N	\N	310	212
4XL	\N	\N	311	308
L	\N	\N	5	209
M	\N	\N	4	208
S	\N	\N	3	207
W22/L28	\N	\N	1226	1631
W22/L32	\N	\N	1226	1631
W24	\N	\N	102	1632
W24/L28	\N	\N	102	1632
W24/L30	\N	\N	102	1632
W24/L32	\N	\N	102	1632
W24/L34	\N	\N	102	1632
W26	\N	\N	2	1634
W26/L26	\N	\N	2	1634
W26/L28	\N	\N	2	1634
W26/L30	\N	\N	2	1634
W26/L32	\N	\N	2	1634
W26/L34	\N	\N	2	1634
W26/L38	\N	\N	2	1634
W28	\N	\N	3	1636
W28/L24	\N	\N	3	1636
W28/L26	\N	\N	3	1636
W28/L28	\N	\N	3	1636
W28/L30	\N	\N	3	1636
W28/L32	\N	\N	3	1636
W28/L34	\N	\N	3	1636
W28/L36	\N	\N	3	1636
W30	\N	\N	4	1638
W30/L24	\N	\N	4	1638
W30/L26	\N	\N	4	1638
W30/L28	\N	\N	4	1638
W30/L30	\N	\N	4	1638
W30/L32	\N	\N	4	1638
W30/L34	\N	\N	4	1638
W30/L36	\N	\N	4	1638
W30/L38	\N	\N	4	1638
W32	\N	\N	5	1640
W32/L26	\N	\N	5	1640
W32/L28	\N	\N	5	1640
W32/L30	\N	\N	5	1640
W32/L32	\N	\N	5	1640
W32/L34	\N	\N	5	1640
W32/L36	\N	\N	5	1640
W32/L38	\N	\N	5	1640
W34	\N	\N	6	1642
W34/L26	\N	\N	6	1642
W34/L28	\N	\N	6	1642
W34/L30	\N	\N	6	1642
W34/L32	\N	\N	6	1642
W34/L34	\N	\N	6	1642
W34/L36	\N	\N	6	1642
W34/L38	\N	\N	6	1642
W36	\N	\N	310	1643
W36/L26	\N	\N	310	1643
W36/L28	\N	\N	310	1643
W36/L30	\N	\N	310	1643
W36/L32	\N	\N	310	1643
W36/L34	\N	\N	310	1643
W36/L36	\N	\N	310	1643
W38	\N	\N	311	1644
W38/L26	\N	\N	311	1644
W38/L28	\N	\N	311	1644
W38/L30	\N	\N	311	1644
W38/L32	\N	\N	311	1644
W38/L34	\N	\N	311	1644
W38/L36	\N	\N	311	1644
W38/L38	\N	\N	311	1644
W40	\N	\N	312	1645
W40/L28	\N	\N	312	1645
W40/L30	\N	\N	312	1645
W40/L32	\N	\N	312	1645
W40/L34	\N	\N	312	1645
W40/L36	\N	\N	312	1645
W40/L38	\N	\N	312	1645
W42	\N	\N	1227	1646
W42/L26	\N	\N	1227	1646
W42/L28	\N	\N	1227	1646
W42/L30	\N	\N	1227	1646
W42/L32	\N	\N	1227	1646
W42/L34	\N	\N	1227	1646
W44	\N	\N	1228	1647
W44/L30	\N	\N	1228	1647
W44/L32	\N	\N	1228	1647
W44/L34	\N	\N	1228	1647
W46	\N	\N	1229	1648
W46/L28	\N	\N	1229	1648
W46/L30	\N	\N	1229	1648
W46/L32	\N	\N	1229	1648
W46/L34	\N	\N	1229	1648
W48/L32	\N	\N	1230	1649
W48/L34	\N	\N	1230	1649
W50/L32	\N	\N	1230	1704
W50/L34	\N	\N	1230	1704
W52	\N	\N	1230	1705
W52/L32	\N	\N	1230	1705
W52/L36	\N	\N	1230	1705
W54/L32	\N	\N	1230	1706
W56/L32	\N	\N	1230	1706
XL	\N	\N	6	210
XS	\N	\N	2	206
XXL	\N	\N	7	211
XXS	\N	\N	102	206
TAILLE UNIQUE	\N	\N	\N	\N
W22/L30	\N	\N	\N	\N
W338/L28	\N	\N	\N	\N
W36/L38	\N	\N	\N	\N
W38/L24	\N	\N	\N	\N
W40/L26	\N	\N	\N	\N
W48/L26	\N	\N	\N	\N
W50/L30	\N	\N	\N	\N
\.



COPY product_attributes.sizes_original (name, created_at) FROM stdin;
8m	2026-01-06 14:20:01.562421+00
w24	2026-01-06 14:20:01.562421+00
w42	2026-01-06 14:20:01.562421+00
W34 L33	2026-01-06 14:20:01.562421+00
34 x 34	2026-01-06 14:20:01.562421+00
S	2026-01-06 14:20:01.562421+00
W 28 L 32	2026-01-06 14:20:01.562421+00
40 X 30	2026-01-06 14:20:01.562421+00
471	2026-01-06 14:20:01.562421+00
33-34	2026-01-06 14:20:01.562421+00
11 long	2026-01-06 14:20:01.562421+00
15	2026-01-06 14:20:01.562421+00
32x32	2026-01-06 14:20:01.562421+00
18 LONG	2026-01-06 14:20:01.562421+00
36 x 29	2026-01-06 14:20:01.562421+00
32 X 34	2026-01-06 14:20:01.562421+00
44 eur	2026-01-06 14:20:01.562421+00
12 med	2026-01-06 14:20:01.562421+00
18w/l	2026-01-06 14:20:01.562421+00
large	2026-01-06 14:20:01.562421+00
31x32	2026-01-06 14:20:01.562421+00
6 m	2026-01-06 14:20:01.562421+00
30-34	2026-01-06 14:20:01.562421+00
W40 L34	2026-01-06 14:20:01.562421+00
w32/l33	2026-01-06 14:20:01.562421+00
w32/l31	2026-01-06 14:20:01.562421+00
42 x 34	2026-01-06 14:20:01.562421+00
40 x 36	2026-01-06 14:20:01.562421+00
42 X 32	2026-01-06 14:20:01.562421+00
w29/l34	2026-01-06 14:20:01.562421+00
w38/l34	2026-01-06 14:20:01.562421+00
w34	2026-01-06 14:20:01.562421+00
8 MEDIUM	2026-01-06 14:20:01.562421+00
w31 l34	2026-01-06 14:20:01.562421+00
44	2026-01-06 14:20:01.562421+00
young xl	2026-01-06 14:20:01.562421+00
w24/l30	2026-01-06 14:20:01.562421+00
34 x 29	2026-01-06 14:20:01.562421+00
14 m	2026-01-06 14:20:01.562421+00
34 x 38	2026-01-06 14:20:01.562421+00
14M	2026-01-06 14:20:01.562421+00
8P	2026-01-06 14:20:01.562421+00
160cm	2026-01-06 14:20:01.562421+00
w27/l36	2026-01-06 14:20:01.562421+00
36/30	2026-01-06 14:20:01.562421+00
18 long	2026-01-06 14:20:01.562421+00
36 x 34	2026-01-06 14:20:01.562421+00
W36 L34	2026-01-06 14:20:01.562421+00
36x30	2026-01-06 14:20:01.562421+00
9 jr l	2026-01-06 14:20:01.562421+00
W 33 L 34	2026-01-06 14:20:01.562421+00
42 X 29	2026-01-06 14:20:01.562421+00
35 x 30	2026-01-06 14:20:01.562421+00
12 medium / mediano / moyen	2026-01-06 14:20:01.562421+00
16 husky / 16 amplio	2026-01-06 14:20:01.562421+00
w:97 l:86	2026-01-06 14:20:01.562421+00
w28/l31	2026-01-06 14:20:01.562421+00
29	2026-01-06 14:20:01.562421+00
38/34	2026-01-06 14:20:01.562421+00
w30/l32 10m	2026-01-06 14:20:01.562421+00
32-32	2026-01-06 14:20:01.562421+00
L/G	2026-01-06 14:20:01.562421+00
misses 4 short	2026-01-06 14:20:01.562421+00
ne pas si fier car le vêtement a été modifié	2026-01-06 14:20:01.562421+00
30 x 32	2026-01-06 14:20:01.562421+00
w26/l28	2026-01-06 14:20:01.562421+00
43	2026-01-06 14:20:01.562421+00
29 X 34	2026-01-06 14:20:01.562421+00
10 PETITE	2026-01-06 14:20:01.562421+00
10 medium	2026-01-06 14:20:01.562421+00
W32 L36	2026-01-06 14:20:01.562421+00
w40/l38	2026-01-06 14:20:01.562421+00
4/ 27	2026-01-06 14:20:01.562421+00
w34/l34	2026-01-06 14:20:01.562421+00
w34/l29	2026-01-06 14:20:01.562421+00
w40/l29	2026-01-06 14:20:01.562421+00
8 M	2026-01-06 14:20:01.562421+00
w38	2026-01-06 14:20:01.562421+00
16 reg	2026-01-06 14:20:01.562421+00
30x32	2026-01-06 14:20:01.562421+00
W29	2026-01-06 14:20:01.562421+00
w27/l32	2026-01-06 14:20:01.562421+00
size 27	2026-01-06 14:20:01.562421+00
33-42	2026-01-06 14:20:01.562421+00
44ul	2026-01-06 14:20:01.562421+00
w34 l32	2026-01-06 14:20:01.562421+00
w25	2026-01-06 14:20:01.562421+00
46 fr	2026-01-06 14:20:01.562421+00
w36/l35	2026-01-06 14:20:01.562421+00
42x32	2026-01-06 14:20:01.562421+00
14 medium	2026-01-06 14:20:01.562421+00
fr42	2026-01-06 14:20:01.562421+00
34x30	2026-01-06 14:20:01.562421+00
w40/l30	2026-01-06 14:20:01.562421+00
30 X 30	2026-01-06 14:20:01.562421+00
9 jr s	2026-01-06 14:20:01.562421+00
28-33	2026-01-06 14:20:01.562421+00
12 medium	2026-01-06 14:20:01.562421+00
W 28	2026-01-06 14:20:01.562421+00
40/34	2026-01-06 14:20:01.562421+00
2x	2026-01-06 14:20:01.562421+00
girls 18 regular	2026-01-06 14:20:01.562421+00
34/36	2026-01-06 14:20:01.562421+00
32/34	2026-01-06 14:20:01.562421+00
w44/l32	2026-01-06 14:20:01.562421+00
38x38	2026-01-06 14:20:01.562421+00
46 reg	2026-01-06 14:20:01.562421+00
w26	2026-01-06 14:20:01.562421+00
12 M	2026-01-06 14:20:01.562421+00
W32 L34	2026-01-06 14:20:01.562421+00
11	2026-01-06 14:20:01.562421+00
56	2026-01-06 14:20:01.562421+00
W42	2026-01-06 14:20:01.562421+00
w36/l29	2026-01-06 14:20:01.562421+00
8 petite	2026-01-06 14:20:01.562421+00
44 x 32	2026-01-06 14:20:01.562421+00
40 32	2026-01-06 14:20:01.562421+00
6 medium	2026-01-06 14:20:01.562421+00
25	2026-01-06 14:20:01.562421+00
28x34	2026-01-06 14:20:01.562421+00
w28 l31	2026-01-06 14:20:01.562421+00
84	2026-01-06 14:20:01.562421+00
38x32	2026-01-06 14:20:01.562421+00
W32 L33	2026-01-06 14:20:01.562421+00
40x30	2026-01-06 14:20:01.562421+00
38-32	2026-01-06 14:20:01.562421+00
t38	2026-01-06 14:20:01.562421+00
36 x 30	2026-01-06 14:20:01.562421+00
34/33	2026-01-06 14:20:01.562421+00
28 x 36	2026-01-06 14:20:01.562421+00
w26/l30	2026-01-06 14:20:01.562421+00
m	2026-01-06 14:20:01.562421+00
34 34	2026-01-06 14:20:01.562421+00
fr40	2026-01-06 14:20:01.562421+00
28x32	2026-01-06 14:20:01.562421+00
46	2026-01-06 14:20:01.562421+00
8 P	2026-01-06 14:20:01.562421+00
w46/l30	2026-01-06 14:20:01.562421+00
11/12 x 32	2026-01-06 14:20:01.562421+00
14 M 	2026-01-06 14:20:01.562421+00
18 m	2026-01-06 14:20:01.562421+00
4 short	2026-01-06 14:20:01.562421+00
W 33	2026-01-06 14:20:01.562421+00
6 p	2026-01-06 14:20:01.562421+00
27x32	2026-01-06 14:20:01.562421+00
7m	2026-01-06 14:20:01.562421+00
w33 l32	2026-01-06 14:20:01.562421+00
34x29	2026-01-06 14:20:01.562421+00
w44	2026-01-06 14:20:01.562421+00
XS / 34 / 6	2026-01-06 14:20:01.562421+00
xl enfant	2026-01-06 14:20:01.562421+00
16 l	2026-01-06 14:20:01.562421+00
w30/32	2026-01-06 14:20:01.562421+00
2xl	2026-01-06 14:20:01.562421+00
W33 L32	2026-01-06 14:20:01.562421+00
35 36	2026-01-06 14:20:01.562421+00
38x36	2026-01-06 14:20:01.562421+00
8 mediano	2026-01-06 14:20:01.562421+00
12 slim	2026-01-06 14:20:01.562421+00
33x32	2026-01-06 14:20:01.562421+00
W36	2026-01-06 14:20:01.562421+00
32x34	2026-01-06 14:20:01.562421+00
w54/l30	2026-01-06 14:20:01.562421+00
7/8 long	2026-01-06 14:20:01.562421+00
w28/l32	2026-01-06 14:20:01.562421+00
M	2026-01-06 14:20:01.562421+00
7 m	2026-01-06 14:20:01.562421+00
s	2026-01-06 14:20:01.562421+00
40 x 30	2026-01-06 14:20:01.562421+00
20w medium	2026-01-06 14:20:01.562421+00
32 x 30	2026-01-06 14:20:01.562421+00
29 32	2026-01-06 14:20:01.562421+00
92S	2026-01-06 14:20:01.562421+00
30/34	2026-01-06 14:20:01.562421+00
14 moyen	2026-01-06 14:20:01.562421+00
L	2026-01-06 14:20:01.562421+00
29/32	2026-01-06 14:20:01.562421+00
3XL	2026-01-06 14:20:01.562421+00
 	2026-01-06 14:20:01.562421+00
42/30	2026-01-06 14:20:01.562421+00
30 32	2026-01-06 14:20:01.562421+00
w32 l34	2026-01-06 14:20:01.562421+00
4p medium	2026-01-06 14:20:01.562421+00
32 31	2026-01-06 14:20:01.562421+00
6m	2026-01-06 14:20:01.562421+00
9/10	2026-01-06 14:20:01.562421+00
32 x 31	2026-01-06 14:20:01.562421+00
17	2026-01-06 14:20:01.562421+00
w40 l34	2026-01-06 14:20:01.562421+00
34W 30IN	2026-01-06 14:20:01.562421+00
s/p	2026-01-06 14:20:01.562421+00
6 short	2026-01-06 14:20:01.562421+00
w32/l32 (raccourci)	2026-01-06 14:20:01.562421+00
W29 L33	2026-01-06 14:20:01.562421+00
28 X 32	2026-01-06 14:20:01.562421+00
7	2026-01-06 14:20:01.562421+00
usa 30	2026-01-06 14:20:01.562421+00
4-petite	2026-01-06 14:20:01.562421+00
xxxl	2026-01-06 14:20:01.562421+00
W36/L32	2026-01-06 14:20:01.562421+00
36 x 36	2026-01-06 14:20:01.562421+00
16 m	2026-01-06 14:20:01.562421+00
fr46	2026-01-06 14:20:01.562421+00
w33	2026-01-06 14:20:01.562421+00
W33 L30	2026-01-06 14:20:01.562421+00
w27 l32	2026-01-06 14:20:01.562421+00
28/30	2026-01-06 14:20:01.562421+00
10/12 ans	2026-01-06 14:20:01.562421+00
28-31	2026-01-06 14:20:01.562421+00
42x30	2026-01-06 14:20:01.562421+00
W34 L32	2026-01-06 14:20:01.562421+00
38-30	2026-01-06 14:20:01.562421+00
120	2026-01-06 14:20:01.562421+00
30/32	2026-01-06 14:20:01.562421+00
44 x 29	2026-01-06 14:20:01.562421+00
W30 L32	2026-01-06 14:20:01.562421+00
28-36	2026-01-06 14:20:01.562421+00
W25 L27	2026-01-06 14:20:01.562421+00
14 med	2026-01-06 14:20:01.562421+00
42 x 30	2026-01-06 14:20:01.562421+00
12 PET	2026-01-06 14:20:01.562421+00
36 X 30	2026-01-06 14:20:01.562421+00
18 medium	2026-01-06 14:20:01.562421+00
w32 l32	2026-01-06 14:20:01.562421+00
36 X 32	2026-01-06 14:20:01.562421+00
w44/l30	2026-01-06 14:20:01.562421+00
7 MED	2026-01-06 14:20:01.562421+00
20w	2026-01-06 14:20:01.562421+00
12 long	2026-01-06 14:20:01.562421+00
l/g	2026-01-06 14:20:01.562421+00
w38/l32	2026-01-06 14:20:01.562421+00
30x34	2026-01-06 14:20:01.562421+00
24 W M	2026-01-06 14:20:01.562421+00
34/30	2026-01-06 14:20:01.562421+00
5/27	2026-01-06 14:20:01.562421+00
20	2026-01-06 14:20:01.562421+00
18	2026-01-06 14:20:01.562421+00
W25	2026-01-06 14:20:01.562421+00
30-31	2026-01-06 14:20:01.562421+00
w78/l96 31	2026-01-06 14:20:01.562421+00
sm	2026-01-06 14:20:01.562421+00
damas 6 cortos	2026-01-06 14:20:01.562421+00
w28/l26	2026-01-06 14:20:01.562421+00
fr 42	2026-01-06 14:20:01.562421+00
14 p	2026-01-06 14:20:01.562421+00
10 l/c	2026-01-06 14:20:01.562421+00
16reg	2026-01-06 14:20:01.562421+00
W31	2026-01-06 14:20:01.562421+00
32 X 30	2026-01-06 14:20:01.562421+00
12 petite	2026-01-06 14:20:01.562421+00
32 x 26	2026-01-06 14:20:01.562421+00
40 30	2026-01-06 14:20:01.562421+00
W33/L32	2026-01-06 14:20:01.562421+00
14 P	2026-01-06 14:20:01.562421+00
18 Medium	2026-01-06 14:20:01.562421+00
38 X 29	2026-01-06 14:20:01.562421+00
W87/L86	2026-01-06 14:20:01.562421+00
w29 l31	2026-01-06 14:20:01.562421+00
w33 / l32	2026-01-06 14:20:01.562421+00
23	2026-01-06 14:20:01.562421+00
w36	2026-01-06 14:20:01.562421+00
14	2026-01-06 14:20:01.562421+00
w34/l31	2026-01-06 14:20:01.562421+00
3x large	2026-01-06 14:20:01.562421+00
regular 16	2026-01-06 14:20:01.562421+00
W26 L31	2026-01-06 14:20:01.562421+00
00	2026-01-06 14:20:01.562421+00
30 x 34	2026-01-06 14:20:01.562421+00
31	2026-01-06 14:20:01.562421+00
w28l34	2026-01-06 14:20:01.562421+00
4 petite	2026-01-06 14:20:01.562421+00
6 M	2026-01-06 14:20:01.562421+00
W34 L34	2026-01-06 14:20:01.562421+00
14 long	2026-01-06 14:20:01.562421+00
46 uu	2026-01-06 14:20:01.562421+00
29x30	2026-01-06 14:20:01.562421+00
w29 l33	2026-01-06 14:20:01.562421+00
16P	2026-01-06 14:20:01.562421+00
4 SHORT	2026-01-06 14:20:01.562421+00
10 reg	2026-01-06 14:20:01.562421+00
16p	2026-01-06 14:20:01.562421+00
w32/l34	2026-01-06 14:20:01.562421+00
MEDIUM	2026-01-06 14:20:01.562421+00
18w	2026-01-06 14:20:01.562421+00
size 10 m.	2026-01-06 14:20:01.562421+00
W 34" L 32"	2026-01-06 14:20:01.562421+00
10 MEDIUM	2026-01-06 14:20:01.562421+00
W40 L30	2026-01-06 14:20:01.562421+00
w40 l32	2026-01-06 14:20:01.562421+00
38x34	2026-01-06 14:20:01.562421+00
33/34	2026-01-06 14:20:01.562421+00
16m	2026-01-06 14:20:01.562421+00
79	2026-01-06 14:20:01.562421+00
34x32	2026-01-06 14:20:01.562421+00
w27	2026-01-06 14:20:01.562421+00
w36 w91/h108	2026-01-06 14:20:01.562421+00
w36/l34	2026-01-06 14:20:01.562421+00
w38/l29	2026-01-06 14:20:01.562421+00
eur 36	2026-01-06 14:20:01.562421+00
29x28	2026-01-06 14:20:01.562421+00
w31/l36	2026-01-06 14:20:01.562421+00
w42/l34	2026-01-06 14:20:01.562421+00
w26 l34	2026-01-06 14:20:01.562421+00
w32/l32	2026-01-06 14:20:01.562421+00
32 x 32	2026-01-06 14:20:01.562421+00
w78/h96 w31	2026-01-06 14:20:01.562421+00
11/12 x 34	2026-01-06 14:20:01.562421+00
w31 / 45 italy	2026-01-06 14:20:01.562421+00
w33 /l32	2026-01-06 14:20:01.562421+00
92	2026-01-06 14:20:01.562421+00
14 M	2026-01-06 14:20:01.562421+00
xl 31 inseam	2026-01-06 14:20:01.562421+00
w42/l30	2026-01-06 14:20:01.562421+00
18 P	2026-01-06 14:20:01.562421+00
38 x 30	2026-01-06 14:20:01.562421+00
18 MEDIUM	2026-01-06 14:20:01.562421+00
w34/l32	2026-01-06 14:20:01.562421+00
38 x 34	2026-01-06 14:20:01.562421+00
12 a	2026-01-06 14:20:01.562421+00
w30	2026-01-06 14:20:01.562421+00
40	2026-01-06 14:20:01.562421+00
w28/l30	2026-01-06 14:20:01.562421+00
misses 10 short	2026-01-06 14:20:01.562421+00
W 29	2026-01-06 14:20:01.562421+00
size 34x34	2026-01-06 14:20:01.562421+00
w28	2026-01-06 14:20:01.562421+00
02	2026-01-06 14:20:01.562421+00
35 x 34	2026-01-06 14:20:01.562421+00
14a	2026-01-06 14:20:01.562421+00
W34 L30	2026-01-06 14:20:01.562421+00
w36 l30	2026-01-06 14:20:01.562421+00
33/30	2026-01-06 14:20:01.562421+00
W46	2026-01-06 14:20:01.562421+00
18m	2026-01-06 14:20:01.562421+00
w78/h96	2026-01-06 14:20:01.562421+00
w30 l30	2026-01-06 14:20:01.562421+00
l	2026-01-06 14:20:01.562421+00
xl / 31	2026-01-06 14:20:01.562421+00
14sh	2026-01-06 14:20:01.562421+00
36 x 32	2026-01-06 14:20:01.562421+00
32-30	2026-01-06 14:20:01.562421+00
20 plus short	2026-01-06 14:20:01.562421+00
10 Medium	2026-01-06 14:20:01.562421+00
36 X 34	2026-01-06 14:20:01.562421+00
33 x 32	2026-01-06 14:20:01.562421+00
w30/l32	2026-01-06 14:20:01.562421+00
34-34	2026-01-06 14:20:01.562421+00
w 34 l 34	2026-01-06 14:20:01.562421+00
8 SHORT	2026-01-06 14:20:01.562421+00
w 27 l 32	2026-01-06 14:20:01.562421+00
32 x 34	2026-01-06 14:20:01.562421+00
38 x 29	2026-01-06 14:20:01.562421+00
40/32l	2026-01-06 14:20:01.562421+00
xs	2026-01-06 14:20:01.562421+00
11/12 x 36	2026-01-06 14:20:01.562421+00
32-34	2026-01-06 14:20:01.562421+00
w30/l30	2026-01-06 14:20:01.562421+00
xl l31	2026-01-06 14:20:01.562421+00
W31 L32	2026-01-06 14:20:01.562421+00
12/13y	2026-01-06 14:20:01.562421+00
12 Medium	2026-01-06 14:20:01.562421+00
w34/l30	2026-01-06 14:20:01.562421+00
w28/l34	2026-01-06 14:20:01.562421+00
W29 L32	2026-01-06 14:20:01.562421+00
8p	2026-01-06 14:20:01.562421+00
W36 L30	2026-01-06 14:20:01.562421+00
40/36	2026-01-06 14:20:01.562421+00
W32 L32	2026-01-06 14:20:01.562421+00
33 30	2026-01-06 14:20:01.562421+00
36-32	2026-01-06 14:20:01.562421+00
44 x 30	2026-01-06 14:20:01.562421+00
12 L	2026-01-06 14:20:01.562421+00
10m	2026-01-06 14:20:01.562421+00
5	2026-01-06 14:20:01.562421+00
W28 L33	2026-01-06 14:20:01.562421+00
33 - 34	2026-01-06 14:20:01.562421+00
14w	2026-01-06 14:20:01.562421+00
47	2026-01-06 14:20:01.562421+00
xs/38	2026-01-06 14:20:01.562421+00
w35	2026-01-06 14:20:01.562421+00
l enfant	2026-01-06 14:20:01.562421+00
30/36	2026-01-06 14:20:01.562421+00
w31	2026-01-06 14:20:01.562421+00
14-short	2026-01-06 14:20:01.562421+00
38/30	2026-01-06 14:20:01.562421+00
15 1/2 - 32	2026-01-06 14:20:01.562421+00
10 PET	2026-01-06 14:20:01.562421+00
w32/l29	2026-01-06 14:20:01.562421+00
34/32	2026-01-06 14:20:01.562421+00
w36/l32	2026-01-06 14:20:01.562421+00
w32 l30	2026-01-06 14:20:01.562421+00
30-33	2026-01-06 14:20:01.562421+00
w28/l33	2026-01-06 14:20:01.562421+00
30	2026-01-06 14:20:01.562421+00
W40 L32	2026-01-06 14:20:01.562421+00
w46	2026-01-06 14:20:01.562421+00
w48/l34	2026-01-06 14:20:01.562421+00
36x32	2026-01-06 14:20:01.562421+00
16w	2026-01-06 14:20:01.562421+00
W33 L36	2026-01-06 14:20:01.562421+00
12 MEDIUM	2026-01-06 14:20:01.562421+00
29 w73 h91	2026-01-06 14:20:01.562421+00
w38 l32	2026-01-06 14:20:01.562421+00
w40/l36	2026-01-06 14:20:01.562421+00
w27 l33	2026-01-06 14:20:01.562421+00
18W L	2026-01-06 14:20:01.562421+00
31-32	2026-01-06 14:20:01.562421+00
10 short	2026-01-06 14:20:01.562421+00
w78 h96	2026-01-06 14:20:01.562421+00
W42 L34	2026-01-06 14:20:01.562421+00
31/36	2026-01-06 14:20:01.562421+00
33 X 34	2026-01-06 14:20:01.562421+00
26 / 30	2026-01-06 14:20:01.562421+00
w34 l30	2026-01-06 14:20:01.562421+00
w29	2026-01-06 14:20:01.562421+00
20 husky	2026-01-06 14:20:01.562421+00
w29 l32	2026-01-06 14:20:01.562421+00
38 X 30	2026-01-06 14:20:01.562421+00
w40/l34	2026-01-06 14:20:01.562421+00
16 medium	2026-01-06 14:20:01.562421+00
42 X 30	2026-01-06 14:20:01.562421+00
30-32	2026-01-06 14:20:01.562421+00
xxl	2026-01-06 14:20:01.562421+00
13 x 34	2026-01-06 14:20:01.562421+00
5/6	2026-01-06 14:20:01.562421+00
31 34	2026-01-06 14:20:01.562421+00
w28 l34	2026-01-06 14:20:01.562421+00
34 X 32	2026-01-06 14:20:01.562421+00
40 x 34	2026-01-06 14:20:01.562421+00
misses 10 long	2026-01-06 14:20:01.562421+00
W33/L33	2026-01-06 14:20:01.562421+00
26/31	2026-01-06 14:20:01.562421+00
27	2026-01-06 14:20:01.562421+00
40 x 29	2026-01-06 14:20:01.562421+00
S/P	2026-01-06 14:20:01.562421+00
S/P/CH	2026-01-06 14:20:01.562421+00
w50/l34	2026-01-06 14:20:01.562421+00
38 30	2026-01-06 14:20:01.562421+00
12 x 32	2026-01-06 14:20:01.562421+00
6M	2026-01-06 14:20:01.562421+00
10	2026-01-06 14:20:01.562421+00
w29l34	2026-01-06 14:20:01.562421+00
40fr	2026-01-06 14:20:01.562421+00
s16 / l34	2026-01-06 14:20:01.562421+00
34 X 30	2026-01-06 14:20:01.562421+00
w 32 l 33	2026-01-06 14:20:01.562421+00
32 X 32	2026-01-06 14:20:01.562421+00
W 26 L 32	2026-01-06 14:20:01.562421+00
W31 L34	2026-01-06 14:20:01.562421+00
30 x 30	2026-01-06 14:20:01.562421+00
w48	2026-01-06 14:20:01.562421+00
w30/l34	2026-01-06 14:20:01.562421+00
W40 | FR 50	2026-01-06 14:20:01.562421+00
15/16 x 32	2026-01-06 14:20:01.562421+00
fr 48	2026-01-06 14:20:01.562421+00
24rg	2026-01-06 14:20:01.562421+00
w86/h103	2026-01-06 14:20:01.562421+00
30/30	2026-01-06 14:20:01.562421+00
W30 L31	2026-01-06 14:20:01.562421+00
10P	2026-01-06 14:20:01.562421+00
0	2026-01-06 14:20:01.562421+00
w81/h98 32	2026-01-06 14:20:01.562421+00
w29/l30	2026-01-06 14:20:01.562421+00
w33 l34	2026-01-06 14:20:01.562421+00
W36 L36	2026-01-06 14:20:01.562421+00
w33/l36	2026-01-06 14:20:01.562421+00
W31 L36	2026-01-06 14:20:01.562421+00
w29/l29	2026-01-06 14:20:01.562421+00
eur 34	2026-01-06 14:20:01.562421+00
38X30	2026-01-06 14:20:01.562421+00
36-30	2026-01-06 14:20:01.562421+00
W30 L30	2026-01-06 14:20:01.562421+00
9	2026-01-06 14:20:01.562421+00
18M	2026-01-06 14:20:01.562421+00
w34/l36	2026-01-06 14:20:01.562421+00
34/34	2026-01-06 14:20:01.562421+00
w32/l35	2026-01-06 14:20:01.562421+00
w26/l32	2026-01-06 14:20:01.562421+00
14 l	2026-01-06 14:20:01.562421+00
7/8	2026-01-06 14:20:01.562421+00
18 reg w29/l29	2026-01-06 14:20:01.562421+00
42 eur	2026-01-06 14:20:01.562421+00
46 eu	2026-01-06 14:20:01.562421+00
18W P	2026-01-06 14:20:01.562421+00
m-r	2026-01-06 14:20:01.562421+00
w44m	2026-01-06 14:20:01.562421+00
W30 L34	2026-01-06 14:20:01.562421+00
1/2 x 34	2026-01-06 14:20:01.562421+00
36 34	2026-01-06 14:20:01.562421+00
w42 l32	2026-01-06 14:20:01.562421+00
W28L32	2026-01-06 14:20:01.562421+00
6m w28/l32	2026-01-06 14:20:01.562421+00
W32 L35	2026-01-06 14:20:01.562421+00
17/18	2026-01-06 14:20:01.562421+00
w36/l30	2026-01-06 14:20:01.562421+00
40 X 32	2026-01-06 14:20:01.562421+00
w50/l30	2026-01-06 14:20:01.562421+00
16 SLM	2026-01-06 14:20:01.562421+00
32 w81 h98	2026-01-06 14:20:01.562421+00
36 32	2026-01-06 14:20:01.562421+00
29 x 32	2026-01-06 14:20:01.562421+00
20W P	2026-01-06 14:20:01.562421+00
14p	2026-01-06 14:20:01.562421+00
34 x 36	2026-01-06 14:20:01.562421+00
14/32	2026-01-06 14:20:01.562421+00
36/32	2026-01-06 14:20:01.562421+00
12m	2026-01-06 14:20:01.562421+00
82	2026-01-06 14:20:01.562421+00
w38 l30	2026-01-06 14:20:01.562421+00
12 husky	2026-01-06 14:20:01.562421+00
9/10 x 34	2026-01-06 14:20:01.562421+00
12 SHORT	2026-01-06 14:20:01.562421+00
3xl femme	2026-01-06 14:20:01.562421+00
w30 l34	2026-01-06 14:20:01.562421+00
s/m	2026-01-06 14:20:01.562421+00
38 x 32	2026-01-06 14:20:01.562421+00
50	2026-01-06 14:20:01.562421+00
48 x 30	2026-01-06 14:20:01.562421+00
16-16½ 34/35	2026-01-06 14:20:01.562421+00
w31/l30	2026-01-06 14:20:01.562421+00
xl/ 31	2026-01-06 14:20:01.562421+00
29 X 30	2026-01-06 14:20:01.562421+00
1	2026-01-06 14:20:01.562421+00
16 SHORT	2026-01-06 14:20:01.562421+00
11/12 x34	2026-01-06 14:20:01.562421+00
f	2026-01-06 14:20:01.562421+00
16 MEDIUM	2026-01-06 14:20:01.562421+00
28/32	2026-01-06 14:20:01.562421+00
26-36	2026-01-06 14:20:01.562421+00
14 SLIM	2026-01-06 14:20:01.562421+00
16 s	2026-01-06 14:20:01.562421+00
w46/l34	2026-01-06 14:20:01.562421+00
w31/l32	2026-01-06 14:20:01.562421+00
W34 L36	2026-01-06 14:20:01.562421+00
6	2026-01-06 14:20:01.562421+00
7 medium	2026-01-06 14:20:01.562421+00
w38 l36	2026-01-06 14:20:01.562421+00
4xl	2026-01-06 14:20:01.562421+00
W35 L34	2026-01-06 14:20:01.562421+00
small	2026-01-06 14:20:01.562421+00
w31/l35	2026-01-06 14:20:01.562421+00
33	2026-01-06 14:20:01.562421+00
1m	2026-01-06 14:20:01.562421+00
6s	2026-01-06 14:20:01.562421+00
37	2026-01-06 14:20:01.562421+00
w9/l29	2026-01-06 14:20:01.562421+00
14m	2026-01-06 14:20:01.562421+00
34 x 32	2026-01-06 14:20:01.562421+00
W25 L33	2026-01-06 14:20:01.562421+00
12 m	2026-01-06 14:20:01.562421+00
34x34	2026-01-06 14:20:01.562421+00
18 M	2026-01-06 14:20:01.562421+00
14 PET	2026-01-06 14:20:01.562421+00
31 w78/h96	2026-01-06 14:20:01.562421+00
w29/l32	2026-01-06 14:20:01.562421+00
w42/l32	2026-01-06 14:20:01.562421+00
29 w78 h91	2026-01-06 14:20:01.562421+00
30x30	2026-01-06 14:20:01.562421+00
w27/l33	2026-01-06 14:20:01.562421+00
w50/l32	2026-01-06 14:20:01.562421+00
w30/l33	2026-01-06 14:20:01.562421+00
w56/l32	2026-01-06 14:20:01.562421+00
14r	2026-01-06 14:20:01.562421+00
40x32	2026-01-06 14:20:01.562421+00
33 x 30	2026-01-06 14:20:01.562421+00
32 32	2026-01-06 14:20:01.562421+00
36/34	2026-01-06 14:20:01.562421+00
36	2026-01-06 14:20:01.562421+00
W36 L32	2026-01-06 14:20:01.562421+00
35 34	2026-01-06 14:20:01.562421+00
15/32	2026-01-06 14:20:01.562421+00
10r	2026-01-06 14:20:01.562421+00
10 pet	2026-01-06 14:20:01.562421+00
24w	2026-01-06 14:20:01.562421+00
w46/l32	2026-01-06 14:20:01.562421+00
36x34	2026-01-06 14:20:01.562421+00
w44/l34	2026-01-06 14:20:01.562421+00
0r	2026-01-06 14:20:01.562421+00
22	2026-01-06 14:20:01.562421+00
w36 l34	2026-01-06 14:20:01.562421+00
w33/l30	2026-01-06 14:20:01.562421+00
3	2026-01-06 14:20:01.562421+00
w48/l32	2026-01-06 14:20:01.562421+00
32	2026-01-06 14:20:01.562421+00
W31 L30	2026-01-06 14:20:01.562421+00
38 us	2026-01-06 14:20:01.562421+00
30X32	2026-01-06 14:20:01.562421+00
w29/l33	2026-01-06 14:20:01.562421+00
W38 L34	2026-01-06 14:20:01.562421+00
38x30	2026-01-06 14:20:01.562421+00
w33/30	2026-01-06 14:20:01.562421+00
40/32	2026-01-06 14:20:01.562421+00
32 34	2026-01-06 14:20:01.562421+00
33 34	2026-01-06 14:20:01.562421+00
26	2026-01-06 14:20:01.562421+00
t28	2026-01-06 14:20:01.562421+00
38 X 32	2026-01-06 14:20:01.562421+00
35 X 34	2026-01-06 14:20:01.562421+00
13	2026-01-06 14:20:01.562421+00
42uu	2026-01-06 14:20:01.562421+00
16 long	2026-01-06 14:20:01.562421+00
t42	2026-01-06 14:20:01.562421+00
W26 L32	2026-01-06 14:20:01.562421+00
10 m	2026-01-06 14:20:01.562421+00
41	2026-01-06 14:20:01.562421+00
38	2026-01-06 14:20:01.562421+00
16 husky	2026-01-06 14:20:01.562421+00
eur 38	2026-01-06 14:20:01.562421+00
W25 L32	2026-01-06 14:20:01.562421+00
5/6r	2026-01-06 14:20:01.562421+00
w36 l32	2026-01-06 14:20:01.562421+00
34	2026-01-06 14:20:01.562421+00
w34/l33	2026-01-06 14:20:01.562421+00
xl	2026-01-06 14:20:01.562421+00
24	2026-01-06 14:20:01.562421+00
28	2026-01-06 14:20:01.562421+00
16 M	2026-01-06 14:20:01.562421+00
29x32	2026-01-06 14:20:01.562421+00
34 X 34	2026-01-06 14:20:01.562421+00
31x34	2026-01-06 14:20:01.562421+00
6 petite	2026-01-06 14:20:01.562421+00
8	2026-01-06 14:20:01.562421+00
42 x 32	2026-01-06 14:20:01.562421+00
42	2026-01-06 14:20:01.562421+00
w71/h88 w28	2026-01-06 14:20:01.562421+00
w33/l32	2026-01-06 14:20:01.562421+00
W-32 L-32	2026-01-06 14:20:01.562421+00
8 Petite	2026-01-06 14:20:01.562421+00
W 29 L 32	2026-01-06 14:20:01.562421+00
eur 40 / us 8 / ca 8 / cn 170/76a / mx 8	2026-01-06 14:20:01.562421+00
16	2026-01-06 14:20:01.562421+00
4M	2026-01-06 14:20:01.562421+00
w40/l32	2026-01-06 14:20:01.562421+00
9 med.	2026-01-06 14:20:01.562421+00
12	2026-01-06 14:20:01.562421+00
w40/l28	2026-01-06 14:20:01.562421+00
16 tall	2026-01-06 14:20:01.562421+00
w32/l30	2026-01-06 14:20:01.562421+00
W38 L32	2026-01-06 14:20:01.562421+00
16 short	2026-01-06 14:20:01.562421+00
2XL	2026-01-06 14:20:01.562421+00
35 x 32	2026-01-06 14:20:01.562421+00
5 x 38	2026-01-06 14:20:01.562421+00
16 P	2026-01-06 14:20:01.562421+00
w35 l34	2026-01-06 14:20:01.562421+00
w31/l34	2026-01-06 14:20:01.562421+00
12 LONG	2026-01-06 14:20:01.562421+00
w33/l34	2026-01-06 14:20:01.562421+00
160	2026-01-06 14:20:01.562421+00
34 x 30	2026-01-06 14:20:01.562421+00
w30 l32	2026-01-06 14:20:01.562421+00
3xl	2026-01-06 14:20:01.562421+00
w38/l30	2026-01-06 14:20:01.562421+00
28-32	2026-01-06 14:20:01.562421+00
28 33	2026-01-06 14:20:01.562421+00
w32	2026-01-06 14:20:01.562421+00
42x29	2026-01-06 14:20:01.562421+00
w27/32	2026-01-06 14:20:01.562421+00
38-34	2026-01-06 14:20:01.562421+00
35	2026-01-06 14:20:01.562421+00
14 SHORT	2026-01-06 14:20:01.562421+00
4	2026-01-06 14:20:01.562421+00
40-34	2026-01-06 14:20:01.562421+00
w30 (raccourci)	2026-01-06 14:20:01.562421+00
W32 L30	2026-01-06 14:20:01.562421+00
40 x 32	2026-01-06 14:20:01.562421+00
w38/l36	2026-01-06 14:20:01.562421+00
XXL	2026-01-06 14:20:01.562421+00
w40	2026-01-06 14:20:01.562421+00
w28/l28	2026-01-06 14:20:01.562421+00
XL	2026-01-06 14:20:01.562421+00
27 x 30	2026-01-06 14:20:01.562421+00
27-4	2026-01-06 14:20:01.562421+00
38 X 34	2026-01-06 14:20:01.562421+00
14a / l enfant	2026-01-06 14:20:01.562421+00
W-30	2026-01-06 14:20:01.562421+00
lt	2026-01-06 14:20:01.562421+00
eur 40, usa 10	2026-01-06 14:20:01.562421+00
18 short	2026-01-06 14:20:01.562421+00
18W MEDIUM	2026-01-06 14:20:01.562421+00
28/31	2026-01-06 14:20:01.562421+00
30 x 36	2026-01-06 14:20:01.562421+00
W30/L32	2026-01-06 14:20:01.562421+00
\.



COPY product_attributes.sleeve_lengths (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
3/4 sleeve	Manches 3/4	3/4-Arm	Manica 3/4	Manga 3/4	3/4 mouw	Rękaw 3/4
Long sleeve	Manches longues	Langarm	Manica lunga	Manga larga	Lange mouw	Długi rękaw
Short sleeve	Manches courtes	Kurzarm	Manica corta	Manga corta	Korte mouw	Krótki rękaw
Sleeveless	Sans manches	Ärmellos	Senza maniche	Sin mangas	Mouwloos	Bez rękawów
\.



COPY product_attributes.sports (name_en, name_fr, description, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
American football	Football américain	\N	American Football	Football americano	Fútbol americano	American football	Futbol amerykański
Baseball	Baseball	\N	Baseball	Baseball	Béisbol	Honkbal	Baseball
Basketball	Basketball	\N	Basketball	Basket	Baloncesto	Basketbal	Koszykówka
Boxing	Boxe	\N	Boxen	Boxe	Boxeo	Boksen	Boks
Climbing	Escalade	\N	Klettern	Arrampicata	Escalada	Klimmen	Wspinaczka
Crossfit	Crossfit	\N	Crossfit	Crossfit	Crossfit	Crossfit	Crossfit
Cycling	Cyclisme	\N	Radsport	Ciclismo	Ciclismo	Wielrennen	Kolarstwo
Dance	Danse	\N	Tanz	Danza	Baile	Dans	Taniec
Equestrian	Équitation	\N	Reitsport	Equitazione	Equitación	Paardrijden	Jeździectwo
Fitness	Fitness	\N	Fitness	Fitness	Fitness	Fitness	Fitness
Football/soccer	Football	\N	Fußball	Calcio	Fútbol	Voetbal	Piłka nożna
Golf	Golf	\N	Golf	Golf	Golf	Golf	Golf
Gymnastics	Gymnastique	\N	Turnen	Ginnastica	Gimnasia	Gymnastiek	Gimnastyka
Hiking	Randonnée	\N	Wandern	Escursionismo	Senderismo	Wandelen	Turystyka piesza
Hockey	Hockey	\N	Hockey	Hockey	Hockey	Hockey	Hokej
Martial arts	Arts martiaux	\N	Kampfsport	Arti marziali	Artes marciales	Vechtsporten	Sztuki walki
Motorsport	Sport automobile	\N	Motorsport	Motorsport	Automovilismo	Autosport	Sporty motorowe
Pilates	Pilates	\N	Pilates	Pilates	Pilates	Pilates	Pilates
Rugby	Rugby	\N	Rugby	Rugby	Rugby	Rugby	Rugby
Running	Course à pied	\N	Laufen	Corsa	Running	Hardlopen	Bieganie
Skateboarding	Skateboard	\N	Skateboarding	Skateboard	Skateboard	Skateboarden	Skateboarding
Ski	Ski	\N	Ski	Sci	Esquí	Skiën	Narciarstwo
Snowboard	Snowboard	\N	Snowboard	Snowboard	Snowboard	Snowboard	Snowboard
Surfing	Surf	\N	Surfen	Surf	Surf	Surfen	Surfing
Swimming	Natation	\N	Schwimmen	Nuoto	Natación	Zwemmen	Pływanie
Tennis	Tennis	\N	Tennis	Tennis	Tenis	Tennis	Tenis
Volleyball	Volleyball	\N	Volleyball	Pallavolo	Voleibol	Volleybal	Siatkówka
Yoga	Yoga	\N	Yoga	Yoga	Yoga	Yoga	Joga
\.



COPY product_attributes.stretches (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
No stretch	Aucun stretch	Kein stretch	Nessun stretch	Sin elasticidad	Geen stretch	Bez Rozciągliwości
Slight stretch	Léger stretch	Leichter stretch	Leggero stretch	elasticidad Ligera	Lichte stretch	Lekka rozciągliwość
Moderate stretch	stretch Modéré	Mäßiger stretch	stretch Moderato	elasticidad Moderada	Matige stretch	Umiarkowana rozciągliwość
Super stretch	Super stretch	Super stretch	Super stretch	Super elasticidad	Super stretch	Super rozciągliwość
\.



COPY product_attributes.trends (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
Athleisure	Athleisure	Athleisure	Athleisure	Athleisure	Athleisure	Athleisure
Bohemian	Bohème	Bohemian	Bohémien	Bohemio	Bohemian	Bohema
Cottagecore	Cottagecore	Cottagecore	Cottagecore	Cottagecore	Cottagecore	Cottagecore
Dark academia	Dark academia	Dark Academia	Dark academia	Dark academia	Dark academia	Dark academia
Geek chic	Geek chic	Geek Chic	Geek chic	Geek chic	Geek chic	Geek chic
Gothic	Gothique	Gothic	Gotico	Gótico	Gothic	Gotycki
Grunge	Grunge	Grunge	Grunge	Grunge	Grunge	Grunge
Japanese streetwear	Streetwear japonais	Japanese Streetwear	Streetwear giapponese	Streetwear japonés	Japanse streetwear	Japoński streetwear
Minimalist	Minimaliste	Minimalistisch	Minimalista	Minimalista	Minimalistisch	Minimalistyczny
Modern	Moderne	Modern	Moderno	Moderno	Modern	Nowoczesny
Normcore	Normcore	Normcore	Normcore	Normcore	Normcore	Normcore
Preppy	Preppy	Preppy	Preppy	Preppy	Preppy	Preppy
Punk	Punk	Punk	Punk	Punk	Punk	Punk
Retro	Rétro	Retro	Retrò	Retro	Retro	Retro
Skater	Skater	Skater	Skater	Skater	Skater	Skater
Sportswear	Sportswear	Sportswear	Sportswear	Sportswear	Sportswear	Sportswear
Streetwear	Streetwear	Streetwear	Streetwear	Streetwear	Streetwear	Streetwear
Techwear	Techwear	Techwear	Techwear	Techwear	Techwear	Techwear
Vintage	Vintage	Vintage	Vintage	Vintage	Vintage	Vintage
Western	Western	Western	Western	Western	Western	Western
Workwear	Workwear	Workwear	Workwear	Workwear	Workwear	Workwear
Y2k	Y2K	Y2K	Y2K	Y2K	Y2K	Y2K
Old money	Old money	Old Money	Old money	Old money	Old money	Old money
Quiet luxury	Quiet luxury	Quiet Luxury	Quiet luxury	Quiet luxury	Quiet luxury	Quiet luxury
Coquette	Coquette	Coquette	Coquette	Coquette	Coquette	Coquette
Clean girl	Clean girl	Clean Girl	Clean girl	Clean girl	Clean girl	Clean girl
Light academia	Light academia	Light Academia	Light academia	Light academia	Light academia	Light academia
Balletcore	Balletcore	Balletcore	Balletcore	Balletcore	Balletcore	Balletcore
Gorpcore	Gorpcore	Gorpcore	Gorpcore	Gorpcore	Gorpcore	Gorpcore
Boho revival	Boho revival	Boho Revival	Boho revival	Boho revival	Boho revival	Boho revival
Downtown girl	Downtown girl	Downtown Girl	Downtown girl	Downtown girl	Downtown girl	Downtown girl
Eclectic grandpa	Eclectic grandpa	Eclectic Grandpa	Eclectic grandpa	Eclectic grandpa	Eclectic grandpa	Eclectic grandpa
Glamoratti	Glamoratti	Glamoratti	Glamoratti	Glamoratti	Glamoratti	Glamoratti
Indie sleaze	Indie sleaze	Indie Sleaze	Indie sleaze	Indie sleaze	Indie sleaze	Indie sleaze
Khaki coded	Khaki coded	Khaki Coded	Khaki coded	Khaki coded	Khaki coded	Khaki coded
Mob wife	Mob wife	Mob Wife	Mob wife	Mob wife	Mob wife	Mob wife
Neo deco	Néo déco	Neo Deco	Neo deco	Neo deco	Neo deco	Neo deco
Office siren	Office siren	Office Siren	Office siren	Office siren	Office siren	Office siren
Poetcore	Poetcore	Poetcore	Poetcore	Poetcore	Poetcore	Poetcore
Vamp romance	Vamp romance	Vamp Romance	Vamp romance	Vamp romance	Vamp romance	Vamp romance
Wilderkind	Wilderkind	Wilderkind	Wilderkind	Wilderkind	Wilderkind	Wilderkind
\.



COPY product_attributes.unique_features (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
Cutouts	Découpes	Cutouts	Tagli	Aberturas	Cutouts	Wycięcia
Fringe	Franges	Fransen	Frange	Flecos	Franjes	Frędzle
Tiered	Volants superposés	Gestuft	A balze	Escalonado	Gelaagd	Warstwowy
Distressed	Vieilli	Distressed	Effetto vissuto	Desgastado	Distressed	Postarzany
Acid wash	Délavage acide	Acid Wash	Lavaggio acido	Lavado ácido	Acid wash	Sprany kwasem
Appliqué	Appliqué	Applikation	Applicazione	Aplique	Applicatie	Aplikacja
Bar tacks	Points d'arrêt	Riegelstiche	Punti di rinforzo	Presillas	Bartacks	Rygle
Beaded	Perlé	Perlenbesetzt	Con perline	Con cuentas	Met kralen	Zdobiony koralikami
Belt loops	Passants de ceinture	Gürtelschlaufen	Passanti	Trabillas	Riemlussen	Szlufki
Bleached	Blanchi	Gebleicht	Sbiancato	Blanqueado	Gebleekt	Wybielany
Brass rivets	Rivets en laiton	Messingnieten	Rivetti in ottone	Remaches de latón	Messing klinknagels	Nity mosiężne
Button detail	Détail boutons	Knopfdetail	Dettaglio bottoni	Detalle de botones	Knoopdetail	Detal guzikowy
Chain detail	Détail chaîne	Kettendetail	Dettaglio catena	Detalle de cadena	Kettingdetail	Detal łańcuszkowy
Chain stitching	Couture chaînette	Kettenstich	Cucitura a catenella	Puntada de cadena	Kettingsteek	Ścieg łańcuszkowy
Coin pocket	Poche à monnaie	Münztasche	Taschino portamonete	Bolsillo monedero	Muntzakje	Kieszonka na monety
Contrast stitching	Surpiqûres contrastées	Kontrastnähte	Cuciture a contrasto	Costuras en contraste	Contrasterende stiksels	Kontrastowe przeszycia
Copper rivets	Rivets en cuivre	Kupfernieten	Rivetti in rame	Remaches de cobre	Koperen klinknagels	Nity miedziane
Cuffed	Revers	Mit Umschlag	Con risvolto	Con dobladillo	Met omslag	Z mankietem
Custom design	Design personnalisé	Individuelles Design	Design personalizzato	Diseño personalizado	Custom design	Własny design
Darted	Pinces	Mit Abnähern	Con pince	Con pinzas	Met figuurnaad	Z zaszewkami
Deadstock fabric	Tissu deadstock	Deadstock-Stoff	Tessuto deadstock	Tejido deadstock	Deadstock stof	Tkanina deadstock
Decorative pockets	Poches décoratives	Ziertaschen	Tasche decorative	Bolsillos decorativos	Decoratieve zakken	Kieszenie dekoracyjne
Double stitch	Double couture	Doppelnaht	Doppia cucitura	Doble puntada	Dubbele steek	Podwójny szew
Embossed buttons	Boutons embossés	Geprägte Knöpfe	Bottoni in rilievo	Botones en relieve	Reliëfknopen	Guziki tłoczone
Embroidered	Brodé	Bestickt	Ricamato	Bordado	Geborduurd	Haftowany
Fading	Délavage	Verblassung	Sbiadito	Desvanecido	Vervaagd	Sprane
Flat felled seams	Coutures rabattues	Kappnähte	Cuciture ribattute	Costuras planas	Platte naden	Szwy płaskie
Frayed	Effiloché	Ausgefranst	Sfilacciato	Deshilachado	Gerafeld	Postrzępiony
Garment dyed	Teinture pièce	Stückgefärbt	Tinto in capo	Teñido en prenda	Garment dyed	Barwiony po uszyciu
Gradient	Dégradé	Farbverlauf	Sfumato	Degradado	Verloop	Gradient
Hand embroidered	Brodé main	Handbestickt	Ricamato a mano	Bordado a mano	Handgeborduurd	Haftowany ręcznie
Hand painted	Peint main	Handbemalt	Dipinto a mano	Pintado a mano	Handgeschilderd	Malowany ręcznie
Hidden rivets	Rivets cachés	Verdeckte Nieten	Rivetti nascosti	Remaches ocultos	Verborgen klinknagels	Ukryte nity
Jacron patch	Patch Jacron	Jacron-Patch	Patch Jacron	Parche Jacron	Jacron patch	Naszywka Jacron
Lace detail	Détail dentelle	Spitzendetail	Dettaglio pizzo	Detalle de encaje	Kantdetail	Detal koronkowy
Leather label	Étiquette cuir	Lederetikett	Etichetta in pelle	Etiqueta de cuero	Leren label	Skórzana metka
Leather patch	Patch cuir	Lederpatch	Patch in pelle	Parche de cuero	Leren patch	Skórzana łata
Lined	Doublé	Gefüttert	Foderato	Forrado	Gevoerd	Podszewka
Original buttons	Boutons d'origine	Originalknöpfe	Bottoni originali	Botones originales	Originele knopen	Oryginalne guziki
Padded	Rembourré	Gepolstert	Imbottito	Acolchado	Gewatteerd	Ocieplany
Painted	Peint	Bemalt	Dipinto	Pintado	Beschilderd	Malowany
Paneled	Panneaux	Mit Einsätzen	A pannelli	Con paneles	Met panelen	Panelowy
Paper patch	Patch papier	Papierpatch	Patch in carta	Parche de papel	Papieren patch	Papierowa naszywka
Patchwork	Patchwork	Patchwork	Patchwork	Patchwork	Patchwork	Patchwork
Pleated	Plissé	Plissiert	Plissettato	Plisado	Geplisseerd	Plisowany
Printed	Imprimé	Bedruckt	Stampato	Estampado	Bedrukt	Nadrukowany
Raw denim	Denim brut	Raw Denim	Denim grezzo	Denim crudo	Raw denim	Surowy denim
Raw hem	Ourlet brut	Offener Saum	Orlo grezzo	Dobladillo sin rematar	Onafgewerkte zoom	Surowy rąbek
Reinforced seams	Coutures renforcées	Verstärkte Nähte	Cuciture rinforzate	Costuras reforzadas	Versterkte naden	Wzmocnione szwy
Ripped	Déchiré	Zerrissen	Strappato	Rasgado	Gescheurd	Podarty
Rope dyed	Teinture corde	Rope Dyed	Tintura a corda	Teñido en cuerda	Rope dyed	Barwiony na linie
Sanforized	Sanforisé	Sanforisiert	Sanforizzato	Sanforizado	Gesanforiseerd	Sanforyzowany
Selvedge	Selvedge	Selvedge	Cimosa	Selvedge	Selvedge	Selvedge
Sequined	À sequins	Mit Pailletten	Con paillettes	Con lentejuelas	Met pailletten	Z cekinami
Shuttle loom	Métier navette	Schiffchenwebstuhl	Telaio a navetta	Telar de lanzadera	Schietspoel weefgetouw	Krosno czółenkowe
Single stitch	Simple couture	Einzelnaht	Cucitura singola	Puntada simple	Enkele steek	Pojedynczy szew
Stone washed	Stone washed	Stone Washed	Stone washed	Lavado a la piedra	Stone washed	Prany z kamieniami
Studded	Clouté	Mit Nieten	Borchiato	Con tachuelas	Met studs	Ćwiekowany
Triple stitch	Triple couture	Dreifachnaht	Tripla cucitura	Triple puntada	Drievoudige steek	Potrójny szew
Unsanforized	Non sanforisé	Unsanforisiert	Non sanforizzato	Sin sanforizar	Ongesanforiseerd	Niesanforyzowany
Vintage hardware	Quincaillerie vintage	Vintage-Beschläge	Ferramenta vintage	Herrajes vintage	Vintage hardware	Vintage okucia
Vintage wash	Lavage vintage	Vintage Wash	Lavaggio vintage	Lavado vintage	Vintage wash	Pranie vintage
Whiskering	Moustaches	Whiskers	Baffature	Bigotes	Whiskering	Wąsy
Woven label	Étiquette tissée	Gewebtes Etikett	Etichetta tessuta	Etiqueta tejida	Geweven label	Tkana metka
Zipper detail	Détail fermeture	Reißverschlussdetail	Dettaglio cerniera	Detalle de cremallera	Ritsdetail	Detal zamkowy
\.



COPY public.admin_audit_logs (id, admin_id, action, resource_type, resource_id, resource_name, details, ip_address, user_agent, created_at) FROM stdin;
1	1	UPDATE	user	1	plugin-test2@stoflow.com	null	127.0.0.1	Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0	2026-01-07 21:53:19.353984+00
\.



COPY public.ai_credits (id, user_id, ai_credits_purchased, ai_credits_used_this_month, last_reset_date, created_at, updated_at) FROM stdin;
1	1	0	15	2026-01-07 20:23:26.982625+00	2025-12-23 13:37:49.936427+00	2026-01-07 21:23:05.593664+00
\.



COPY public.alembic_version (version_num) FROM stdin;
9e1b5d86d3ec
\.



COPY public.clothing_prices (brand, category, base_price, updated_at) FROM stdin;
\.



COPY public.doc_articles (id, category_id, slug, title, summary, content, display_order, is_active, created_at, updated_at) FROM stdin;
1	1	premiers-pas	Premiers pas avec Stoflow	Découvrez comment démarrer avec Stoflow et configurer votre compte.	# Premiers pas avec Stoflow\n\nBienvenue sur Stoflow ! Ce guide vous accompagne dans vos premiers pas.\n\n## 1. Créer votre compte\n\nRendez-vous sur la page d'inscription et remplissez le formulaire avec vos informations.\n\n## 2. Connecter votre première marketplace\n\nUne fois connecté, accédez à **Paramètres > Intégrations** pour connecter Vinted, eBay ou Etsy.\n\n## 3. Créer votre premier produit\n\nCliquez sur **Produits > Créer un produit** pour ajouter votre premier article.\n\n---\n\nBesoin d'aide ? Consultez notre FAQ ou contactez notre support.	0	t	2025-12-24 09:45:30.062696+00	2025-12-24 09:45:30.062696+00
2	1	creer-produit	Comment créer un produit	Apprenez à créer et publier vos produits sur les marketplaces.	# Comment créer un produit\n\nCe guide vous explique comment créer un produit dans Stoflow.\n\n## Étape 1 : Informations de base\n\n- **Titre** : Le nom de votre produit\n- **Description** : Une description détaillée\n- **Prix** : Le prix de vente\n\n## Étape 2 : Photos\n\nAjoutez jusqu'à 10 photos de votre produit. La première photo sera la photo principale.\n\n## Étape 3 : Attributs\n\nSélectionnez la catégorie, la taille, la couleur et les autres attributs.\n\n## Étape 4 : Publication\n\nCliquez sur **Publier** pour envoyer votre produit sur les marketplaces connectées.	1	t	2025-12-24 09:45:30.062696+00	2025-12-24 09:45:30.062696+00
3	2	abonnement	Questions sur les abonnements	Tout savoir sur les plans et tarifs Stoflow.	# Questions sur les abonnements\n\n## Quels sont les plans disponibles ?\n\nStoflow propose 4 plans :\n- **Gratuit** : Pour découvrir la plateforme (50 produits, 1 marketplace)\n- **Pro** : Pour les vendeurs actifs (500 produits, toutes marketplaces)\n- **Business** : Pour les professionnels (2000 produits)\n- **Enterprise** : Pour les grandes équipes (illimité)\n\n## Puis-je changer de plan ?\n\nOui, vous pouvez upgrader ou downgrader à tout moment depuis **Paramètres > Abonnement**.\n\n## Comment fonctionne la facturation ?\n\nLa facturation est mensuelle ou annuelle (avec 20% de réduction).	0	t	2025-12-24 09:45:30.062696+00	2025-12-24 09:45:30.062696+00
4	1	connecter-vinted	Connecter votre compte Vinted	Apprenez à connecter votre compte Vinted à Stoflow pour synchroniser vos produits.	# Connecter votre compte Vinted\n\n## Introduction\n\nConnecter votre compte Vinted à Stoflow vous permet de :\n- Synchroniser automatiquement vos articles\n- Gérer vos prix depuis une interface unique\n- Suivre vos ventes et statistiques\n\n## Étapes de connexion\n\n### 1. Installer l'extension navigateur\n\nTéléchargez et installez l'extension Stoflow pour votre navigateur :\n- **Firefox** : [Lien vers Firefox Add-ons]\n- **Chrome** : [Lien vers Chrome Web Store]\n\n### 2. Se connecter à Vinted\n\n1. Ouvrez Vinted dans votre navigateur\n2. Connectez-vous à votre compte Vinted\n3. L'extension détectera automatiquement votre session\n\n### 3. Lier à Stoflow\n\n1. Allez dans **Paramètres > Intégrations** dans Stoflow\n2. Cliquez sur "Connecter Vinted"\n3. Suivez les instructions à l'écran\n\n## Dépannage\n\n### L'extension ne détecte pas ma session\n\n- Assurez-vous d'être connecté à Vinted\n- Essayez de rafraîchir la page\n- Redémarrez votre navigateur\n\n### Erreur de synchronisation\n\n- Vérifiez votre connexion internet\n- Réessayez dans quelques minutes\n- Contactez le support si le problème persiste	2	t	2025-12-24 10:07:51.340398+00	2025-12-24 10:07:51.340398+00
5	1	publier-produits	Publier vos produits sur Vinted	Guide complet pour publier vos produits Stoflow sur la marketplace Vinted.	# Publier vos produits sur Vinted\n\n## Prérequis\n\nAvant de publier, assurez-vous que :\n- Votre compte Vinted est connecté\n- Votre produit est complet (photos, description, prix)\n- Le produit est en statut "Brouillon"\n\n## Publication individuelle\n\n### Depuis la fiche produit\n\n1. Ouvrez la fiche du produit\n2. Cliquez sur "Publier sur Vinted"\n3. Vérifiez les informations\n4. Confirmez la publication\n\n### Depuis la liste des produits\n\n1. Sélectionnez le produit\n2. Menu Actions > "Publier sur Vinted"\n\n## Publication en masse\n\n### Sélectionner plusieurs produits\n\n1. Cochez les produits à publier\n2. Cliquez sur "Actions groupées"\n3. Sélectionnez "Publier sur Vinted"\n\n### Limites\n\n- Maximum 50 produits par lot\n- Les produits incomplets seront ignorés\n- Un rapport vous sera envoyé après publication\n\n## Statuts de publication\n\n| Statut | Description |\n|--------|-------------|\n| Brouillon | Produit non publié |\n| En cours | Publication en cours |\n| Publié | Visible sur Vinted |\n| Erreur | Échec de publication |\n\n## Bonnes pratiques\n\n1. **Photos de qualité** : Minimum 3 photos par produit\n2. **Description détaillée** : Incluez matière, taille, état\n3. **Prix compétitif** : Vérifiez les prix du marché\n4. **Catégorie précise** : Aide à la visibilité	3	t	2025-12-24 10:07:51.340398+00	2025-12-24 10:07:51.340398+00
6	1	gerer-prix	Gérer les prix de vos produits	Découvrez comment optimiser vos prix avec les outils Stoflow.	# Gérer les prix de vos produits\n\n## Prix de base vs Prix Vinted\n\nStoflow vous permet de définir :\n- **Prix de base** : Votre prix de référence\n- **Prix Vinted** : Prix affiché sur Vinted (peut inclure des ajustements)\n\n## Modification de prix\n\n### Prix individuel\n\n1. Ouvrez la fiche produit\n2. Modifiez le champ "Prix"\n3. Le prix Vinted sera automatiquement mis à jour\n\n### Modification en masse\n\n1. Sélectionnez les produits\n2. Actions > "Modifier les prix"\n3. Choisissez une méthode :\n   - **Montant fixe** : +/- X€\n   - **Pourcentage** : +/- X%\n   - **Prix fixe** : Définir un nouveau prix\n\n## Stratégies de prix\n\n### Prix rond\n\nStoflow peut arrondir automatiquement vos prix :\n- 19.90€ au lieu de 19.87€\n- 25.00€ au lieu de 24.73€\n\n### Prix psychologique\n\nOption pour finir les prix en :\n- `.99` (ex: 19.99€)\n- `.90` (ex: 19.90€)\n- `.00` (ex: 20.00€)\n\n## Alertes de prix\n\nConfigurez des alertes pour :\n- Prix inférieur à un seuil\n- Marge trop faible\n- Prix concurrent détecté\n\n## Historique des prix\n\nConsultez l'évolution de vos prix dans l'onglet "Historique" de chaque produit.	4	t	2025-12-24 10:07:51.340398+00	2025-12-24 10:07:51.340398+00
7	1	utiliser-ia	Utiliser l'assistant IA	Comment l'intelligence artificielle de Stoflow peut vous aider à optimiser vos annonces.	# Utiliser l'assistant IA\n\n## Fonctionnalités IA\n\nStoflow intègre une intelligence artificielle pour vous aider à :\n- Générer des descriptions\n- Suggérer des prix\n- Optimiser vos photos\n- Catégoriser automatiquement\n\n## Génération de descriptions\n\n### Comment ça marche\n\n1. Ajoutez vos photos\n2. Cliquez sur "Générer description"\n3. L'IA analyse vos images\n4. Une description est proposée\n\n### Personnaliser le résultat\n\nVous pouvez ajuster :\n- Le ton (professionnel, décontracté, détaillé)\n- La longueur (courte, moyenne, longue)\n- Les mots-clés à inclure\n\n## Suggestions de prix\n\n### Analyse du marché\n\nL'IA analyse :\n- Prix des articles similaires sur Vinted\n- Tendances du marché\n- État de l'article\n\n### Fourchette de prix\n\nVous recevez une suggestion avec :\n- Prix minimum recommandé\n- Prix optimal\n- Prix maximum\n\n## Catégorisation automatique\n\n### À partir des photos\n\n1. L'IA identifie le type de vêtement\n2. Propose une catégorie\n3. Suggère la marque si détectée\n\n### Précision\n\nLa catégorisation automatique a un taux de précision de ~85%. Vérifiez toujours les suggestions.\n\n## Limites\n\n- Disponible selon votre abonnement\n- Nombre de générations limitées par mois\n- Résultats à vérifier par vos soins	5	t	2025-12-24 10:07:51.340398+00	2025-12-24 10:07:51.340398+00
8	2	modifier-email	Comment modifier mon email ?	Procédure pour changer l'adresse email associée à votre compte Stoflow.	# Comment modifier mon email ?\n\n## Depuis les paramètres\n\n1. Connectez-vous à votre compte Stoflow\n2. Allez dans **Paramètres > Mon compte**\n3. Cliquez sur "Modifier" à côté de votre email\n4. Entrez votre nouvelle adresse email\n5. Confirmez avec votre mot de passe\n\n## Vérification\n\nUn email de confirmation sera envoyé à votre nouvelle adresse. Cliquez sur le lien pour valider le changement.\n\n## Délai\n\nLe changement est effectif immédiatement après confirmation.\n\n## En cas de problème\n\nSi vous ne recevez pas l'email de confirmation :\n- Vérifiez votre dossier spam\n- Attendez quelques minutes\n- Réessayez avec une autre adresse\n\nContactez le support si le problème persiste.	2	t	2025-12-24 10:09:12.709193+00	2025-12-24 10:09:12.709193+00
9	2	facturation	Questions sur la facturation	Tout savoir sur les factures, paiements et abonnements Stoflow.	# Questions sur la facturation\n\n## Où trouver mes factures ?\n\n1. Allez dans **Paramètres > Facturation**\n2. Cliquez sur "Historique des factures"\n3. Téléchargez la facture souhaitée au format PDF\n\n## Moyens de paiement acceptés\n\n- Carte bancaire (Visa, Mastercard)\n- PayPal\n- Prélèvement SEPA\n\n## Modifier mon moyen de paiement\n\n1. Paramètres > Facturation\n2. Section "Moyen de paiement"\n3. Cliquez sur "Modifier"\n4. Entrez les nouvelles informations\n\n## Annuler mon abonnement\n\n1. Paramètres > Abonnement\n2. Cliquez sur "Gérer l'abonnement"\n3. Sélectionnez "Annuler"\n4. Confirmez l'annulation\n\n> **Note** : Vous conservez l'accès jusqu'à la fin de la période payée.\n\n## Remboursement\n\nLes remboursements sont possibles sous 14 jours après le premier paiement, conformément au droit de rétractation. Contactez le support pour en faire la demande.\n\n## TVA\n\nLes prix affichés incluent la TVA française (20%). Pour les entreprises avec un numéro de TVA intracommunautaire, contactez-nous.	3	t	2025-12-24 10:09:12.709193+00	2025-12-24 10:09:12.709193+00
10	2	limites-produits	Quelles sont les limites de produits ?	Informations sur les quotas de produits selon votre abonnement.	# Quelles sont les limites de produits ?\n\n## Limites par abonnement\n\n| Abonnement | Produits max | Marketplaces |\n|------------|--------------|--------------|\n| Starter | 50 | 1 |\n| Pro | 500 | 3 |\n| Business | Illimité | Illimité |\n\n## Que se passe-t-il si j'atteins la limite ?\n\n- Vous ne pouvez plus créer de nouveaux produits\n- Les produits existants restent actifs\n- Vous êtes notifié par email\n\n## Comment augmenter ma limite ?\n\n### Passer à l'abonnement supérieur\n\n1. Paramètres > Abonnement\n2. Cliquez sur "Changer d'offre"\n3. Sélectionnez le nouvel abonnement\n4. La différence est calculée au prorata\n\n### Demander une extension temporaire\n\nPour des besoins ponctuels, contactez le support pour une extension temporaire (sous conditions).\n\n## Archivage des produits\n\nLes produits archivés ne comptent pas dans votre quota. Archivez les produits vendus ou inactifs pour libérer de la place.\n\n## FAQ rapide\n\n**Q: Les produits en brouillon comptent-ils ?**\nR: Oui, tous les produits (brouillon, publiés, archivés) comptent dans le quota.\n\n**Q: Puis-je supprimer des produits pour faire de la place ?**\nR: Oui, la suppression est immédiate et irréversible.	4	t	2025-12-24 10:09:12.709193+00	2025-12-24 10:09:12.709193+00
11	2	synchronisation	Problèmes de synchronisation	Solutions aux problèmes courants de synchronisation avec les marketplaces.	# Problèmes de synchronisation\n\n## La synchronisation ne fonctionne pas\n\n### Vérifications de base\n\n1. **Connexion internet** : Vérifiez votre connexion\n2. **Extension installée** : L'extension doit être active\n3. **Session Vinted** : Vous devez être connecté à Vinted\n\n### Réinitialiser la connexion\n\n1. Déconnectez l'intégration Vinted (Paramètres > Intégrations)\n2. Fermez et rouvrez votre navigateur\n3. Reconnectez-vous à Vinted\n4. Reconnectez l'intégration dans Stoflow\n\n## Produits non synchronisés\n\n### Causes possibles\n\n- Produit incomplet (photos manquantes)\n- Catégorie non mappée\n- Erreur côté Vinted\n\n### Solution\n\n1. Vérifiez le statut dans la colonne "Sync"\n2. Cliquez sur l'icône d'erreur pour voir le détail\n3. Corrigez le problème indiqué\n4. Relancez la synchronisation\n\n## Délais de synchronisation\n\n| Action | Délai normal |\n|--------|--------------|\n| Publication | 1-5 minutes |\n| Modification | 1-2 minutes |\n| Suppression | Immédiat |\n| Import initial | 5-30 minutes |\n\n## Forcer une synchronisation\n\nBouton "Synchroniser" dans :\n- La fiche produit (pour 1 produit)\n- La barre d'actions (pour une sélection)\n- Paramètres > Intégrations (pour tout)\n\n## Contacter le support\n\nSi le problème persiste après ces vérifications, contactez le support avec :\n- Capture d'écran de l'erreur\n- ID du produit concerné\n- Navigateur et version utilisés	5	t	2025-12-24 10:09:12.709193+00	2025-12-24 10:09:12.709193+00
12	2	securite-compte	Sécurité de mon compte	Conseils et options pour sécuriser votre compte Stoflow.	# Sécurité de mon compte\n\n## Mot de passe\n\n### Exigences\n\nVotre mot de passe doit contenir :\n- Au moins 8 caractères\n- Une majuscule\n- Une minuscule\n- Un chiffre\n- Un caractère spécial\n\n### Changer mon mot de passe\n\n1. Paramètres > Sécurité\n2. Cliquez sur "Modifier le mot de passe"\n3. Entrez l'ancien mot de passe\n4. Entrez le nouveau (x2)\n5. Confirmez\n\n### Mot de passe oublié\n\n1. Page de connexion\n2. Cliquez sur "Mot de passe oublié"\n3. Entrez votre email\n4. Suivez le lien reçu par email\n\n## Sessions actives\n\n### Voir mes sessions\n\nParamètres > Sécurité > Sessions actives\n\nVous voyez :\n- Appareil utilisé\n- Localisation approximative\n- Date de dernière activité\n\n### Déconnecter une session\n\nCliquez sur "Déconnecter" à côté de la session suspecte.\n\n### Déconnecter toutes les sessions\n\nOption "Déconnecter tous les appareils" pour forcer une reconnexion partout.\n\n## Activité suspecte\n\n### Signes d'alerte\n\n- Connexions depuis des lieux inhabituels\n- Modifications non effectuées par vous\n- Emails de notification non reconnus\n\n### Que faire ?\n\n1. Changez immédiatement votre mot de passe\n2. Déconnectez toutes les sessions\n3. Vérifiez vos informations de compte\n4. Contactez le support si nécessaire\n\n## Bonnes pratiques\n\n1. Utilisez un mot de passe unique\n2. Ne partagez jamais vos identifiants\n3. Déconnectez-vous des appareils partagés\n4. Vérifiez régulièrement vos sessions	6	t	2025-12-24 10:09:12.709193+00	2025-12-24 10:09:12.709193+00
\.



COPY public.doc_categories (id, slug, name, description, icon, display_order, is_active, created_at, updated_at) FROM stdin;
1	guide	Guide d'utilisation	Apprenez à utiliser Stoflow étape par étape	pi-book	0	t	2025-12-24 09:45:30.062696+00	2025-12-24 09:45:30.062696+00
2	faq	FAQ	Questions fréquemment posées	pi-question-circle	1	t	2025-12-24 09:45:30.062696+00	2025-12-24 09:45:30.062696+00
\.



COPY public.migration_errors (id, schema_name, product_id, migration_name, error_type, error_details, migrated_at) FROM stdin;
\.



COPY public.permissions (id, code, name, description, category, is_active) FROM stdin;
1	products:read	View products	View product list and details	products	t
2	products:create	Create products	Create new products	products	t
3	products:update	Update products	Modify existing products	products	t
4	products:delete	Delete products	Delete products	products	t
5	publications:read	View publications	View publication list and status	publications	t
6	publications:create	Publish products	Publish products to marketplaces	publications	t
7	publications:delete	Unpublish products	Remove products from marketplaces	publications	t
8	integrations:read	View integrations	View connected platforms	integrations	t
9	integrations:vinted:connect	Connect Vinted	Connect Vinted account	integrations	t
10	integrations:vinted:disconnect	Disconnect Vinted	Disconnect Vinted account	integrations	t
11	integrations:ebay:connect	Connect eBay	Connect eBay account	integrations	t
12	integrations:ebay:disconnect	Disconnect eBay	Disconnect eBay account	integrations	t
13	integrations:etsy:connect	Connect Etsy	Connect Etsy account	integrations	t
14	integrations:etsy:disconnect	Disconnect Etsy	Disconnect Etsy account	integrations	t
15	stats:read	View statistics	View sales and performance stats	stats	t
16	stats:export	Export statistics	Export stats to CSV/Excel	stats	t
17	account:read	View account	View own account settings	account	t
18	account:update	Update account	Modify own account settings	account	t
19	subscription:read	View subscription	View subscription details	account	t
20	subscription:manage	Manage subscription	Change subscription plan	account	t
21	admin:users:read	View all users	View all users in the system	admin	t
22	admin:users:update	Update users	Modify any user's data	admin	t
23	admin:users:delete	Delete users	Delete any user	admin	t
24	admin:users:role	Change user roles	Change any user's role	admin	t
25	admin:permissions:manage	Manage permissions	Modify role permissions	admin	t
\.



COPY public.revoked_tokens (token_hash, revoked_at, expires_at) FROM stdin;
\.



COPY public.role_permissions (id, role, permission_id) FROM stdin;
1	admin	1
2	admin	2
3	admin	3
4	admin	4
5	admin	5
6	admin	6
7	admin	7
8	admin	8
9	admin	9
10	admin	10
11	admin	11
12	admin	12
13	admin	13
14	admin	14
15	admin	15
16	admin	16
17	admin	17
18	admin	18
19	admin	19
20	admin	20
21	admin	21
22	admin	22
23	admin	23
24	admin	24
25	admin	25
26	user	1
27	user	2
28	user	3
29	user	4
30	user	5
31	user	6
32	user	7
33	user	8
34	user	9
35	user	10
36	user	11
37	user	12
38	user	13
39	user	14
40	user	15
41	user	16
42	user	17
43	user	18
44	user	19
45	user	20
46	support	1
47	support	5
48	support	8
49	support	15
50	support	17
51	support	18
52	support	19
53	support	21
\.



COPY public.subscription_features (id, subscription_quota_id, feature_text, display_order) FROM stdin;
1	1	Jusqu'à 50 produits	0
2	1	1 marketplace	1
3	1	Support email	2
4	2	Produits illimités	0
5	2	Toutes les marketplaces	1
6	2	Génération IA (100/mois)	2
7	2	Support prioritaire	3
8	3	Tout le plan Pro	0
9	3	Génération IA illimitée	1
10	3	API access	2
11	3	Support dédié	3
12	4	Tout illimité	0
13	4	Multi-utilisateurs	1
14	4	Intégration sur mesure	2
15	4	Account manager dédié	3
\.



COPY public.subscription_quotas (id, tier, max_products, max_platforms, ai_credits_monthly, price, display_name, description, annual_discount_percent, is_popular, cta_text, display_order) FROM stdin;
1	FREE	30	2	15	0.00	Gratuit	Pour découvrir Stoflow	0	f	Commencer	0
2	STARTER	150	3	75	19.00	Pro	Pour les vendeurs actifs	20	t	Essai gratuit 14 jours	1
3	PRO	500	5	250	49.00	Business	Pour les professionnels	20	f	Essai gratuit 14 jours	2
4	ENTERPRISE	999999	999999	999999	199.00	Enterprise	Pour les grandes équipes	20	f	Nous contacter	3
\.



COPY public.users (id, email, hashed_password, full_name, role, is_active, last_login, subscription_tier, subscription_status, created_at, updated_at, business_name, account_type, business_type, estimated_products, siret, vat_number, phone, country, language, subscription_tier_id, current_products_count, current_platforms_count, stripe_customer_id, stripe_subscription_id, failed_login_attempts, last_failed_login, locked_until, email_verified, email_verification_token, email_verification_expires, password_changed_at) FROM stdin;
2	test-sidebar@test.com	$2b$12$RWft3jWZJQZM/0I8wRHZQuKa2LBRdkcQeBzH9yosG0VlO8mXjLNDG	Test User	USER	t	2025-12-24 09:21:20.207261+00	FREE	active	2025-12-24 09:20:42.401319+00	2025-12-24 09:21:20.009895+00	\N	individual	resale	0-50	\N	\N	\N	FR	fr	1	0	0	\N	\N	0	\N	\N	t	8ff6ccc546ae0befc1d3acc53fb5ad05946c2be5b8ccedc50fa15f845406c16e	2025-12-25 09:20:42.959354+00	\N
3	test@stoflow.com	$2b$12$TZTllczoEX4PwNPNuRrtIOCwGgVs9TU0Gk8apEp2l2Ep.huVqf/9W	Test User	USER	t	\N	FREE	active	2025-12-24 10:33:21.112631+00	2025-12-24 10:33:21.631829+00	\N	individual	\N	\N	\N	\N	\N	FR	fr	1	0	0	\N	\N	0	\N	\N	f	06dce8a8233bb633392006bc868063f6f848b0b168c68d5a0f05995b5e17cfbc	2025-12-25 10:33:21.630735+00	\N
1	plugin-test2@stoflow.com	$2b$12$XCvNjFAlUe/r.A2QkJkfaulaYJlU23fiV37b9ihHvRFWUCoUgbTtq	rferfee	ADMIN	t	2026-01-08 16:07:13.561924+00	STARTER	active	2025-12-23 13:37:42.501163+00	2026-01-08 16:07:13.407562+00	rferre	individual	resale	\N	\N	\N	0778788167	FR	fr	2	0	0	\N	\N	0	\N	\N	t	Z35g5_7-yQd8gJ096yyHihg7k9WBRFc_I4Znztkk9tM	2025-12-24 13:37:42.988995+00	\N
\.



COPY template_tenant.ai_generation_logs (id, product_id, model, prompt_tokens, completion_tokens, total_tokens, total_cost, cached, generation_time_ms, error_message, created_at) FROM stdin;
\.



COPY template_tenant.batch_jobs (id, batch_id, marketplace, action_code, total_count, completed_count, failed_count, cancelled_count, status, priority, created_by_user_id, created_at, started_at, completed_at) FROM stdin;
\.



COPY template_tenant.ebay_credentials (id, ebay_user_id, access_token, refresh_token, access_token_expires_at, refresh_token_expires_at, sandbox_mode, is_connected, last_sync, created_at, updated_at, username, email, account_type, business_name, first_name, last_name, phone, address, marketplace, feedback_score, feedback_percentage, seller_level, registration_date) FROM stdin;
\.



COPY template_tenant.ebay_orders (id, order_id, marketplace_id, buyer_username, buyer_email, shipping_name, shipping_address, shipping_city, shipping_postal_code, shipping_country, total_price, currency, shipping_cost, order_fulfillment_status, order_payment_status, creation_date, paid_date, tracking_number, shipping_carrier, created_at, updated_at) FROM stdin;
\.



COPY template_tenant.ebay_orders_products (id, order_id, line_item_id, sku, sku_original, title, quantity, unit_price, total_price, currency, legacy_item_id, created_at) FROM stdin;
\.



COPY template_tenant.ebay_products (id, ebay_sku, product_id, title, description, price, currency, brand, size, color, material, category_id, condition, condition_description, quantity, availability_type, marketplace_id, ebay_listing_id, ebay_offer_id, image_urls, aspects, status, listing_format, listing_duration, package_weight_value, package_weight_unit, published_at, last_synced_at, created_at, updated_at, package_length_value, package_length_unit, package_width_value, package_width_unit, package_height_value, package_height_unit, merchant_location_key, secondary_category_id, lot_size, quantity_limit_per_buyer, listing_description, sold_quantity, available_quantity) FROM stdin;
\.



COPY template_tenant.ebay_products_marketplace (sku_derived, product_id, marketplace_id, ebay_offer_id, ebay_listing_id, status, error_message, published_at, sold_at, last_sync_at, created_at, updated_at) FROM stdin;
\.



COPY template_tenant.ebay_promoted_listings (id, campaign_id, campaign_name, marketplace_id, product_id, sku_derived, ad_id, listing_id, bid_percentage, ad_status, total_clicks, total_impressions, total_sales, total_sales_amount, total_ad_fees, created_at, updated_at) FROM stdin;
\.



COPY template_tenant.etsy_credentials (id, access_token, refresh_token, access_token_expires_at, refresh_token_expires_at, shop_id, shop_name, shop_url, user_id_etsy, email, is_connected, last_sync, created_at, updated_at) FROM stdin;
\.



COPY template_tenant.marketplace_jobs (id, batch_id, action_type_id, product_id, status, priority, error_message, retry_count, started_at, completed_at, expires_at, created_at, result_data, marketplace, batch_job_id, input_data, max_retries, idempotency_key) FROM stdin;
\.



COPY template_tenant.marketplace_tasks (id, task_type, status, payload, result, error_message, product_id, created_at, started_at, completed_at, retry_count, max_retries, platform, http_method, path, job_id, description) FROM stdin;
\.



COPY template_tenant.pending_instructions (id, user_id, action, status, result, error, created_at, completed_at, expires_at) FROM stdin;
\.



COPY template_tenant.product_colors (product_id, color, is_primary) FROM stdin;
\.



COPY template_tenant.product_condition_sups (product_id, condition_sup) FROM stdin;
\.



COPY template_tenant.product_images (id, product_id, image_path, display_order, created_at) FROM stdin;
\.



COPY template_tenant.product_materials (product_id, material, percentage) FROM stdin;
\.



COPY template_tenant.products (id, sku, title, description, price, category, brand, size_original, fit, gender, season, rise, closure, sleeve_length, origin, decade, trend, location, model, dim1, dim2, dim3, dim4, dim5, dim6, stock_quantity, images, status, scheduled_publish_at, published_at, sold_at, deleted_at, integration_metadata, created_at, updated_at, pricing_edit, pricing_rarity, pricing_quality, pricing_details, pricing_style, marking, sport, neckline, length, pattern, condition, size_normalized, unique_feature, stretch, version_number) FROM stdin;
\.



COPY template_tenant.publication_history (id, product_id, status, platform_product_id, error_message, metadata, created_at) FROM stdin;
\.



COPY template_tenant.vinted_connection (vinted_user_id, login, user_id, created_at, last_sync, is_connected, disconnected_at, last_datadome_ping, datadome_status, item_count, total_items_count, given_item_count, taken_item_count, followers_count, feedback_count, feedback_reputation, positive_feedback_count, negative_feedback_count, is_business, is_on_holiday, stats_updated_at) FROM stdin;
\.



COPY template_tenant.vinted_conversations (conversation_id, opposite_user_id, opposite_user_login, opposite_user_photo_url, last_message_preview, is_unread, unread_count, item_count, item_id, item_title, item_photo_url, transaction_id, updated_at_vinted, created_at, updated_at, last_synced_at) FROM stdin;
\.



COPY template_tenant.vinted_error_logs (id, product_id, operation, error_type, error_message, error_details, created_at) FROM stdin;
\.



COPY template_tenant.vinted_job_stats (id, action_type_id, date, total_jobs, success_count, failure_count, avg_duration_ms, created_at) FROM stdin;
\.



COPY template_tenant.vinted_messages (id, conversation_id, vinted_message_id, entity_type, sender_id, sender_login, body, title, subtitle, offer_price, offer_status, is_from_current_user, created_at_vinted, created_at) FROM stdin;
\.



COPY template_tenant.vinted_products (vinted_id, title, description, price, currency, brand, size, color, category, status, condition, is_draft, is_closed, view_count, favourite_count, url, photos_data, created_at, updated_at, total_price, brand_id, size_id, catalog_id, condition_id, material, measurements, measurement_width, measurement_length, manufacturer_labelling, is_reserved, is_hidden, seller_id, seller_login, service_fee, buyer_protection_fee, shipping_price, published_at, product_id, color1_id, color2_id, color2, status_id, is_unisex, measurement_unit, item_attributes) FROM stdin;
\.























































































ALTER TABLE ONLY product_attributes.brands
    ADD CONSTRAINT brands_pkey PRIMARY KEY (name);



ALTER TABLE ONLY product_attributes.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.closures
    ADD CONSTRAINT closures_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.colors
    ADD CONSTRAINT colors_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.condition_sups
    ADD CONSTRAINT condition_sups_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.conditions
    ADD CONSTRAINT conditions_new_pkey PRIMARY KEY (note);



ALTER TABLE ONLY product_attributes.decades
    ADD CONSTRAINT decades_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.dim1
    ADD CONSTRAINT dim1_pkey PRIMARY KEY (value);



ALTER TABLE ONLY product_attributes.dim2
    ADD CONSTRAINT dim2_pkey PRIMARY KEY (value);



ALTER TABLE ONLY product_attributes.dim3
    ADD CONSTRAINT dim3_pkey PRIMARY KEY (value);



ALTER TABLE ONLY product_attributes.dim4
    ADD CONSTRAINT dim4_pkey PRIMARY KEY (value);



ALTER TABLE ONLY product_attributes.dim5
    ADD CONSTRAINT dim5_pkey PRIMARY KEY (value);



ALTER TABLE ONLY product_attributes.dim6
    ADD CONSTRAINT dim6_pkey PRIMARY KEY (value);



ALTER TABLE ONLY product_attributes.fits
    ADD CONSTRAINT fits_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.genders
    ADD CONSTRAINT genders_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.lengths
    ADD CONSTRAINT lengths_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.linings
    ADD CONSTRAINT linings_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.materials
    ADD CONSTRAINT materials_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.necklines
    ADD CONSTRAINT necklines_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.origins
    ADD CONSTRAINT origins_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.patterns
    ADD CONSTRAINT patterns_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.rises
    ADD CONSTRAINT rises_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.seasons
    ADD CONSTRAINT seasons_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.sizes_normalized
    ADD CONSTRAINT sizes_normalized_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.sizes_original
    ADD CONSTRAINT sizes_original_pkey PRIMARY KEY (name);



ALTER TABLE ONLY product_attributes.sleeve_lengths
    ADD CONSTRAINT sleeve_lengths_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.sports
    ADD CONSTRAINT sports_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.stretches
    ADD CONSTRAINT stretches_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.trends
    ADD CONSTRAINT trends_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY product_attributes.unique_features
    ADD CONSTRAINT unique_features_pkey PRIMARY KEY (name_en);



ALTER TABLE ONLY public.admin_audit_logs
    ADD CONSTRAINT admin_audit_logs_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.ai_credits
    ADD CONSTRAINT ai_credits_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.ai_credits
    ADD CONSTRAINT ai_credits_user_id_key UNIQUE (user_id);



ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);



ALTER TABLE ONLY public.clothing_prices
    ADD CONSTRAINT clothing_prices_pkey PRIMARY KEY (brand, category);



ALTER TABLE ONLY public.doc_articles
    ADD CONSTRAINT doc_articles_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.doc_categories
    ADD CONSTRAINT doc_categories_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.migration_errors
    ADD CONSTRAINT idx_migration_errors_schema_product UNIQUE (schema_name, product_id, migration_name, error_type);



ALTER TABLE ONLY public.migration_errors
    ADD CONSTRAINT migration_errors_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.revoked_tokens
    ADD CONSTRAINT revoked_tokens_pkey PRIMARY KEY (token_hash);



ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.subscription_features
    ADD CONSTRAINT subscription_features_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.subscription_quotas
    ADD CONSTRAINT subscription_quotas_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT uq_role_permission UNIQUE (role, permission_id);



ALTER TABLE ONLY public.subscription_quotas
    ADD CONSTRAINT uq_subscription_quotas_tier UNIQUE (tier);



ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.ai_generation_logs
    ADD CONSTRAINT ai_generation_logs_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.batch_jobs
    ADD CONSTRAINT batch_jobs_batch_id_key UNIQUE (batch_id);



ALTER TABLE ONLY template_tenant.batch_jobs
    ADD CONSTRAINT batch_jobs_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.ebay_credentials
    ADD CONSTRAINT ebay_credentials_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.ebay_orders
    ADD CONSTRAINT ebay_orders_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.ebay_orders_products
    ADD CONSTRAINT ebay_orders_products_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.ebay_products
    ADD CONSTRAINT ebay_products_ebay_sku_key UNIQUE (ebay_sku);



ALTER TABLE ONLY template_tenant.ebay_products_marketplace
    ADD CONSTRAINT ebay_products_marketplace_pkey PRIMARY KEY (sku_derived);



ALTER TABLE ONLY template_tenant.ebay_products
    ADD CONSTRAINT ebay_products_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.ebay_products
    ADD CONSTRAINT ebay_products_product_id_key UNIQUE (product_id);



ALTER TABLE ONLY template_tenant.ebay_promoted_listings
    ADD CONSTRAINT ebay_promoted_listings_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.etsy_credentials
    ADD CONSTRAINT etsy_credentials_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.marketplace_jobs
    ADD CONSTRAINT marketplace_jobs_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.marketplace_tasks
    ADD CONSTRAINT marketplace_tasks_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.pending_instructions
    ADD CONSTRAINT pending_instructions_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.product_colors
    ADD CONSTRAINT pk_product_colors PRIMARY KEY (product_id, color);



ALTER TABLE ONLY template_tenant.product_condition_sups
    ADD CONSTRAINT pk_product_condition_sups PRIMARY KEY (product_id, condition_sup);



ALTER TABLE ONLY template_tenant.product_materials
    ADD CONSTRAINT pk_product_materials PRIMARY KEY (product_id, material);



ALTER TABLE ONLY template_tenant.product_images
    ADD CONSTRAINT product_images_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.publication_history
    ADD CONSTRAINT publication_history_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.ebay_promoted_listings
    ADD CONSTRAINT uq_ad_id UNIQUE (ad_id);



ALTER TABLE ONLY template_tenant.ebay_orders
    ADD CONSTRAINT uq_order_id UNIQUE (order_id);



ALTER TABLE ONLY template_tenant.vinted_products
    ADD CONSTRAINT uq_template_vinted_products_product_id UNIQUE (product_id);



ALTER TABLE ONLY template_tenant.vinted_connection
    ADD CONSTRAINT vinted_connection_pkey PRIMARY KEY (vinted_user_id);



ALTER TABLE ONLY template_tenant.vinted_conversations
    ADD CONSTRAINT vinted_conversations_pkey PRIMARY KEY (conversation_id);



ALTER TABLE ONLY template_tenant.vinted_error_logs
    ADD CONSTRAINT vinted_error_logs_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.vinted_job_stats
    ADD CONSTRAINT vinted_job_stats_action_type_id_date_key UNIQUE (action_type_id, date);



ALTER TABLE ONLY template_tenant.vinted_job_stats
    ADD CONSTRAINT vinted_job_stats_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.vinted_messages
    ADD CONSTRAINT vinted_messages_pkey PRIMARY KEY (id);



ALTER TABLE ONLY template_tenant.vinted_products
    ADD CONSTRAINT vinted_products_pkey PRIMARY KEY (vinted_id);



CREATE INDEX idx_colors_parent_color ON product_attributes.colors USING btree (parent_color);



CREATE INDEX idx_linings_name_en ON product_attributes.linings USING btree (name_en);



CREATE INDEX idx_stretches_name_en ON product_attributes.stretches USING btree (name_en);



CREATE INDEX ix_materials_vinted_id ON product_attributes.materials USING btree (vinted_id);



CREATE INDEX ix_product_attributes_brands_name ON product_attributes.brands USING btree (name);



CREATE INDEX ix_product_attributes_categories_name_en ON product_attributes.categories USING btree (name_en);



CREATE INDEX ix_product_attributes_categories_parent_category ON product_attributes.categories USING btree (parent_category);



CREATE INDEX ix_product_attributes_closures_name_en ON product_attributes.closures USING btree (name_en);



CREATE INDEX ix_product_attributes_colors_name_en ON product_attributes.colors USING btree (name_en);



CREATE INDEX ix_product_attributes_decades_name_en ON product_attributes.decades USING btree (name_en);



CREATE INDEX ix_product_attributes_fits_name_en ON product_attributes.fits USING btree (name_en);



CREATE INDEX ix_product_attributes_genders_name_en ON product_attributes.genders USING btree (name_en);



CREATE INDEX ix_product_attributes_lengths_name_en ON product_attributes.lengths USING btree (name_en);



CREATE INDEX ix_product_attributes_materials_name_en ON product_attributes.materials USING btree (name_en);



CREATE INDEX ix_product_attributes_necklines_name_en ON product_attributes.necklines USING btree (name_en);



CREATE INDEX ix_product_attributes_origins_name_en ON product_attributes.origins USING btree (name_en);



CREATE INDEX ix_product_attributes_patterns_name_en ON product_attributes.patterns USING btree (name_en);



CREATE INDEX ix_product_attributes_rises_name_en ON product_attributes.rises USING btree (name_en);



CREATE INDEX ix_product_attributes_seasons_name_en ON product_attributes.seasons USING btree (name_en);



CREATE INDEX ix_product_attributes_sizes_name_en ON product_attributes.sizes_normalized USING btree (name_en);



CREATE INDEX ix_product_attributes_sleeve_lengths_name_en ON product_attributes.sleeve_lengths USING btree (name_en);



CREATE INDEX ix_product_attributes_sports_name_en ON product_attributes.sports USING btree (name_en);



CREATE INDEX ix_product_attributes_trends_name_en ON product_attributes.trends USING btree (name_en);



CREATE INDEX ix_product_attributes_unique_features_name_en ON product_attributes.unique_features USING btree (name_en);



CREATE INDEX ix_sizes_original_name ON product_attributes.sizes_original USING btree (name);



CREATE INDEX idx_migration_errors_error_type ON public.migration_errors USING btree (error_type);



CREATE INDEX idx_migration_errors_migrated_at ON public.migration_errors USING btree (migrated_at DESC);



CREATE INDEX idx_migration_errors_schema_name ON public.migration_errors USING btree (schema_name);



CREATE INDEX idx_revoked_tokens_expires_at ON public.revoked_tokens USING btree (expires_at);



CREATE INDEX idx_revoked_tokens_token_hash ON public.revoked_tokens USING btree (token_hash);



CREATE INDEX ix_audit_action ON public.admin_audit_logs USING btree (action);



CREATE INDEX ix_audit_admin_id ON public.admin_audit_logs USING btree (admin_id);



CREATE INDEX ix_audit_created_at ON public.admin_audit_logs USING btree (created_at);



CREATE INDEX ix_audit_resource_type ON public.admin_audit_logs USING btree (resource_type);



CREATE INDEX ix_doc_articles_category_id ON public.doc_articles USING btree (category_id);



CREATE INDEX ix_doc_articles_display_order ON public.doc_articles USING btree (display_order);



CREATE UNIQUE INDEX ix_doc_articles_slug ON public.doc_articles USING btree (slug);



CREATE INDEX ix_doc_categories_display_order ON public.doc_categories USING btree (display_order);



CREATE UNIQUE INDEX ix_doc_categories_slug ON public.doc_categories USING btree (slug);



CREATE INDEX ix_public_ai_credits_id ON public.ai_credits USING btree (id);



CREATE UNIQUE INDEX ix_public_ai_credits_user_id ON public.ai_credits USING btree (user_id);



CREATE UNIQUE INDEX ix_public_permissions_code ON public.permissions USING btree (code);



CREATE INDEX ix_public_permissions_id ON public.permissions USING btree (id);



CREATE INDEX ix_public_role_permissions_id ON public.role_permissions USING btree (id);



CREATE INDEX ix_public_role_permissions_permission_id ON public.role_permissions USING btree (permission_id);



CREATE INDEX ix_public_role_permissions_role ON public.role_permissions USING btree (role);



CREATE UNIQUE INDEX ix_public_users_email ON public.users USING btree (email);



CREATE INDEX ix_public_users_id ON public.users USING btree (id);



CREATE INDEX ix_subscription_features_subscription_quota_id ON public.subscription_features USING btree (subscription_quota_id);



CREATE INDEX ix_subscription_quotas_id ON public.subscription_quotas USING btree (id);



CREATE INDEX ix_subscription_quotas_tier ON public.subscription_quotas USING btree (tier);



CREATE INDEX ix_users_email_verification_token ON public.users USING btree (email_verification_token) WHERE (email_verification_token IS NOT NULL);



CREATE INDEX ix_users_locked_until ON public.users USING btree (locked_until) WHERE (locked_until IS NOT NULL);



CREATE UNIQUE INDEX ix_users_stripe_customer_id ON public.users USING btree (stripe_customer_id);



CREATE INDEX idx_batch_jobs_batch_id ON template_tenant.batch_jobs USING btree (batch_id);



CREATE INDEX idx_batch_jobs_created_at ON template_tenant.batch_jobs USING btree (created_at);



CREATE INDEX idx_batch_jobs_marketplace ON template_tenant.batch_jobs USING btree (marketplace, status);



CREATE INDEX idx_batch_jobs_status ON template_tenant.batch_jobs USING btree (status, created_at);



CREATE INDEX idx_ebay_op_order_id ON template_tenant.ebay_orders_products USING btree (order_id);



CREATE INDEX idx_ebay_op_sku ON template_tenant.ebay_orders_products USING btree (sku);



CREATE INDEX idx_ebay_op_sku_original ON template_tenant.ebay_orders_products USING btree (sku_original);



CREATE INDEX idx_ebay_orders_fulfillment_status ON template_tenant.ebay_orders USING btree (order_fulfillment_status);



CREATE INDEX idx_ebay_orders_marketplace ON template_tenant.ebay_orders USING btree (marketplace_id);



CREATE INDEX idx_ebay_orders_order_id ON template_tenant.ebay_orders USING btree (order_id);



CREATE INDEX idx_ebay_pl_campaign ON template_tenant.ebay_promoted_listings USING btree (campaign_id);



CREATE INDEX idx_ebay_pl_marketplace ON template_tenant.ebay_promoted_listings USING btree (marketplace_id);



CREATE INDEX idx_ebay_pl_product_id ON template_tenant.ebay_promoted_listings USING btree (product_id);



CREATE INDEX idx_ebay_pl_status ON template_tenant.ebay_promoted_listings USING btree (ad_status);



CREATE INDEX idx_ebay_pm_listing_id ON template_tenant.ebay_products_marketplace USING btree (ebay_listing_id);



CREATE INDEX idx_ebay_pm_marketplace ON template_tenant.ebay_products_marketplace USING btree (marketplace_id);



CREATE INDEX idx_ebay_pm_product_id ON template_tenant.ebay_products_marketplace USING btree (product_id);



CREATE INDEX idx_ebay_pm_status ON template_tenant.ebay_products_marketplace USING btree (status);



CREATE INDEX idx_ebay_products_brand ON template_tenant.ebay_products USING btree (brand);



CREATE INDEX idx_ebay_products_ebay_listing_id ON template_tenant.ebay_products USING btree (ebay_listing_id);



CREATE INDEX idx_ebay_products_ebay_sku ON template_tenant.ebay_products USING btree (ebay_sku);



CREATE INDEX idx_ebay_products_marketplace_id ON template_tenant.ebay_products USING btree (marketplace_id);



CREATE INDEX idx_ebay_products_product_id ON template_tenant.ebay_products USING btree (product_id);



CREATE INDEX idx_ebay_products_status ON template_tenant.ebay_products USING btree (status);



CREATE INDEX idx_marketplace_jobs_batch_job_id ON template_tenant.marketplace_jobs USING btree (batch_job_id);



CREATE INDEX idx_marketplace_jobs_marketplace ON template_tenant.marketplace_jobs USING btree (marketplace);



CREATE INDEX idx_pending_instructions_user_status ON template_tenant.pending_instructions USING btree (user_id, status);



CREATE INDEX idx_product_colors_color ON template_tenant.product_colors USING btree (color);



CREATE INDEX idx_product_colors_product_id ON template_tenant.product_colors USING btree (product_id);



CREATE INDEX idx_product_condition_sups_condition_sup ON template_tenant.product_condition_sups USING btree (condition_sup);



CREATE INDEX idx_product_condition_sups_product_id ON template_tenant.product_condition_sups USING btree (product_id);



CREATE INDEX idx_product_materials_material ON template_tenant.product_materials USING btree (material);



CREATE INDEX idx_product_materials_product_id ON template_tenant.product_materials USING btree (product_id);



CREATE INDEX idx_products_stretch ON template_tenant.products USING btree (stretch);



CREATE UNIQUE INDEX idx_template_marketplace_jobs_idempotency_key ON template_tenant.marketplace_jobs USING btree (idempotency_key) WHERE (idempotency_key IS NOT NULL);



CREATE INDEX idx_template_tenant_vinted_products_catalog_id ON template_tenant.vinted_products USING btree (catalog_id);



CREATE INDEX idx_template_tenant_vinted_products_published_at ON template_tenant.vinted_products USING btree (published_at);



CREATE INDEX idx_template_tenant_vinted_products_seller_id ON template_tenant.vinted_products USING btree (seller_id);



CREATE INDEX idx_template_vinted_products_product_id ON template_tenant.vinted_products USING btree (product_id) WHERE (product_id IS NOT NULL);



CREATE INDEX idx_vinted_conversations_opposite_user ON template_tenant.vinted_conversations USING btree (opposite_user_id);



CREATE INDEX idx_vinted_conversations_transaction ON template_tenant.vinted_conversations USING btree (transaction_id);



CREATE INDEX idx_vinted_conversations_unread ON template_tenant.vinted_conversations USING btree (is_unread);



CREATE INDEX idx_vinted_conversations_updated ON template_tenant.vinted_conversations USING btree (updated_at_vinted);



CREATE INDEX idx_vinted_error_logs_created_at ON template_tenant.vinted_error_logs USING btree (created_at);



CREATE INDEX idx_vinted_error_logs_error_type ON template_tenant.vinted_error_logs USING btree (error_type);



CREATE INDEX idx_vinted_error_logs_product_id ON template_tenant.vinted_error_logs USING btree (product_id);



CREATE INDEX idx_vinted_messages_conversation ON template_tenant.vinted_messages USING btree (conversation_id);



CREATE INDEX idx_vinted_messages_created ON template_tenant.vinted_messages USING btree (created_at_vinted);



CREATE INDEX idx_vinted_messages_sender ON template_tenant.vinted_messages USING btree (sender_id);



CREATE INDEX idx_vinted_messages_type ON template_tenant.vinted_messages USING btree (entity_type);



CREATE INDEX idx_vinted_products_brand ON template_tenant.vinted_products USING btree (brand);



CREATE INDEX idx_vinted_products_status ON template_tenant.vinted_products USING btree (status);



CREATE INDEX ix_etsy_credentials_id ON template_tenant.etsy_credentials USING btree (id);



CREATE INDEX ix_etsy_credentials_shop_id ON template_tenant.etsy_credentials USING btree (shop_id);



CREATE INDEX ix_etsy_credentials_user_id_etsy ON template_tenant.etsy_credentials USING btree (user_id_etsy);



CREATE INDEX ix_template_tenant_ai_generation_logs_id ON template_tenant.ai_generation_logs USING btree (id);



CREATE INDEX ix_template_tenant_ai_generation_logs_product_id ON template_tenant.ai_generation_logs USING btree (product_id);



CREATE INDEX ix_template_tenant_ebay_credentials_ebay_user_id ON template_tenant.ebay_credentials USING btree (ebay_user_id);



CREATE INDEX ix_template_tenant_ebay_credentials_id ON template_tenant.ebay_credentials USING btree (id);



CREATE INDEX ix_template_tenant_marketplace_tasks_platform ON template_tenant.marketplace_tasks USING btree (platform);



CREATE INDEX ix_template_tenant_marketplace_tasks_product_id ON template_tenant.marketplace_tasks USING btree (product_id);



CREATE INDEX ix_template_tenant_marketplace_tasks_status ON template_tenant.marketplace_tasks USING btree (status);



CREATE INDEX ix_template_tenant_product_images_id ON template_tenant.product_images USING btree (id);



CREATE INDEX ix_template_tenant_product_images_product_id ON template_tenant.product_images USING btree (product_id);



CREATE INDEX ix_template_tenant_products_id ON template_tenant.products USING btree (id);



CREATE INDEX ix_template_tenant_products_length ON template_tenant.products USING btree (length);



CREATE INDEX ix_template_tenant_products_neckline ON template_tenant.products USING btree (neckline);



CREATE INDEX ix_template_tenant_products_pattern ON template_tenant.products USING btree (pattern);



CREATE INDEX ix_template_tenant_products_sport ON template_tenant.products USING btree (sport);



CREATE INDEX ix_template_tenant_publication_history_id ON template_tenant.publication_history USING btree (id);



CREATE INDEX ix_template_tenant_publication_history_product_id ON template_tenant.publication_history USING btree (product_id);



CREATE INDEX ix_template_tenant_vinted_connection_login ON template_tenant.vinted_connection USING btree (login);



CREATE INDEX ix_template_tenant_vinted_connection_user_id ON template_tenant.vinted_connection USING btree (user_id);



CREATE INDEX ix_template_vinted_conn_is_connected ON template_tenant.vinted_connection USING btree (is_connected);



CREATE INDEX ix_templatetenant_marketplace_jobs_batch_id ON template_tenant.marketplace_jobs USING btree (batch_id);



CREATE INDEX ix_templatetenant_marketplace_jobs_created_at ON template_tenant.marketplace_jobs USING btree (created_at);



CREATE INDEX ix_templatetenant_marketplace_jobs_priority ON template_tenant.marketplace_jobs USING btree (priority);



CREATE INDEX ix_templatetenant_marketplace_jobs_status ON template_tenant.marketplace_jobs USING btree (status);



CREATE INDEX ix_templatetenant_marketplace_tasks_job_id ON template_tenant.marketplace_tasks USING btree (job_id);



CREATE UNIQUE INDEX uq_product_colors_primary ON template_tenant.product_colors USING btree (product_id) WHERE (is_primary = true);



ALTER TABLE ONLY product_attributes.categories
    ADD CONSTRAINT categories_parent_category_fkey FOREIGN KEY (parent_category) REFERENCES product_attributes.categories(name_en) ON UPDATE CASCADE ON DELETE SET NULL;



ALTER TABLE ONLY product_attributes.categories
    ADD CONSTRAINT fk_categories_parent FOREIGN KEY (parent_category) REFERENCES product_attributes.categories(name_en) ON UPDATE CASCADE ON DELETE SET NULL;



ALTER TABLE ONLY product_attributes.colors
    ADD CONSTRAINT fk_colors_parent_color FOREIGN KEY (parent_color) REFERENCES product_attributes.colors(name_en) ON UPDATE CASCADE ON DELETE SET NULL;



ALTER TABLE ONLY public.admin_audit_logs
    ADD CONSTRAINT admin_audit_logs_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES public.users(id) ON DELETE SET NULL;



ALTER TABLE ONLY public.ai_credits
    ADD CONSTRAINT ai_credits_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;



ALTER TABLE ONLY public.doc_articles
    ADD CONSTRAINT doc_articles_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.doc_categories(id) ON DELETE CASCADE;



ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_subscription_tier_id FOREIGN KEY (subscription_tier_id) REFERENCES public.subscription_quotas(id);



ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(id) ON DELETE CASCADE;



ALTER TABLE ONLY public.subscription_features
    ADD CONSTRAINT subscription_features_subscription_quota_id_fkey FOREIGN KEY (subscription_quota_id) REFERENCES public.subscription_quotas(id) ON DELETE CASCADE;



ALTER TABLE ONLY template_tenant.ebay_orders_products
    ADD CONSTRAINT ebay_orders_products_order_id_fkey FOREIGN KEY (order_id) REFERENCES template_tenant.ebay_orders(order_id) ON DELETE CASCADE;



ALTER TABLE ONLY template_tenant.ebay_products_marketplace
    ADD CONSTRAINT ebay_products_marketplace_product_id_fkey FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;



ALTER TABLE ONLY template_tenant.ebay_products
    ADD CONSTRAINT ebay_products_product_id_fkey FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON UPDATE CASCADE ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.ebay_promoted_listings
    ADD CONSTRAINT ebay_promoted_listings_product_id_fkey FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;



ALTER TABLE ONLY template_tenant.ai_generation_logs
    ADD CONSTRAINT fk_ai_generation_logs_product_id FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;



ALTER TABLE ONLY template_tenant.batch_jobs
    ADD CONSTRAINT fk_batch_jobs_user FOREIGN KEY (created_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.marketplace_jobs
    ADD CONSTRAINT fk_marketplace_jobs_batch_job FOREIGN KEY (batch_job_id) REFERENCES template_tenant.batch_jobs(id) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.marketplace_tasks
    ADD CONSTRAINT fk_marketplace_tasks_job FOREIGN KEY (job_id) REFERENCES template_tenant.marketplace_jobs(id) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.product_colors
    ADD CONSTRAINT fk_product_colors_color FOREIGN KEY (color) REFERENCES product_attributes.colors(name_en) ON UPDATE CASCADE ON DELETE CASCADE;



ALTER TABLE ONLY template_tenant.product_colors
    ADD CONSTRAINT fk_product_colors_product_id FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;



ALTER TABLE ONLY template_tenant.product_condition_sups
    ADD CONSTRAINT fk_product_condition_sups_condition_sup FOREIGN KEY (condition_sup) REFERENCES product_attributes.condition_sups(name_en) ON UPDATE CASCADE ON DELETE CASCADE;



ALTER TABLE ONLY template_tenant.product_condition_sups
    ADD CONSTRAINT fk_product_condition_sups_product_id FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;



ALTER TABLE ONLY template_tenant.product_images
    ADD CONSTRAINT fk_product_images_product_id FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;



ALTER TABLE ONLY template_tenant.product_materials
    ADD CONSTRAINT fk_product_materials_material FOREIGN KEY (material) REFERENCES product_attributes.materials(name_en) ON UPDATE CASCADE ON DELETE CASCADE;



ALTER TABLE ONLY template_tenant.product_materials
    ADD CONSTRAINT fk_product_materials_product_id FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_products_size_normalized FOREIGN KEY (size_normalized) REFERENCES product_attributes.sizes_normalized(name_en) ON UPDATE CASCADE ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_products_stretch FOREIGN KEY (stretch) REFERENCES product_attributes.stretches(name_en) ON UPDATE CASCADE ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.publication_history
    ADD CONSTRAINT fk_publication_history_product_id FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_brand FOREIGN KEY (brand) REFERENCES product_attributes.brands(name) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_category FOREIGN KEY (category) REFERENCES product_attributes.categories(name_en) ON UPDATE CASCADE ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_closure FOREIGN KEY (closure) REFERENCES product_attributes.closures(name_en) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_condition FOREIGN KEY (condition) REFERENCES product_attributes.conditions(note) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_decade FOREIGN KEY (decade) REFERENCES product_attributes.decades(name_en) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_fit FOREIGN KEY (fit) REFERENCES product_attributes.fits(name_en) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_gender FOREIGN KEY (gender) REFERENCES product_attributes.genders(name_en) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_length FOREIGN KEY (length) REFERENCES product_attributes.lengths(name_en) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_neckline FOREIGN KEY (neckline) REFERENCES product_attributes.necklines(name_en) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_origin FOREIGN KEY (origin) REFERENCES product_attributes.origins(name_en) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_pattern FOREIGN KEY (pattern) REFERENCES product_attributes.patterns(name_en) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_rise FOREIGN KEY (rise) REFERENCES product_attributes.rises(name_en) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_season FOREIGN KEY (season) REFERENCES product_attributes.seasons(name_en) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_size FOREIGN KEY (size_normalized) REFERENCES product_attributes.sizes_normalized(name_en) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_sleeve_length FOREIGN KEY (sleeve_length) REFERENCES product_attributes.sleeve_lengths(name_en) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_sport FOREIGN KEY (sport) REFERENCES product_attributes.sports(name_en) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_trend FOREIGN KEY (trend) REFERENCES product_attributes.trends(name_en) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.vinted_products
    ADD CONSTRAINT fk_template_vinted_products_product_id FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON UPDATE CASCADE ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.marketplace_jobs
    ADD CONSTRAINT marketplace_jobs_action_type_id_fkey FOREIGN KEY (action_type_id) REFERENCES vinted.action_types(id);



ALTER TABLE ONLY template_tenant.marketplace_jobs
    ADD CONSTRAINT marketplace_jobs_product_id_fkey FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.marketplace_tasks
    ADD CONSTRAINT marketplace_tasks_job_id_fkey FOREIGN KEY (job_id) REFERENCES template_tenant.marketplace_jobs(id) ON DELETE SET NULL;



ALTER TABLE ONLY template_tenant.vinted_connection
    ADD CONSTRAINT vinted_connection_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;



ALTER TABLE ONLY template_tenant.vinted_error_logs
    ADD CONSTRAINT vinted_error_logs_product_id_fkey FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;



ALTER TABLE ONLY template_tenant.vinted_job_stats
    ADD CONSTRAINT vinted_job_stats_action_type_id_fkey FOREIGN KEY (action_type_id) REFERENCES vinted.action_types(id);



ALTER TABLE ONLY template_tenant.vinted_messages
    ADD CONSTRAINT vinted_messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES template_tenant.vinted_conversations(conversation_id) ON DELETE CASCADE;



\unrestrict Hboc06VsLwF69LAYeYxqTdQtgzwRvAaHkE7YIqfJg1yelCGRbZuRFQaIurSU9QS

