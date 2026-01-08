\restrict ErDm3VhmcvhgM6dDBn9VagxmpTbtiVI41qOmXUiS89gE7hW0dQfxseKdvCihVdh
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
\unrestrict ErDm3VhmcvhgM6dDBn9VagxmpTbtiVI41qOmXUiS89gE7hW0dQfxseKdvCihVdh
