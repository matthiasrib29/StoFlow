--
-- PostgreSQL database cluster dump
--

\restrict BBF8CVb3NEJC5mJ5WQkHvu0BBkSYXd6e7SwpYnjfJdRcg7Wt8AdinZadS1kmSh0

SET default_transaction_read_only = off;

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

--
-- Roles
--

CREATE ROLE stoflow_user;
ALTER ROLE stoflow_user WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION BYPASSRLS PASSWORD 'SCRAM-SHA-256$4096:mznxVgR5E2oZd2PUAgOoqA==$biRKYmVq1Axv+zW/ODJlL+Im5Y3XLbnbz3aEBycn1Bk=:zfph79asXl6ycTQC4Do3BMuWjDDfdWB3CfsixV+bPdE=';

--
-- User Configurations
--








\unrestrict BBF8CVb3NEJC5mJ5WQkHvu0BBkSYXd6e7SwpYnjfJdRcg7Wt8AdinZadS1kmSh0

--
-- Databases
--

--
-- Database "template1" dump
--

\connect template1

--
-- PostgreSQL database dump
--

\restrict QehaVPyvS2JORYwd9lCAQpCHmqb1UPKfGMd6Y0UcSpgJx00hSpWObEv3AZUpEyv

-- Dumped from database version 15.15
-- Dumped by pg_dump version 15.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- PostgreSQL database dump complete
--

\unrestrict QehaVPyvS2JORYwd9lCAQpCHmqb1UPKfGMd6Y0UcSpgJx00hSpWObEv3AZUpEyv

--
-- Database "postgres" dump
--

\connect postgres

--
-- PostgreSQL database dump
--

\restrict wGo2FTZAnIAs7SBGa97BdOAOZIL3rmqKCam2lHjvcbaxhCuHUdRT1nb4LzqLkxL

-- Dumped from database version 15.15
-- Dumped by pg_dump version 15.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- PostgreSQL database dump complete
--

\unrestrict wGo2FTZAnIAs7SBGa97BdOAOZIL3rmqKCam2lHjvcbaxhCuHUdRT1nb4LzqLkxL

--
-- Database "stoflow_db" dump
--

--
-- PostgreSQL database dump
--

\restrict QAugG7tPgQs6yLU5s12oyGoDWFUKA6ioUk77VYk2EKXsHgYmz9zGxo7CcCOkv0g

-- Dumped from database version 15.15
-- Dumped by pg_dump version 15.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: stoflow_db; Type: DATABASE; Schema: -; Owner: stoflow_user
--

CREATE DATABASE stoflow_db WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';


ALTER DATABASE stoflow_db OWNER TO stoflow_user;

\unrestrict QAugG7tPgQs6yLU5s12oyGoDWFUKA6ioUk77VYk2EKXsHgYmz9zGxo7CcCOkv0g
\connect stoflow_db
\restrict QAugG7tPgQs6yLU5s12oyGoDWFUKA6ioUk77VYk2EKXsHgYmz9zGxo7CcCOkv0g

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: ebay; Type: SCHEMA; Schema: -; Owner: stoflow_user
--

CREATE SCHEMA ebay;


ALTER SCHEMA ebay OWNER TO stoflow_user;

--
-- Name: product_attributes; Type: SCHEMA; Schema: -; Owner: stoflow_user
--

CREATE SCHEMA product_attributes;


ALTER SCHEMA product_attributes OWNER TO stoflow_user;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: pg_database_owner
--

COMMENT ON SCHEMA public IS 'Schema partagé pour tables communes (tenants, users, etc.)';


--
-- Name: template_tenant; Type: SCHEMA; Schema: -; Owner: stoflow_user
--

CREATE SCHEMA template_tenant;


ALTER SCHEMA template_tenant OWNER TO stoflow_user;

--
-- Name: user_1; Type: SCHEMA; Schema: -; Owner: stoflow_user
--

CREATE SCHEMA user_1;


ALTER SCHEMA user_1 OWNER TO stoflow_user;

--
-- Name: vinted; Type: SCHEMA; Schema: -; Owner: stoflow_user
--

CREATE SCHEMA vinted;


ALTER SCHEMA vinted OWNER TO stoflow_user;

--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: account_type; Type: TYPE; Schema: public; Owner: stoflow_user
--

CREATE TYPE public.account_type AS ENUM (
    'individual',
    'professional'
);


ALTER TYPE public.account_type OWNER TO stoflow_user;

--
-- Name: business_type; Type: TYPE; Schema: public; Owner: stoflow_user
--

CREATE TYPE public.business_type AS ENUM (
    'resale',
    'dropshipping',
    'artisan',
    'retail',
    'other'
);


ALTER TYPE public.business_type OWNER TO stoflow_user;

--
-- Name: datadomestatus; Type: TYPE; Schema: public; Owner: stoflow_user
--

CREATE TYPE public.datadomestatus AS ENUM (
    'OK',
    'FAILED',
    'UNKNOWN'
);


ALTER TYPE public.datadomestatus OWNER TO stoflow_user;

--
-- Name: estimated_products; Type: TYPE; Schema: public; Owner: stoflow_user
--

CREATE TYPE public.estimated_products AS ENUM (
    '0-50',
    '50-200',
    '200-500',
    '500+'
);


ALTER TYPE public.estimated_products OWNER TO stoflow_user;

--
-- Name: product_status; Type: TYPE; Schema: public; Owner: stoflow_user
--

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


ALTER TYPE public.product_status OWNER TO stoflow_user;

--
-- Name: publication_status; Type: TYPE; Schema: public; Owner: stoflow_user
--

CREATE TYPE public.publication_status AS ENUM (
    'PENDING',
    'SUCCESS',
    'FAILED'
);


ALTER TYPE public.publication_status OWNER TO stoflow_user;

--
-- Name: subscription_tier; Type: TYPE; Schema: public; Owner: stoflow_user
--

CREATE TYPE public.subscription_tier AS ENUM (
    'FREE',
    'STARTER',
    'PRO',
    'ENTERPRISE'
);


ALTER TYPE public.subscription_tier OWNER TO stoflow_user;

--
-- Name: user_role; Type: TYPE; Schema: public; Owner: stoflow_user
--

CREATE TYPE public.user_role AS ENUM (
    'ADMIN',
    'USER',
    'SUPPORT'
);


ALTER TYPE public.user_role OWNER TO stoflow_user;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: stoflow_user
--

CREATE TYPE public.userrole AS ENUM (
    'admin',
    'user',
    'support'
);


ALTER TYPE public.userrole OWNER TO stoflow_user;

--
-- Name: batch_job_status; Type: TYPE; Schema: template_tenant; Owner: stoflow_user
--

CREATE TYPE template_tenant.batch_job_status AS ENUM (
    'pending',
    'running',
    'completed',
    'partially_failed',
    'failed',
    'cancelled'
);


ALTER TYPE template_tenant.batch_job_status OWNER TO stoflow_user;

--
-- Name: marketplace_task_type; Type: TYPE; Schema: template_tenant; Owner: stoflow_user
--

CREATE TYPE template_tenant.marketplace_task_type AS ENUM (
    'plugin_http',
    'direct_http',
    'db_operation',
    'file_operation'
);


ALTER TYPE template_tenant.marketplace_task_type OWNER TO stoflow_user;

--
-- Name: batch_job_status; Type: TYPE; Schema: user_1; Owner: stoflow_user
--

CREATE TYPE user_1.batch_job_status AS ENUM (
    'pending',
    'running',
    'completed',
    'partially_failed',
    'failed',
    'cancelled'
);


ALTER TYPE user_1.batch_job_status OWNER TO stoflow_user;

--
-- Name: marketplace_task_type; Type: TYPE; Schema: user_1; Owner: stoflow_user
--

CREATE TYPE user_1.marketplace_task_type AS ENUM (
    'plugin_http',
    'direct_http',
    'db_operation',
    'file_operation'
);


ALTER TYPE user_1.marketplace_task_type OWNER TO stoflow_user;

--
-- Name: get_vinted_category(character varying, character varying, character varying, character varying, character varying, character varying, character varying, character varying, character varying); Type: FUNCTION; Schema: public; Owner: stoflow_user
--

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


ALTER FUNCTION public.get_vinted_category(p_category character varying, p_gender character varying, p_fit character varying, p_length character varying, p_rise character varying, p_material character varying, p_pattern character varying, p_neckline character varying, p_sleeve_length character varying) OWNER TO stoflow_user;

--
-- Name: get_vinted_category(character varying, character varying, character varying, character varying, character varying, character varying, character varying, character varying, character varying); Type: FUNCTION; Schema: vinted; Owner: stoflow_user
--

CREATE FUNCTION vinted.get_vinted_category(p_category character varying, p_gender character varying, p_fit character varying DEFAULT NULL::character varying, p_length character varying DEFAULT NULL::character varying, p_rise character varying DEFAULT NULL::character varying, p_material character varying DEFAULT NULL::character varying, p_pattern character varying DEFAULT NULL::character varying, p_neckline character varying DEFAULT NULL::character varying, p_sleeve_length character varying DEFAULT NULL::character varying) RETURNS integer
    LANGUAGE plpgsql
    AS $$
        DECLARE
            v_result INTEGER;
        BEGIN
            -- Try to find best match with attributes
            -- Score based on matching attributes (higher = better match)
            SELECT vinted_id INTO v_result
            FROM vinted.mapping
            WHERE my_category = p_category
              AND my_gender = p_gender
              AND (p_fit IS NULL OR my_fit IS NULL OR my_fit = p_fit)
              AND (p_length IS NULL OR my_length IS NULL OR my_length = p_length)
              AND (p_rise IS NULL OR my_rise IS NULL OR my_rise = p_rise)
              AND (p_material IS NULL OR my_material IS NULL OR my_material = p_material)
              AND (p_pattern IS NULL OR my_pattern IS NULL OR my_pattern = p_pattern)
              AND (p_neckline IS NULL OR my_neckline IS NULL || my_neckline = p_neckline)
              AND (p_sleeve_length IS NULL OR my_sleeve_length IS NULL OR my_sleeve_length = p_sleeve_length)
            ORDER BY
                -- Calculate match score: higher weight for more important attributes
                (CASE WHEN my_fit = p_fit THEN 10 ELSE 0 END) +
                (CASE WHEN my_length = p_length THEN 10 ELSE 0 END) +
                (CASE WHEN my_rise = p_rise THEN 10 ELSE 0 END) +
                (CASE WHEN my_material = p_material THEN 5 ELSE 0 END) +
                (CASE WHEN my_pattern = p_pattern THEN 3 ELSE 0 END) +
                (CASE WHEN my_neckline = p_neckline THEN 3 ELSE 0 END) +
                (CASE WHEN my_sleeve_length = p_sleeve_length THEN 2 ELSE 0 END) DESC,
                -- Prefer default mapping as tiebreaker
                is_default DESC
            LIMIT 1;

            -- Fallback to default if no specific match
            IF v_result IS NULL THEN
                SELECT vinted_id INTO v_result
                FROM vinted.mapping
                WHERE my_category = p_category
                  AND my_gender = p_gender
                  AND is_default = TRUE
                LIMIT 1;
            END IF;

            RETURN v_result;
        END;
        $$;


ALTER FUNCTION vinted.get_vinted_category(p_category character varying, p_gender character varying, p_fit character varying, p_length character varying, p_rise character varying, p_material character varying, p_pattern character varying, p_neckline character varying, p_sleeve_length character varying) OWNER TO stoflow_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: aspect_closure; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_closure (
    ebay_gb character varying(100) NOT NULL,
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_es character varying(100),
    ebay_it character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_closure OWNER TO stoflow_user;

--
-- Name: COLUMN aspect_closure.ebay_gb; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_closure.ebay_gb IS 'English/GB value (reference key)';


--
-- Name: COLUMN aspect_closure.ebay_fr; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_closure.ebay_fr IS 'French translation';


--
-- Name: COLUMN aspect_closure.ebay_de; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_closure.ebay_de IS 'German translation';


--
-- Name: COLUMN aspect_closure.ebay_es; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_closure.ebay_es IS 'Spanish translation';


--
-- Name: COLUMN aspect_closure.ebay_it; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_closure.ebay_it IS 'Italian translation';


--
-- Name: COLUMN aspect_closure.ebay_nl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_closure.ebay_nl IS 'Dutch translation';


--
-- Name: COLUMN aspect_closure.ebay_be; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_closure.ebay_be IS 'Belgian French translation';


--
-- Name: COLUMN aspect_closure.ebay_pl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_closure.ebay_pl IS 'Polish translation';


--
-- Name: aspect_colour; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_colour (
    ebay_gb character varying(100) NOT NULL,
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_es character varying(100),
    ebay_it character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_colour OWNER TO stoflow_user;

--
-- Name: COLUMN aspect_colour.ebay_gb; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_colour.ebay_gb IS 'English/GB value (reference key)';


--
-- Name: COLUMN aspect_colour.ebay_fr; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_colour.ebay_fr IS 'French translation';


--
-- Name: COLUMN aspect_colour.ebay_de; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_colour.ebay_de IS 'German translation';


--
-- Name: COLUMN aspect_colour.ebay_es; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_colour.ebay_es IS 'Spanish translation';


--
-- Name: COLUMN aspect_colour.ebay_it; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_colour.ebay_it IS 'Italian translation';


--
-- Name: COLUMN aspect_colour.ebay_nl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_colour.ebay_nl IS 'Dutch translation';


--
-- Name: COLUMN aspect_colour.ebay_be; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_colour.ebay_be IS 'Belgian French translation';


--
-- Name: COLUMN aspect_colour.ebay_pl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_colour.ebay_pl IS 'Polish translation';


--
-- Name: aspect_department; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_department (
    ebay_gb character varying(100) NOT NULL,
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_es character varying(100),
    ebay_it character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_department OWNER TO stoflow_user;

--
-- Name: COLUMN aspect_department.ebay_gb; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_department.ebay_gb IS 'English/GB value (reference key)';


--
-- Name: COLUMN aspect_department.ebay_fr; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_department.ebay_fr IS 'French translation';


--
-- Name: COLUMN aspect_department.ebay_de; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_department.ebay_de IS 'German translation';


--
-- Name: COLUMN aspect_department.ebay_es; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_department.ebay_es IS 'Spanish translation';


--
-- Name: COLUMN aspect_department.ebay_it; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_department.ebay_it IS 'Italian translation';


--
-- Name: COLUMN aspect_department.ebay_nl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_department.ebay_nl IS 'Dutch translation';


--
-- Name: COLUMN aspect_department.ebay_be; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_department.ebay_be IS 'Belgian French translation';


--
-- Name: COLUMN aspect_department.ebay_pl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_department.ebay_pl IS 'Polish translation';


--
-- Name: aspect_features; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_features (
    ebay_gb character varying(100) NOT NULL,
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_es character varying(100),
    ebay_it character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_features OWNER TO stoflow_user;

--
-- Name: COLUMN aspect_features.ebay_gb; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_features.ebay_gb IS 'English/GB value (reference key)';


--
-- Name: COLUMN aspect_features.ebay_fr; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_features.ebay_fr IS 'French translation';


--
-- Name: COLUMN aspect_features.ebay_de; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_features.ebay_de IS 'German translation';


--
-- Name: COLUMN aspect_features.ebay_es; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_features.ebay_es IS 'Spanish translation';


--
-- Name: COLUMN aspect_features.ebay_it; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_features.ebay_it IS 'Italian translation';


--
-- Name: COLUMN aspect_features.ebay_nl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_features.ebay_nl IS 'Dutch translation';


--
-- Name: COLUMN aspect_features.ebay_be; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_features.ebay_be IS 'Belgian French translation';


--
-- Name: COLUMN aspect_features.ebay_pl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_features.ebay_pl IS 'Polish translation';


--
-- Name: aspect_fit; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_fit (
    ebay_gb character varying(100) NOT NULL,
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_es character varying(100),
    ebay_it character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_fit OWNER TO stoflow_user;

--
-- Name: COLUMN aspect_fit.ebay_gb; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_fit.ebay_gb IS 'English/GB value (reference key)';


--
-- Name: COLUMN aspect_fit.ebay_fr; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_fit.ebay_fr IS 'French translation';


--
-- Name: COLUMN aspect_fit.ebay_de; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_fit.ebay_de IS 'German translation';


--
-- Name: COLUMN aspect_fit.ebay_es; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_fit.ebay_es IS 'Spanish translation';


--
-- Name: COLUMN aspect_fit.ebay_it; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_fit.ebay_it IS 'Italian translation';


--
-- Name: COLUMN aspect_fit.ebay_nl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_fit.ebay_nl IS 'Dutch translation';


--
-- Name: COLUMN aspect_fit.ebay_be; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_fit.ebay_be IS 'Belgian French translation';


--
-- Name: COLUMN aspect_fit.ebay_pl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_fit.ebay_pl IS 'Polish translation';


--
-- Name: aspect_inside_leg; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_inside_leg (
    ebay_gb character varying(100) NOT NULL,
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_es character varying(100),
    ebay_it character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_inside_leg OWNER TO stoflow_user;

--
-- Name: COLUMN aspect_inside_leg.ebay_gb; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_inside_leg.ebay_gb IS 'English/GB value (reference key)';


--
-- Name: COLUMN aspect_inside_leg.ebay_fr; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_inside_leg.ebay_fr IS 'French translation';


--
-- Name: COLUMN aspect_inside_leg.ebay_de; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_inside_leg.ebay_de IS 'German translation';


--
-- Name: COLUMN aspect_inside_leg.ebay_es; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_inside_leg.ebay_es IS 'Spanish translation';


--
-- Name: COLUMN aspect_inside_leg.ebay_it; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_inside_leg.ebay_it IS 'Italian translation';


--
-- Name: COLUMN aspect_inside_leg.ebay_nl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_inside_leg.ebay_nl IS 'Dutch translation';


--
-- Name: COLUMN aspect_inside_leg.ebay_be; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_inside_leg.ebay_be IS 'Belgian French translation';


--
-- Name: COLUMN aspect_inside_leg.ebay_pl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_inside_leg.ebay_pl IS 'Polish translation';


--
-- Name: aspect_material; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_material (
    ebay_gb character varying(100) NOT NULL,
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_es character varying(100),
    ebay_it character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_material OWNER TO stoflow_user;

--
-- Name: COLUMN aspect_material.ebay_gb; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_material.ebay_gb IS 'English/GB value (reference key)';


--
-- Name: COLUMN aspect_material.ebay_fr; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_material.ebay_fr IS 'French translation';


--
-- Name: COLUMN aspect_material.ebay_de; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_material.ebay_de IS 'German translation';


--
-- Name: COLUMN aspect_material.ebay_es; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_material.ebay_es IS 'Spanish translation';


--
-- Name: COLUMN aspect_material.ebay_it; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_material.ebay_it IS 'Italian translation';


--
-- Name: COLUMN aspect_material.ebay_nl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_material.ebay_nl IS 'Dutch translation';


--
-- Name: COLUMN aspect_material.ebay_be; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_material.ebay_be IS 'Belgian French translation';


--
-- Name: COLUMN aspect_material.ebay_pl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_material.ebay_pl IS 'Polish translation';


--
-- Name: aspect_name_mapping; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_name_mapping (
    aspect_key character varying(100) NOT NULL,
    ebay_gb character varying(100),
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_it character varying(100),
    ebay_es character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_name_mapping OWNER TO stoflow_user;

--
-- Name: aspect_neckline; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_neckline (
    ebay_gb character varying(100) NOT NULL,
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_es character varying(100),
    ebay_it character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_neckline OWNER TO stoflow_user;

--
-- Name: COLUMN aspect_neckline.ebay_gb; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_neckline.ebay_gb IS 'English/GB value (reference key)';


--
-- Name: COLUMN aspect_neckline.ebay_fr; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_neckline.ebay_fr IS 'French translation';


--
-- Name: COLUMN aspect_neckline.ebay_de; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_neckline.ebay_de IS 'German translation';


--
-- Name: COLUMN aspect_neckline.ebay_es; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_neckline.ebay_es IS 'Spanish translation';


--
-- Name: COLUMN aspect_neckline.ebay_it; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_neckline.ebay_it IS 'Italian translation';


--
-- Name: COLUMN aspect_neckline.ebay_nl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_neckline.ebay_nl IS 'Dutch translation';


--
-- Name: COLUMN aspect_neckline.ebay_be; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_neckline.ebay_be IS 'Belgian French translation';


--
-- Name: COLUMN aspect_neckline.ebay_pl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_neckline.ebay_pl IS 'Polish translation';


--
-- Name: aspect_occasion; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_occasion (
    ebay_gb character varying(100) NOT NULL,
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_es character varying(100),
    ebay_it character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_occasion OWNER TO stoflow_user;

--
-- Name: COLUMN aspect_occasion.ebay_gb; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_occasion.ebay_gb IS 'English/GB value (reference key)';


--
-- Name: COLUMN aspect_occasion.ebay_fr; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_occasion.ebay_fr IS 'French translation';


--
-- Name: COLUMN aspect_occasion.ebay_de; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_occasion.ebay_de IS 'German translation';


--
-- Name: COLUMN aspect_occasion.ebay_es; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_occasion.ebay_es IS 'Spanish translation';


--
-- Name: COLUMN aspect_occasion.ebay_it; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_occasion.ebay_it IS 'Italian translation';


--
-- Name: COLUMN aspect_occasion.ebay_nl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_occasion.ebay_nl IS 'Dutch translation';


--
-- Name: COLUMN aspect_occasion.ebay_be; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_occasion.ebay_be IS 'Belgian French translation';


--
-- Name: COLUMN aspect_occasion.ebay_pl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_occasion.ebay_pl IS 'Polish translation';


--
-- Name: aspect_pattern; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_pattern (
    ebay_gb character varying(100) NOT NULL,
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_es character varying(100),
    ebay_it character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_pattern OWNER TO stoflow_user;

--
-- Name: COLUMN aspect_pattern.ebay_gb; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_pattern.ebay_gb IS 'English/GB value (reference key)';


--
-- Name: COLUMN aspect_pattern.ebay_fr; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_pattern.ebay_fr IS 'French translation';


--
-- Name: COLUMN aspect_pattern.ebay_de; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_pattern.ebay_de IS 'German translation';


--
-- Name: COLUMN aspect_pattern.ebay_es; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_pattern.ebay_es IS 'Spanish translation';


--
-- Name: COLUMN aspect_pattern.ebay_it; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_pattern.ebay_it IS 'Italian translation';


--
-- Name: COLUMN aspect_pattern.ebay_nl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_pattern.ebay_nl IS 'Dutch translation';


--
-- Name: COLUMN aspect_pattern.ebay_be; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_pattern.ebay_be IS 'Belgian French translation';


--
-- Name: COLUMN aspect_pattern.ebay_pl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_pattern.ebay_pl IS 'Polish translation';


--
-- Name: aspect_rise; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_rise (
    ebay_gb character varying(100) NOT NULL,
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_es character varying(100),
    ebay_it character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_rise OWNER TO stoflow_user;

--
-- Name: COLUMN aspect_rise.ebay_gb; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_rise.ebay_gb IS 'English/GB value (reference key)';


--
-- Name: COLUMN aspect_rise.ebay_fr; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_rise.ebay_fr IS 'French translation';


--
-- Name: COLUMN aspect_rise.ebay_de; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_rise.ebay_de IS 'German translation';


--
-- Name: COLUMN aspect_rise.ebay_es; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_rise.ebay_es IS 'Spanish translation';


--
-- Name: COLUMN aspect_rise.ebay_it; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_rise.ebay_it IS 'Italian translation';


--
-- Name: COLUMN aspect_rise.ebay_nl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_rise.ebay_nl IS 'Dutch translation';


--
-- Name: COLUMN aspect_rise.ebay_be; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_rise.ebay_be IS 'Belgian French translation';


--
-- Name: COLUMN aspect_rise.ebay_pl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_rise.ebay_pl IS 'Polish translation';


--
-- Name: aspect_size; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_size (
    ebay_gb character varying(100) NOT NULL,
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_es character varying(100),
    ebay_it character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_size OWNER TO stoflow_user;

--
-- Name: COLUMN aspect_size.ebay_gb; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_size.ebay_gb IS 'English/GB value (reference key)';


--
-- Name: COLUMN aspect_size.ebay_fr; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_size.ebay_fr IS 'French translation';


--
-- Name: COLUMN aspect_size.ebay_de; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_size.ebay_de IS 'German translation';


--
-- Name: COLUMN aspect_size.ebay_es; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_size.ebay_es IS 'Spanish translation';


--
-- Name: COLUMN aspect_size.ebay_it; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_size.ebay_it IS 'Italian translation';


--
-- Name: COLUMN aspect_size.ebay_nl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_size.ebay_nl IS 'Dutch translation';


--
-- Name: COLUMN aspect_size.ebay_be; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_size.ebay_be IS 'Belgian French translation';


--
-- Name: COLUMN aspect_size.ebay_pl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_size.ebay_pl IS 'Polish translation';


--
-- Name: aspect_sleeve_length; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_sleeve_length (
    ebay_gb character varying(100) NOT NULL,
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_es character varying(100),
    ebay_it character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_sleeve_length OWNER TO stoflow_user;

--
-- Name: COLUMN aspect_sleeve_length.ebay_gb; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_sleeve_length.ebay_gb IS 'English/GB value (reference key)';


--
-- Name: COLUMN aspect_sleeve_length.ebay_fr; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_sleeve_length.ebay_fr IS 'French translation';


--
-- Name: COLUMN aspect_sleeve_length.ebay_de; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_sleeve_length.ebay_de IS 'German translation';


--
-- Name: COLUMN aspect_sleeve_length.ebay_es; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_sleeve_length.ebay_es IS 'Spanish translation';


--
-- Name: COLUMN aspect_sleeve_length.ebay_it; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_sleeve_length.ebay_it IS 'Italian translation';


--
-- Name: COLUMN aspect_sleeve_length.ebay_nl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_sleeve_length.ebay_nl IS 'Dutch translation';


--
-- Name: COLUMN aspect_sleeve_length.ebay_be; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_sleeve_length.ebay_be IS 'Belgian French translation';


--
-- Name: COLUMN aspect_sleeve_length.ebay_pl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_sleeve_length.ebay_pl IS 'Polish translation';


--
-- Name: aspect_style; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_style (
    ebay_gb character varying(100) NOT NULL,
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_es character varying(100),
    ebay_it character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_style OWNER TO stoflow_user;

--
-- Name: COLUMN aspect_style.ebay_gb; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_style.ebay_gb IS 'English/GB value (reference key)';


--
-- Name: COLUMN aspect_style.ebay_fr; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_style.ebay_fr IS 'French translation';


--
-- Name: COLUMN aspect_style.ebay_de; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_style.ebay_de IS 'German translation';


--
-- Name: COLUMN aspect_style.ebay_es; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_style.ebay_es IS 'Spanish translation';


--
-- Name: COLUMN aspect_style.ebay_it; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_style.ebay_it IS 'Italian translation';


--
-- Name: COLUMN aspect_style.ebay_nl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_style.ebay_nl IS 'Dutch translation';


--
-- Name: COLUMN aspect_style.ebay_be; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_style.ebay_be IS 'Belgian French translation';


--
-- Name: COLUMN aspect_style.ebay_pl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_style.ebay_pl IS 'Polish translation';


--
-- Name: aspect_type; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_type (
    ebay_gb character varying(100) NOT NULL,
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_es character varying(100),
    ebay_it character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_type OWNER TO stoflow_user;

--
-- Name: COLUMN aspect_type.ebay_gb; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_type.ebay_gb IS 'English/GB value (reference key)';


--
-- Name: COLUMN aspect_type.ebay_fr; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_type.ebay_fr IS 'French translation';


--
-- Name: COLUMN aspect_type.ebay_de; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_type.ebay_de IS 'German translation';


--
-- Name: COLUMN aspect_type.ebay_es; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_type.ebay_es IS 'Spanish translation';


--
-- Name: COLUMN aspect_type.ebay_it; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_type.ebay_it IS 'Italian translation';


--
-- Name: COLUMN aspect_type.ebay_nl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_type.ebay_nl IS 'Dutch translation';


--
-- Name: COLUMN aspect_type.ebay_be; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_type.ebay_be IS 'Belgian French translation';


--
-- Name: COLUMN aspect_type.ebay_pl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_type.ebay_pl IS 'Polish translation';


--
-- Name: aspect_waist_size; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.aspect_waist_size (
    ebay_gb character varying(100) NOT NULL,
    ebay_fr character varying(100),
    ebay_de character varying(100),
    ebay_es character varying(100),
    ebay_it character varying(100),
    ebay_nl character varying(100),
    ebay_be character varying(100),
    ebay_pl character varying(100)
);


ALTER TABLE ebay.aspect_waist_size OWNER TO stoflow_user;

--
-- Name: COLUMN aspect_waist_size.ebay_gb; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_waist_size.ebay_gb IS 'English/GB value (reference key)';


--
-- Name: COLUMN aspect_waist_size.ebay_fr; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_waist_size.ebay_fr IS 'French translation';


--
-- Name: COLUMN aspect_waist_size.ebay_de; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_waist_size.ebay_de IS 'German translation';


--
-- Name: COLUMN aspect_waist_size.ebay_es; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_waist_size.ebay_es IS 'Spanish translation';


--
-- Name: COLUMN aspect_waist_size.ebay_it; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_waist_size.ebay_it IS 'Italian translation';


--
-- Name: COLUMN aspect_waist_size.ebay_nl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_waist_size.ebay_nl IS 'Dutch translation';


--
-- Name: COLUMN aspect_waist_size.ebay_be; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_waist_size.ebay_be IS 'Belgian French translation';


--
-- Name: COLUMN aspect_waist_size.ebay_pl; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.aspect_waist_size.ebay_pl IS 'Polish translation';


--
-- Name: category_mapping; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.category_mapping (
    id integer NOT NULL,
    my_category character varying(100) NOT NULL,
    my_gender character varying(20) NOT NULL,
    ebay_category_id integer NOT NULL,
    ebay_name_en character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE ebay.category_mapping OWNER TO stoflow_user;

--
-- Name: COLUMN category_mapping.my_category; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.category_mapping.my_category IS 'StoFlow category name';


--
-- Name: COLUMN category_mapping.my_gender; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.category_mapping.my_gender IS 'Gender: men or women';


--
-- Name: COLUMN category_mapping.ebay_category_id; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.category_mapping.ebay_category_id IS 'eBay category ID (global for all EU marketplaces)';


--
-- Name: COLUMN category_mapping.ebay_name_en; Type: COMMENT; Schema: ebay; Owner: stoflow_user
--

COMMENT ON COLUMN ebay.category_mapping.ebay_name_en IS 'eBay category name in English';


--
-- Name: ebay_category_mapping_id_seq; Type: SEQUENCE; Schema: ebay; Owner: stoflow_user
--

CREATE SEQUENCE ebay.ebay_category_mapping_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE ebay.ebay_category_mapping_id_seq OWNER TO stoflow_user;

--
-- Name: ebay_category_mapping_id_seq; Type: SEQUENCE OWNED BY; Schema: ebay; Owner: stoflow_user
--

ALTER SEQUENCE ebay.ebay_category_mapping_id_seq OWNED BY ebay.category_mapping.id;


--
-- Name: exchange_rate; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.exchange_rate (
    id integer NOT NULL,
    currency character varying(3) NOT NULL,
    rate numeric(10,6) NOT NULL,
    source character varying(50) DEFAULT 'ECB'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE ebay.exchange_rate OWNER TO stoflow_user;

--
-- Name: exchange_rate_config_id_seq; Type: SEQUENCE; Schema: ebay; Owner: stoflow_user
--

CREATE SEQUENCE ebay.exchange_rate_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE ebay.exchange_rate_config_id_seq OWNER TO stoflow_user;

--
-- Name: exchange_rate_config_id_seq; Type: SEQUENCE OWNED BY; Schema: ebay; Owner: stoflow_user
--

ALTER SEQUENCE ebay.exchange_rate_config_id_seq OWNED BY ebay.exchange_rate.id;


--
-- Name: marketplace_config; Type: TABLE; Schema: ebay; Owner: stoflow_user
--

CREATE TABLE ebay.marketplace_config (
    id integer NOT NULL,
    marketplace_id character varying(20) NOT NULL,
    country_code character varying(2) NOT NULL,
    site_id integer NOT NULL,
    currency character varying(3) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE ebay.marketplace_config OWNER TO stoflow_user;

--
-- Name: marketplace_config_id_seq; Type: SEQUENCE; Schema: ebay; Owner: stoflow_user
--

CREATE SEQUENCE ebay.marketplace_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE ebay.marketplace_config_id_seq OWNER TO stoflow_user;

--
-- Name: marketplace_config_id_seq; Type: SEQUENCE OWNED BY; Schema: ebay; Owner: stoflow_user
--

ALTER SEQUENCE ebay.marketplace_config_id_seq OWNED BY ebay.marketplace_config.id;


--
-- Name: brands; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.brands (
    name character varying(100) NOT NULL,
    description text,
    vinted_id text,
    monitoring boolean DEFAULT false NOT NULL,
    sector_jeans character varying(20),
    sector_jacket character varying(20)
);


ALTER TABLE product_attributes.brands OWNER TO stoflow_user;

--
-- Name: COLUMN brands.name; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.brands.name IS 'Nom de la marque (EN)';


--
-- Name: COLUMN brands.description; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.brands.description IS 'Description de la marque';


--
-- Name: COLUMN brands.vinted_id; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.brands.vinted_id IS 'ID Vinted pour intégration marketplace';


--
-- Name: COLUMN brands.monitoring; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.brands.monitoring IS 'Marque surveillée (tracking spécial)';


--
-- Name: COLUMN brands.sector_jeans; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.brands.sector_jeans IS 'Segment de marché pour les jeans: BUDGET, STANDARD, HYPE, PREMIUM, ULTRA PREMIUM';


--
-- Name: COLUMN brands.sector_jacket; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.brands.sector_jacket IS 'Segment de marché pour les vestes: BUDGET, STANDARD, HYPE, PREMIUM, ULTRA PREMIUM';


--
-- Name: categories; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

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


ALTER TABLE product_attributes.categories OWNER TO stoflow_user;

--
-- Name: COLUMN categories.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.categories.name_en IS 'Nom de la catégorie (EN)';


--
-- Name: COLUMN categories.parent_category; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.categories.parent_category IS 'Catégorie parente (self-reference)';


--
-- Name: COLUMN categories.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.categories.name_fr IS 'Nom de la catégorie (FR)';


--
-- Name: COLUMN categories.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.categories.name_de IS 'Nom de la catégorie (DE)';


--
-- Name: COLUMN categories.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.categories.name_it IS 'Nom de la catégorie (IT)';


--
-- Name: COLUMN categories.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.categories.name_es IS 'Nom de la catégorie (ES)';


--
-- Name: COLUMN categories.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.categories.name_nl IS 'Nom de la catégorie (NL)';


--
-- Name: COLUMN categories.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.categories.name_pl IS 'Nom de la catégorie (PL)';


--
-- Name: COLUMN categories.genders; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.categories.genders IS 'Available genders for this category';


--
-- Name: closures; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.closures (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);


ALTER TABLE product_attributes.closures OWNER TO stoflow_user;

--
-- Name: COLUMN closures.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.closures.name_en IS 'Type de fermeture (EN)';


--
-- Name: COLUMN closures.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.closures.name_fr IS 'Type de fermeture (FR)';


--
-- Name: COLUMN closures.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.closures.name_de IS 'Type de fermeture (DE)';


--
-- Name: COLUMN closures.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.closures.name_it IS 'Type de fermeture (IT)';


--
-- Name: COLUMN closures.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.closures.name_es IS 'Type de fermeture (ES)';


--
-- Name: COLUMN closures.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.closures.name_nl IS 'Type de fermeture (NL)';


--
-- Name: COLUMN closures.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.closures.name_pl IS 'Type de fermeture (PL)';


--
-- Name: colors; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

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


ALTER TABLE product_attributes.colors OWNER TO stoflow_user;

--
-- Name: COLUMN colors.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.colors.name_en IS 'Nom de la couleur (EN)';


--
-- Name: COLUMN colors.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.colors.name_fr IS 'Nom de la couleur (FR)';


--
-- Name: COLUMN colors.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.colors.name_de IS 'Nom de la couleur (DE)';


--
-- Name: COLUMN colors.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.colors.name_it IS 'Nom de la couleur (IT)';


--
-- Name: COLUMN colors.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.colors.name_es IS 'Nom de la couleur (ES)';


--
-- Name: COLUMN colors.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.colors.name_nl IS 'Nom de la couleur (NL)';


--
-- Name: COLUMN colors.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.colors.name_pl IS 'Nom de la couleur (PL)';


--
-- Name: COLUMN colors.hex_code; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.colors.hex_code IS 'Code couleur hexadécimal (#RRGGBB)';


--
-- Name: condition_sups; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.condition_sups (
    name_en character varying(255) NOT NULL,
    name_fr character varying(255),
    name_de character varying(255),
    name_it character varying(255),
    name_es character varying(255),
    name_nl character varying(255),
    name_pl character varying(255)
);


ALTER TABLE product_attributes.condition_sups OWNER TO stoflow_user;

--
-- Name: COLUMN condition_sups.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.condition_sups.name_en IS 'Détail d''état supplémentaire (EN)';


--
-- Name: COLUMN condition_sups.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.condition_sups.name_fr IS 'Détail d''état supplémentaire (FR)';


--
-- Name: COLUMN condition_sups.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.condition_sups.name_de IS 'Détail d''état supplémentaire (DE)';


--
-- Name: COLUMN condition_sups.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.condition_sups.name_it IS 'Détail d''état supplémentaire (IT)';


--
-- Name: COLUMN condition_sups.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.condition_sups.name_es IS 'Détail d''état supplémentaire (ES)';


--
-- Name: COLUMN condition_sups.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.condition_sups.name_nl IS 'Détail d''état supplémentaire (NL)';


--
-- Name: COLUMN condition_sups.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.condition_sups.name_pl IS 'Détail d''état supplémentaire (PL)';


--
-- Name: conditions; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

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


ALTER TABLE product_attributes.conditions OWNER TO stoflow_user;

--
-- Name: decades; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.decades (
    name_en character varying(100) NOT NULL
);


ALTER TABLE product_attributes.decades OWNER TO stoflow_user;

--
-- Name: COLUMN decades.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.decades.name_en IS 'Décennie (EN)';


--
-- Name: dim1; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.dim1 (
    value integer NOT NULL,
    CONSTRAINT dim1_value_positive CHECK ((value > 0))
);


ALTER TABLE product_attributes.dim1 OWNER TO stoflow_user;

--
-- Name: TABLE dim1; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON TABLE product_attributes.dim1 IS 'Chest / Shoulders (cm) - Tour de poitrine / Épaules (cm)';


--
-- Name: dim2; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.dim2 (
    value integer NOT NULL,
    CONSTRAINT dim2_value_positive CHECK ((value > 0))
);


ALTER TABLE product_attributes.dim2 OWNER TO stoflow_user;

--
-- Name: TABLE dim2; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON TABLE product_attributes.dim2 IS 'Total length (cm) - Longueur totale (cm)';


--
-- Name: dim3; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.dim3 (
    value integer NOT NULL,
    CONSTRAINT dim3_value_positive CHECK ((value > 0))
);


ALTER TABLE product_attributes.dim3 OWNER TO stoflow_user;

--
-- Name: TABLE dim3; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON TABLE product_attributes.dim3 IS 'Sleeve length (cm) - Longueur manche (cm)';


--
-- Name: dim4; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.dim4 (
    value integer NOT NULL,
    CONSTRAINT dim4_value_positive CHECK ((value > 0))
);


ALTER TABLE product_attributes.dim4 OWNER TO stoflow_user;

--
-- Name: TABLE dim4; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON TABLE product_attributes.dim4 IS 'Waist (cm) - Tour de taille (cm)';


--
-- Name: dim5; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.dim5 (
    value integer NOT NULL,
    CONSTRAINT dim5_value_positive CHECK ((value > 0))
);


ALTER TABLE product_attributes.dim5 OWNER TO stoflow_user;

--
-- Name: TABLE dim5; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON TABLE product_attributes.dim5 IS 'Hips (cm) - Tour de hanches (cm)';


--
-- Name: dim6; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.dim6 (
    value integer NOT NULL,
    CONSTRAINT dim6_value_positive CHECK ((value > 0))
);


ALTER TABLE product_attributes.dim6 OWNER TO stoflow_user;

--
-- Name: TABLE dim6; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON TABLE product_attributes.dim6 IS 'Inseam (cm) - Entrejambe (cm)';


--
-- Name: fits; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.fits (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);


ALTER TABLE product_attributes.fits OWNER TO stoflow_user;

--
-- Name: COLUMN fits.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.fits.name_en IS 'Coupe (EN)';


--
-- Name: COLUMN fits.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.fits.name_fr IS 'Coupe (FR)';


--
-- Name: COLUMN fits.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.fits.name_de IS 'Coupe (DE)';


--
-- Name: COLUMN fits.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.fits.name_it IS 'Coupe (IT)';


--
-- Name: COLUMN fits.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.fits.name_es IS 'Coupe (ES)';


--
-- Name: COLUMN fits.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.fits.name_nl IS 'Coupe (NL)';


--
-- Name: COLUMN fits.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.fits.name_pl IS 'Coupe (PL)';


--
-- Name: genders; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

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


ALTER TABLE product_attributes.genders OWNER TO stoflow_user;

--
-- Name: COLUMN genders.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.genders.name_en IS 'Genre (EN)';


--
-- Name: COLUMN genders.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.genders.name_fr IS 'Genre (FR)';


--
-- Name: COLUMN genders.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.genders.name_de IS 'Genre (DE)';


--
-- Name: COLUMN genders.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.genders.name_it IS 'Genre (IT)';


--
-- Name: COLUMN genders.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.genders.name_es IS 'Genre (ES)';


--
-- Name: COLUMN genders.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.genders.name_nl IS 'Genre (NL)';


--
-- Name: COLUMN genders.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.genders.name_pl IS 'Genre (PL)';


--
-- Name: COLUMN genders.vinted_id; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.genders.vinted_id IS 'ID genre Vinted';


--
-- Name: COLUMN genders.ebay_gender; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.genders.ebay_gender IS 'Genre eBay correspondant';


--
-- Name: COLUMN genders.etsy_gender; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.genders.etsy_gender IS 'Genre Etsy correspondant';


--
-- Name: lengths; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

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


ALTER TABLE product_attributes.lengths OWNER TO stoflow_user;

--
-- Name: COLUMN lengths.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.lengths.name_en IS 'Nom de la longueur (EN)';


--
-- Name: COLUMN lengths.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.lengths.name_fr IS 'Nom de la longueur (FR)';


--
-- Name: COLUMN lengths.description; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.lengths.description IS 'Description de la longueur';


--
-- Name: COLUMN lengths.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.lengths.name_de IS 'Nom de la longueur (DE)';


--
-- Name: COLUMN lengths.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.lengths.name_it IS 'Nom de la longueur (IT)';


--
-- Name: COLUMN lengths.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.lengths.name_es IS 'Nom de la longueur (ES)';


--
-- Name: COLUMN lengths.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.lengths.name_nl IS 'Nom de la longueur (NL)';


--
-- Name: COLUMN lengths.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.lengths.name_pl IS 'Nom de la longueur (PL)';


--
-- Name: linings; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.linings (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);


ALTER TABLE product_attributes.linings OWNER TO stoflow_user;

--
-- Name: materials; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

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


ALTER TABLE product_attributes.materials OWNER TO stoflow_user;

--
-- Name: COLUMN materials.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.materials.name_en IS 'Matière (EN)';


--
-- Name: COLUMN materials.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.materials.name_fr IS 'Matière (FR)';


--
-- Name: COLUMN materials.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.materials.name_de IS 'Matière (DE)';


--
-- Name: COLUMN materials.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.materials.name_it IS 'Matière (IT)';


--
-- Name: COLUMN materials.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.materials.name_es IS 'Matière (ES)';


--
-- Name: COLUMN materials.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.materials.name_nl IS 'Matière (NL)';


--
-- Name: COLUMN materials.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.materials.name_pl IS 'Matière (PL)';


--
-- Name: COLUMN materials.vinted_id; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.materials.vinted_id IS 'Vinted material ID';


--
-- Name: necklines; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

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


ALTER TABLE product_attributes.necklines OWNER TO stoflow_user;

--
-- Name: COLUMN necklines.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.necklines.name_en IS 'Nom de l''encolure (EN)';


--
-- Name: COLUMN necklines.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.necklines.name_fr IS 'Nom de l''encolure (FR)';


--
-- Name: COLUMN necklines.description; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.necklines.description IS 'Description de l''encolure';


--
-- Name: COLUMN necklines.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.necklines.name_de IS 'Nom de l''encolure (DE)';


--
-- Name: COLUMN necklines.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.necklines.name_it IS 'Nom de l''encolure (IT)';


--
-- Name: COLUMN necklines.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.necklines.name_es IS 'Nom de l''encolure (ES)';


--
-- Name: COLUMN necklines.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.necklines.name_nl IS 'Nom de l''encolure (NL)';


--
-- Name: COLUMN necklines.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.necklines.name_pl IS 'Nom de l''encolure (PL)';


--
-- Name: origins; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.origins (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);


ALTER TABLE product_attributes.origins OWNER TO stoflow_user;

--
-- Name: COLUMN origins.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.origins.name_en IS 'Origine/Provenance (EN)';


--
-- Name: COLUMN origins.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.origins.name_fr IS 'Origine/Provenance (FR)';


--
-- Name: COLUMN origins.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.origins.name_de IS 'Origine/Provenance (DE)';


--
-- Name: COLUMN origins.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.origins.name_it IS 'Origine/Provenance (IT)';


--
-- Name: COLUMN origins.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.origins.name_es IS 'Origine/Provenance (ES)';


--
-- Name: COLUMN origins.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.origins.name_nl IS 'Origine/Provenance (NL)';


--
-- Name: COLUMN origins.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.origins.name_pl IS 'Origine/Provenance (PL)';


--
-- Name: patterns; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

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


ALTER TABLE product_attributes.patterns OWNER TO stoflow_user;

--
-- Name: COLUMN patterns.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.patterns.name_en IS 'Nom du motif (EN)';


--
-- Name: COLUMN patterns.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.patterns.name_fr IS 'Nom du motif (FR)';


--
-- Name: COLUMN patterns.description; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.patterns.description IS 'Description du motif';


--
-- Name: COLUMN patterns.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.patterns.name_de IS 'Nom du motif (DE)';


--
-- Name: COLUMN patterns.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.patterns.name_it IS 'Nom du motif (IT)';


--
-- Name: COLUMN patterns.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.patterns.name_es IS 'Nom du motif (ES)';


--
-- Name: COLUMN patterns.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.patterns.name_nl IS 'Nom du motif (NL)';


--
-- Name: COLUMN patterns.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.patterns.name_pl IS 'Nom du motif (PL)';


--
-- Name: rises; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.rises (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);


ALTER TABLE product_attributes.rises OWNER TO stoflow_user;

--
-- Name: COLUMN rises.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.rises.name_en IS 'Hauteur de taille (EN)';


--
-- Name: COLUMN rises.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.rises.name_fr IS 'Hauteur de taille (FR)';


--
-- Name: COLUMN rises.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.rises.name_de IS 'Hauteur de taille (DE)';


--
-- Name: COLUMN rises.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.rises.name_it IS 'Hauteur de taille (IT)';


--
-- Name: COLUMN rises.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.rises.name_es IS 'Hauteur de taille (ES)';


--
-- Name: COLUMN rises.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.rises.name_nl IS 'Hauteur de taille (NL)';


--
-- Name: COLUMN rises.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.rises.name_pl IS 'Hauteur de taille (PL)';


--
-- Name: seasons; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.seasons (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);


ALTER TABLE product_attributes.seasons OWNER TO stoflow_user;

--
-- Name: COLUMN seasons.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.seasons.name_en IS 'Saison (EN)';


--
-- Name: COLUMN seasons.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.seasons.name_fr IS 'Saison (FR)';


--
-- Name: COLUMN seasons.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.seasons.name_de IS 'Saison (DE)';


--
-- Name: COLUMN seasons.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.seasons.name_it IS 'Saison (IT)';


--
-- Name: COLUMN seasons.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.seasons.name_es IS 'Saison (ES)';


--
-- Name: COLUMN seasons.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.seasons.name_nl IS 'Saison (NL)';


--
-- Name: COLUMN seasons.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.seasons.name_pl IS 'Saison (PL)';


--
-- Name: sizes_normalized; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.sizes_normalized (
    name_en character varying(100) NOT NULL,
    ebay_size character varying(50),
    etsy_size character varying(50),
    vinted_women_id integer,
    vinted_men_id integer
);


ALTER TABLE product_attributes.sizes_normalized OWNER TO stoflow_user;

--
-- Name: COLUMN sizes_normalized.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sizes_normalized.name_en IS 'Taille (EN)';


--
-- Name: COLUMN sizes_normalized.ebay_size; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sizes_normalized.ebay_size IS 'Taille eBay correspondante';


--
-- Name: COLUMN sizes_normalized.etsy_size; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sizes_normalized.etsy_size IS 'Taille Etsy correspondante';


--
-- Name: sizes_original; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.sizes_original (
    name character varying(100) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE product_attributes.sizes_original OWNER TO stoflow_user;

--
-- Name: sleeve_lengths; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.sleeve_lengths (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);


ALTER TABLE product_attributes.sleeve_lengths OWNER TO stoflow_user;

--
-- Name: COLUMN sleeve_lengths.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sleeve_lengths.name_en IS 'Longueur de manche (EN)';


--
-- Name: COLUMN sleeve_lengths.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sleeve_lengths.name_fr IS 'Longueur de manche (FR)';


--
-- Name: COLUMN sleeve_lengths.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sleeve_lengths.name_de IS 'Longueur de manche (DE)';


--
-- Name: COLUMN sleeve_lengths.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sleeve_lengths.name_it IS 'Longueur de manche (IT)';


--
-- Name: COLUMN sleeve_lengths.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sleeve_lengths.name_es IS 'Longueur de manche (ES)';


--
-- Name: COLUMN sleeve_lengths.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sleeve_lengths.name_nl IS 'Longueur de manche (NL)';


--
-- Name: COLUMN sleeve_lengths.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sleeve_lengths.name_pl IS 'Longueur de manche (PL)';


--
-- Name: sports; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

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


ALTER TABLE product_attributes.sports OWNER TO stoflow_user;

--
-- Name: COLUMN sports.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sports.name_en IS 'Nom du sport (EN)';


--
-- Name: COLUMN sports.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sports.name_fr IS 'Nom du sport (FR)';


--
-- Name: COLUMN sports.description; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sports.description IS 'Description du sport';


--
-- Name: COLUMN sports.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sports.name_de IS 'Nom du sport (DE)';


--
-- Name: COLUMN sports.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sports.name_it IS 'Nom du sport (IT)';


--
-- Name: COLUMN sports.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sports.name_es IS 'Nom du sport (ES)';


--
-- Name: COLUMN sports.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sports.name_nl IS 'Nom du sport (NL)';


--
-- Name: COLUMN sports.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.sports.name_pl IS 'Nom du sport (PL)';


--
-- Name: stretches; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.stretches (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);


ALTER TABLE product_attributes.stretches OWNER TO stoflow_user;

--
-- Name: trends; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.trends (
    name_en character varying(100) NOT NULL,
    name_fr character varying(100),
    name_de character varying(100),
    name_it character varying(100),
    name_es character varying(100),
    name_nl character varying(100),
    name_pl character varying(100)
);


ALTER TABLE product_attributes.trends OWNER TO stoflow_user;

--
-- Name: COLUMN trends.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.trends.name_en IS 'Tendance/Style (EN)';


--
-- Name: COLUMN trends.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.trends.name_fr IS 'Tendance/Style (FR)';


--
-- Name: COLUMN trends.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.trends.name_de IS 'Tendance/Style (DE)';


--
-- Name: COLUMN trends.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.trends.name_it IS 'Tendance/Style (IT)';


--
-- Name: COLUMN trends.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.trends.name_es IS 'Tendance/Style (ES)';


--
-- Name: COLUMN trends.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.trends.name_nl IS 'Tendance/Style (NL)';


--
-- Name: COLUMN trends.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.trends.name_pl IS 'Tendance/Style (PL)';


--
-- Name: unique_features; Type: TABLE; Schema: product_attributes; Owner: stoflow_user
--

CREATE TABLE product_attributes.unique_features (
    name_en character varying(255) NOT NULL,
    name_fr character varying(255),
    name_de character varying(255),
    name_it character varying(255),
    name_es character varying(255),
    name_nl character varying(255),
    name_pl character varying(255)
);


ALTER TABLE product_attributes.unique_features OWNER TO stoflow_user;

--
-- Name: COLUMN unique_features.name_en; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.unique_features.name_en IS 'Caractéristique unique (EN)';


--
-- Name: COLUMN unique_features.name_fr; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.unique_features.name_fr IS 'Caractéristique unique (FR)';


--
-- Name: COLUMN unique_features.name_de; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.unique_features.name_de IS 'Caractéristique unique (DE)';


--
-- Name: COLUMN unique_features.name_it; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.unique_features.name_it IS 'Caractéristique unique (IT)';


--
-- Name: COLUMN unique_features.name_es; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.unique_features.name_es IS 'Caractéristique unique (ES)';


--
-- Name: COLUMN unique_features.name_nl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.unique_features.name_nl IS 'Caractéristique unique (NL)';


--
-- Name: COLUMN unique_features.name_pl; Type: COMMENT; Schema: product_attributes; Owner: stoflow_user
--

COMMENT ON COLUMN product_attributes.unique_features.name_pl IS 'Caractéristique unique (PL)';


--
-- Name: vw_dimension_info; Type: VIEW; Schema: product_attributes; Owner: stoflow_user
--

CREATE VIEW product_attributes.vw_dimension_info AS
 SELECT 'dim1'::text AS dimension,
    'Chest / Shoulders'::text AS name_en,
    'Tour de poitrine / Épaules'::text AS name_fr,
    'cm'::text AS unit,
    30 AS min_value,
    80 AS max_value,
    'measurement_width'::text AS vinted_field
UNION ALL
 SELECT 'dim2'::text AS dimension,
    'Total length'::text AS name_en,
    'Longueur totale'::text AS name_fr,
    'cm'::text AS unit,
    40 AS min_value,
    120 AS max_value,
    'measurement_length'::text AS vinted_field
UNION ALL
 SELECT 'dim3'::text AS dimension,
    'Sleeve length'::text AS name_en,
    'Longueur manche'::text AS name_fr,
    'cm'::text AS unit,
    20 AS min_value,
    80 AS max_value,
    NULL::text AS vinted_field
UNION ALL
 SELECT 'dim4'::text AS dimension,
    'Waist'::text AS name_en,
    'Tour de taille'::text AS name_fr,
    'cm'::text AS unit,
    25 AS min_value,
    60 AS max_value,
    NULL::text AS vinted_field
UNION ALL
 SELECT 'dim5'::text AS dimension,
    'Hips'::text AS name_en,
    'Tour de hanches'::text AS name_fr,
    'cm'::text AS unit,
    30 AS min_value,
    80 AS max_value,
    NULL::text AS vinted_field
UNION ALL
 SELECT 'dim6'::text AS dimension,
    'Inseam'::text AS name_en,
    'Entrejambe'::text AS name_fr,
    'cm'::text AS unit,
    20 AS min_value,
    100 AS max_value,
    NULL::text AS vinted_field;


ALTER TABLE product_attributes.vw_dimension_info OWNER TO stoflow_user;

--
-- Name: admin_audit_logs; Type: TABLE; Schema: public; Owner: stoflow_user
--

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


ALTER TABLE public.admin_audit_logs OWNER TO stoflow_user;

--
-- Name: COLUMN admin_audit_logs.action; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.admin_audit_logs.action IS 'Action type: CREATE, UPDATE, DELETE, TOGGLE_ACTIVE, UNLOCK';


--
-- Name: COLUMN admin_audit_logs.resource_type; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.admin_audit_logs.resource_type IS 'Resource type: user, brand, category, color, material';


--
-- Name: COLUMN admin_audit_logs.resource_id; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.admin_audit_logs.resource_id IS 'Primary key of the affected resource';


--
-- Name: COLUMN admin_audit_logs.resource_name; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.admin_audit_logs.resource_name IS 'Human-readable name of the resource';


--
-- Name: COLUMN admin_audit_logs.details; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.admin_audit_logs.details IS 'Changed fields, before/after values';


--
-- Name: COLUMN admin_audit_logs.ip_address; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.admin_audit_logs.ip_address IS 'IP address of the admin';


--
-- Name: COLUMN admin_audit_logs.user_agent; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.admin_audit_logs.user_agent IS 'User agent of the admin browser';


--
-- Name: admin_audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: stoflow_user
--

CREATE SEQUENCE public.admin_audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.admin_audit_logs_id_seq OWNER TO stoflow_user;

--
-- Name: admin_audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: stoflow_user
--

ALTER SEQUENCE public.admin_audit_logs_id_seq OWNED BY public.admin_audit_logs.id;


--
-- Name: ai_credits; Type: TABLE; Schema: public; Owner: stoflow_user
--

CREATE TABLE public.ai_credits (
    id integer NOT NULL,
    user_id integer NOT NULL,
    ai_credits_purchased integer DEFAULT 0 NOT NULL,
    ai_credits_used_this_month integer DEFAULT 0 NOT NULL,
    last_reset_date timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.ai_credits OWNER TO stoflow_user;

--
-- Name: COLUMN ai_credits.user_id; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.ai_credits.user_id IS 'Utilisateur propriétaire';


--
-- Name: COLUMN ai_credits.ai_credits_purchased; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.ai_credits.ai_credits_purchased IS 'Crédits IA achetés (cumulables, ne s''épuisent pas)';


--
-- Name: COLUMN ai_credits.ai_credits_used_this_month; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.ai_credits.ai_credits_used_this_month IS 'Crédits IA utilisés ce mois-ci';


--
-- Name: COLUMN ai_credits.last_reset_date; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.ai_credits.last_reset_date IS 'Date du dernier reset mensuel';


--
-- Name: ai_credits_id_seq; Type: SEQUENCE; Schema: public; Owner: stoflow_user
--

CREATE SEQUENCE public.ai_credits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ai_credits_id_seq OWNER TO stoflow_user;

--
-- Name: ai_credits_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: stoflow_user
--

ALTER SEQUENCE public.ai_credits_id_seq OWNED BY public.ai_credits.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: stoflow_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO stoflow_user;

--
-- Name: clothing_prices; Type: TABLE; Schema: public; Owner: stoflow_user
--

CREATE TABLE public.clothing_prices (
    brand character varying(100) NOT NULL,
    category character varying(255) NOT NULL,
    base_price numeric(10,2) NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_base_price_positive CHECK ((base_price >= (0)::numeric))
);


ALTER TABLE public.clothing_prices OWNER TO stoflow_user;

--
-- Name: TABLE clothing_prices; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON TABLE public.clothing_prices IS 'Prix de base par brand/category pour calcul automatique';


--
-- Name: COLUMN clothing_prices.brand; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.clothing_prices.brand IS 'Marque (FK product_attributes.brands.name)';


--
-- Name: COLUMN clothing_prices.category; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.clothing_prices.category IS 'Catégorie (FK product_attributes.categories.name_en)';


--
-- Name: COLUMN clothing_prices.base_price; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.clothing_prices.base_price IS 'Prix de base en euros';


--
-- Name: COLUMN clothing_prices.updated_at; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.clothing_prices.updated_at IS 'Date de dernière mise à jour du prix';


--
-- Name: doc_articles; Type: TABLE; Schema: public; Owner: stoflow_user
--

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


ALTER TABLE public.doc_articles OWNER TO stoflow_user;

--
-- Name: COLUMN doc_articles.category_id; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.doc_articles.category_id IS 'Parent category ID';


--
-- Name: COLUMN doc_articles.slug; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.doc_articles.slug IS 'URL-friendly identifier';


--
-- Name: COLUMN doc_articles.title; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.doc_articles.title IS 'Article title';


--
-- Name: COLUMN doc_articles.summary; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.doc_articles.summary IS 'Short excerpt';


--
-- Name: COLUMN doc_articles.content; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.doc_articles.content IS 'Markdown content';


--
-- Name: COLUMN doc_articles.display_order; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.doc_articles.display_order IS 'Order within category';


--
-- Name: COLUMN doc_articles.is_active; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.doc_articles.is_active IS 'Whether visible';


--
-- Name: doc_articles_id_seq; Type: SEQUENCE; Schema: public; Owner: stoflow_user
--

CREATE SEQUENCE public.doc_articles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.doc_articles_id_seq OWNER TO stoflow_user;

--
-- Name: doc_articles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: stoflow_user
--

ALTER SEQUENCE public.doc_articles_id_seq OWNED BY public.doc_articles.id;


--
-- Name: doc_categories; Type: TABLE; Schema: public; Owner: stoflow_user
--

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


ALTER TABLE public.doc_categories OWNER TO stoflow_user;

--
-- Name: COLUMN doc_categories.slug; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.doc_categories.slug IS 'URL-friendly identifier';


--
-- Name: COLUMN doc_categories.name; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.doc_categories.name IS 'Display name';


--
-- Name: COLUMN doc_categories.description; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.doc_categories.description IS 'Short description';


--
-- Name: COLUMN doc_categories.icon; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.doc_categories.icon IS 'PrimeIcons class';


--
-- Name: COLUMN doc_categories.display_order; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.doc_categories.display_order IS 'Order in navigation';


--
-- Name: COLUMN doc_categories.is_active; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.doc_categories.is_active IS 'Whether visible';


--
-- Name: doc_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: stoflow_user
--

CREATE SEQUENCE public.doc_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.doc_categories_id_seq OWNER TO stoflow_user;

--
-- Name: doc_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: stoflow_user
--

ALTER SEQUENCE public.doc_categories_id_seq OWNED BY public.doc_categories.id;


--
-- Name: migration_errors; Type: TABLE; Schema: public; Owner: stoflow_user
--

CREATE TABLE public.migration_errors (
    id integer NOT NULL,
    schema_name character varying(100) NOT NULL,
    product_id integer NOT NULL,
    migration_name character varying(255) NOT NULL,
    error_type character varying(100) NOT NULL,
    error_details text,
    migrated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.migration_errors OWNER TO stoflow_user;

--
-- Name: migration_errors_id_seq; Type: SEQUENCE; Schema: public; Owner: stoflow_user
--

CREATE SEQUENCE public.migration_errors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.migration_errors_id_seq OWNER TO stoflow_user;

--
-- Name: migration_errors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: stoflow_user
--

ALTER SEQUENCE public.migration_errors_id_seq OWNED BY public.migration_errors.id;


--
-- Name: permissions; Type: TABLE; Schema: public; Owner: stoflow_user
--

CREATE TABLE public.permissions (
    id integer NOT NULL,
    code character varying(100) NOT NULL,
    name character varying(255) NOT NULL,
    description character varying(500),
    category character varying(50) NOT NULL,
    is_active boolean DEFAULT true NOT NULL
);


ALTER TABLE public.permissions OWNER TO stoflow_user;

--
-- Name: COLUMN permissions.code; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.permissions.code IS 'Unique permission code (e.g., ''products:create'')';


--
-- Name: COLUMN permissions.name; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.permissions.name IS 'Human-readable permission name';


--
-- Name: COLUMN permissions.description; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.permissions.description IS 'Description of what this permission allows';


--
-- Name: COLUMN permissions.category; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.permissions.category IS 'Permission category for grouping';


--
-- Name: COLUMN permissions.is_active; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.permissions.is_active IS 'Whether this permission is active';


--
-- Name: permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: stoflow_user
--

CREATE SEQUENCE public.permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.permissions_id_seq OWNER TO stoflow_user;

--
-- Name: permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: stoflow_user
--

ALTER SEQUENCE public.permissions_id_seq OWNED BY public.permissions.id;


--
-- Name: revoked_tokens; Type: TABLE; Schema: public; Owner: stoflow_user
--

CREATE TABLE public.revoked_tokens (
    token_hash character varying(255) NOT NULL,
    revoked_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL
);


ALTER TABLE public.revoked_tokens OWNER TO stoflow_user;

--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: stoflow_user
--

CREATE TABLE public.role_permissions (
    id integer NOT NULL,
    role public.userrole NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.role_permissions OWNER TO stoflow_user;

--
-- Name: COLUMN role_permissions.role; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.role_permissions.role IS 'User role';


--
-- Name: COLUMN role_permissions.permission_id; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.role_permissions.permission_id IS 'Permission ID';


--
-- Name: role_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: stoflow_user
--

CREATE SEQUENCE public.role_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.role_permissions_id_seq OWNER TO stoflow_user;

--
-- Name: role_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: stoflow_user
--

ALTER SEQUENCE public.role_permissions_id_seq OWNED BY public.role_permissions.id;


--
-- Name: subscription_features; Type: TABLE; Schema: public; Owner: stoflow_user
--

CREATE TABLE public.subscription_features (
    id integer NOT NULL,
    subscription_quota_id integer NOT NULL,
    feature_text character varying(200) NOT NULL,
    display_order integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.subscription_features OWNER TO stoflow_user;

--
-- Name: subscription_features_id_seq; Type: SEQUENCE; Schema: public; Owner: stoflow_user
--

CREATE SEQUENCE public.subscription_features_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.subscription_features_id_seq OWNER TO stoflow_user;

--
-- Name: subscription_features_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: stoflow_user
--

ALTER SEQUENCE public.subscription_features_id_seq OWNED BY public.subscription_features.id;


--
-- Name: subscription_quotas; Type: TABLE; Schema: public; Owner: stoflow_user
--

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


ALTER TABLE public.subscription_quotas OWNER TO stoflow_user;

--
-- Name: COLUMN subscription_quotas.max_products; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.subscription_quotas.max_products IS 'Nombre maximum de produits actifs';


--
-- Name: COLUMN subscription_quotas.max_platforms; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.subscription_quotas.max_platforms IS 'Nombre maximum de plateformes connectées';


--
-- Name: COLUMN subscription_quotas.ai_credits_monthly; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.subscription_quotas.ai_credits_monthly IS 'Crédits IA mensuels';


--
-- Name: COLUMN subscription_quotas.price; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.subscription_quotas.price IS 'Prix mensuel de l''abonnement en euros';


--
-- Name: subscription_quotas_id_seq; Type: SEQUENCE; Schema: public; Owner: stoflow_user
--

CREATE SEQUENCE public.subscription_quotas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.subscription_quotas_id_seq OWNER TO stoflow_user;

--
-- Name: subscription_quotas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: stoflow_user
--

ALTER SEQUENCE public.subscription_quotas_id_seq OWNED BY public.subscription_quotas.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: stoflow_user
--

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


ALTER TABLE public.users OWNER TO stoflow_user;

--
-- Name: COLUMN users.subscription_status; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.subscription_status IS 'active, suspended, cancelled';


--
-- Name: COLUMN users.business_name; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.business_name IS 'Nom de l''entreprise ou de la boutique';


--
-- Name: COLUMN users.account_type; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.account_type IS 'Type de compte: individual (particulier) ou professional (entreprise)';


--
-- Name: COLUMN users.business_type; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.business_type IS 'Type d''activité: resale, dropshipping, artisan, retail, other';


--
-- Name: COLUMN users.estimated_products; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.estimated_products IS 'Nombre de produits estimé: 0-50, 50-200, 200-500, 500+';


--
-- Name: COLUMN users.siret; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.siret IS 'Numéro SIRET (France) - uniquement pour les professionnels';


--
-- Name: COLUMN users.vat_number; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.vat_number IS 'Numéro de TVA intracommunautaire - uniquement pour les professionnels';


--
-- Name: COLUMN users.phone; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.phone IS 'Numéro de téléphone';


--
-- Name: COLUMN users.country; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.country IS 'Code pays ISO 3166-1 alpha-2 (FR, BE, CH, etc.)';


--
-- Name: COLUMN users.language; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.language IS 'Code langue ISO 639-1 (fr, en, etc.)';


--
-- Name: COLUMN users.subscription_tier_id; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.subscription_tier_id IS 'FK vers subscription_quotas';


--
-- Name: COLUMN users.current_products_count; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.current_products_count IS 'Nombre actuel de produits actifs de l''utilisateur';


--
-- Name: COLUMN users.current_platforms_count; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.current_platforms_count IS 'Nombre actuel de plateformes connectées';


--
-- Name: COLUMN users.stripe_customer_id; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.stripe_customer_id IS 'ID du customer Stripe (cus_xxx)';


--
-- Name: COLUMN users.stripe_subscription_id; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.stripe_subscription_id IS 'ID de la subscription Stripe active (sub_xxx)';


--
-- Name: COLUMN users.failed_login_attempts; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.failed_login_attempts IS 'Nombre de tentatives de connexion échouées consécutives';


--
-- Name: COLUMN users.last_failed_login; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.last_failed_login IS 'Date de la dernière tentative de connexion échouée';


--
-- Name: COLUMN users.locked_until; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.locked_until IS 'Date jusqu''à laquelle le compte est verrouillé';


--
-- Name: COLUMN users.email_verified; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.email_verified IS 'Email vérifié par l''utilisateur';


--
-- Name: COLUMN users.email_verification_token; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.email_verification_token IS 'Token de vérification d''email';


--
-- Name: COLUMN users.email_verification_expires; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.email_verification_expires IS 'Date d''expiration du token de vérification';


--
-- Name: COLUMN users.password_changed_at; Type: COMMENT; Schema: public; Owner: stoflow_user
--

COMMENT ON COLUMN public.users.password_changed_at IS 'Date du dernier changement de mot de passe';


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: stoflow_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO stoflow_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: stoflow_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: categories; Type: TABLE; Schema: vinted; Owner: stoflow_user
--

CREATE TABLE vinted.categories (
    id integer NOT NULL,
    code character varying(100),
    title character varying(255) NOT NULL,
    parent_id integer,
    path character varying(500),
    is_leaf boolean DEFAULT false NOT NULL,
    gender character varying(20),
    is_active boolean DEFAULT false NOT NULL
);


ALTER TABLE vinted.categories OWNER TO stoflow_user;

--
-- Name: COLUMN categories.id; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.categories.id IS 'Vinted category ID';


--
-- Name: COLUMN categories.code; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.categories.code IS 'Vinted category code';


--
-- Name: COLUMN categories.title; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.categories.title IS 'Category title';


--
-- Name: COLUMN categories.parent_id; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.categories.parent_id IS 'Parent category ID';


--
-- Name: COLUMN categories.path; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.categories.path IS 'Full path (e.g., Femmes > Vêtements > Jeans)';


--
-- Name: COLUMN categories.is_leaf; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.categories.is_leaf IS 'True if category can be selected for products';


--
-- Name: COLUMN categories.gender; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.categories.gender IS 'Gender: women, men, girls, boys';


--
-- Name: mapping; Type: TABLE; Schema: vinted; Owner: stoflow_user
--

CREATE TABLE vinted.mapping (
    id integer NOT NULL,
    vinted_id integer NOT NULL,
    vinted_gender character varying(20) NOT NULL,
    my_category character varying(100) NOT NULL,
    my_gender character varying(20) NOT NULL,
    my_fit character varying(50),
    my_length character varying(50),
    my_rise character varying(50),
    my_material character varying(50),
    my_pattern character varying(50),
    my_neckline character varying(50),
    my_sleeve_length character varying(50),
    is_default boolean DEFAULT false NOT NULL
);


ALTER TABLE vinted.mapping OWNER TO stoflow_user;

--
-- Name: vw_mapping_issues; Type: VIEW; Schema: public; Owner: stoflow_user
--

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


ALTER TABLE public.vw_mapping_issues OWNER TO stoflow_user;

--
-- Name: ai_generation_logs; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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


ALTER TABLE template_tenant.ai_generation_logs OWNER TO stoflow_user;

--
-- Name: COLUMN ai_generation_logs.product_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ai_generation_logs.product_id IS 'ID du produit (FK products.id)';


--
-- Name: COLUMN ai_generation_logs.model; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ai_generation_logs.model IS 'Modèle utilisé (gpt-4o-mini, etc.)';


--
-- Name: COLUMN ai_generation_logs.prompt_tokens; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ai_generation_logs.prompt_tokens IS 'Tokens utilisés dans le prompt';


--
-- Name: COLUMN ai_generation_logs.completion_tokens; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ai_generation_logs.completion_tokens IS 'Tokens générés dans la réponse';


--
-- Name: COLUMN ai_generation_logs.total_tokens; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ai_generation_logs.total_tokens IS 'Total tokens (prompt + completion)';


--
-- Name: COLUMN ai_generation_logs.total_cost; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ai_generation_logs.total_cost IS 'Coût total en $ (6 decimales)';


--
-- Name: COLUMN ai_generation_logs.cached; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ai_generation_logs.cached IS 'Résultat depuis cache ou API';


--
-- Name: COLUMN ai_generation_logs.generation_time_ms; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ai_generation_logs.generation_time_ms IS 'Temps de génération en ms';


--
-- Name: COLUMN ai_generation_logs.error_message; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ai_generation_logs.error_message IS 'Message d''erreur si échec';


--
-- Name: ai_generation_logs_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.ai_generation_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.ai_generation_logs_id_seq OWNER TO stoflow_user;

--
-- Name: ai_generation_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.ai_generation_logs_id_seq OWNED BY template_tenant.ai_generation_logs.id;


--
-- Name: batch_jobs; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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


ALTER TABLE template_tenant.batch_jobs OWNER TO stoflow_user;

--
-- Name: TABLE batch_jobs; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON TABLE template_tenant.batch_jobs IS 'Groups multiple marketplace jobs into a single batch operation';


--
-- Name: batch_jobs_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.batch_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.batch_jobs_id_seq OWNER TO stoflow_user;

--
-- Name: batch_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.batch_jobs_id_seq OWNED BY template_tenant.batch_jobs.id;


--
-- Name: ebay_credentials; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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


ALTER TABLE template_tenant.ebay_credentials OWNER TO stoflow_user;

--
-- Name: COLUMN ebay_credentials.ebay_user_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.ebay_user_id IS 'ID utilisateur eBay';


--
-- Name: COLUMN ebay_credentials.access_token; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.access_token IS 'OAuth2 Access Token (expire 2h)';


--
-- Name: COLUMN ebay_credentials.refresh_token; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.refresh_token IS 'OAuth2 Refresh Token (expire 18 mois)';


--
-- Name: COLUMN ebay_credentials.access_token_expires_at; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.access_token_expires_at IS 'Date d''expiration du access_token';


--
-- Name: COLUMN ebay_credentials.refresh_token_expires_at; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.refresh_token_expires_at IS 'Date d''expiration du refresh_token';


--
-- Name: COLUMN ebay_credentials.sandbox_mode; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.sandbox_mode IS 'True si utilise eBay Sandbox';


--
-- Name: COLUMN ebay_credentials.is_connected; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.is_connected IS 'True si les credentials sont valides';


--
-- Name: COLUMN ebay_credentials.last_sync; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.last_sync IS 'Dernière synchronisation réussie';


--
-- Name: COLUMN ebay_credentials.username; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.username IS 'Username eBay (ex: shop.ton.outfit)';


--
-- Name: COLUMN ebay_credentials.email; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.email IS 'Email du compte eBay';


--
-- Name: COLUMN ebay_credentials.account_type; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.account_type IS 'Type de compte: BUSINESS ou INDIVIDUAL';


--
-- Name: COLUMN ebay_credentials.business_name; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.business_name IS 'Nom de l''entreprise (si BUSINESS)';


--
-- Name: COLUMN ebay_credentials.first_name; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.first_name IS 'Prénom (si INDIVIDUAL)';


--
-- Name: COLUMN ebay_credentials.last_name; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.last_name IS 'Nom (si INDIVIDUAL)';


--
-- Name: COLUMN ebay_credentials.phone; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.phone IS 'Numéro de téléphone';


--
-- Name: COLUMN ebay_credentials.address; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.address IS 'Adresse complète';


--
-- Name: COLUMN ebay_credentials.marketplace; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.marketplace IS 'Marketplace d''inscription (EBAY_FR, EBAY_US, etc.)';


--
-- Name: COLUMN ebay_credentials.feedback_score; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.feedback_score IS 'Score de feedback';


--
-- Name: COLUMN ebay_credentials.feedback_percentage; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.feedback_percentage IS 'Pourcentage de feedback positif';


--
-- Name: COLUMN ebay_credentials.seller_level; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.seller_level IS 'Niveau vendeur (top_rated, above_standard, standard, below_standard)';


--
-- Name: COLUMN ebay_credentials.registration_date; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_credentials.registration_date IS 'Date d''inscription sur eBay';


--
-- Name: ebay_credentials_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.ebay_credentials_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.ebay_credentials_id_seq OWNER TO stoflow_user;

--
-- Name: ebay_credentials_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.ebay_credentials_id_seq OWNED BY template_tenant.ebay_credentials.id;


--
-- Name: ebay_orders; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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


ALTER TABLE template_tenant.ebay_orders OWNER TO stoflow_user;

--
-- Name: ebay_orders_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.ebay_orders_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.ebay_orders_id_seq OWNER TO stoflow_user;

--
-- Name: ebay_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.ebay_orders_id_seq OWNED BY template_tenant.ebay_orders.id;


--
-- Name: ebay_orders_products; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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


ALTER TABLE template_tenant.ebay_orders_products OWNER TO stoflow_user;

--
-- Name: ebay_orders_products_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.ebay_orders_products_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.ebay_orders_products_id_seq OWNER TO stoflow_user;

--
-- Name: ebay_orders_products_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.ebay_orders_products_id_seq OWNED BY template_tenant.ebay_orders_products.id;


--
-- Name: ebay_products; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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
    category_name character varying(255),
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
    location character varying(100),
    country character varying(2),
    published_at timestamp with time zone,
    last_synced_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE template_tenant.ebay_products OWNER TO stoflow_user;

--
-- Name: TABLE ebay_products; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON TABLE template_tenant.ebay_products IS 'Produits eBay importés depuis Inventory API';


--
-- Name: COLUMN ebay_products.ebay_sku; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_products.ebay_sku IS 'SKU unique eBay (inventory item)';


--
-- Name: COLUMN ebay_products.product_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_products.product_id IS 'FK optionnelle vers Product Stoflow (1:1)';


--
-- Name: COLUMN ebay_products.image_urls; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_products.image_urls IS 'JSON des URLs d images';


--
-- Name: COLUMN ebay_products.aspects; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.ebay_products.aspects IS 'JSON des aspects eBay (Brand, Color, Size, etc.)';


--
-- Name: ebay_products_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.ebay_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.ebay_products_id_seq OWNER TO stoflow_user;

--
-- Name: ebay_products_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.ebay_products_id_seq OWNED BY template_tenant.ebay_products.id;


--
-- Name: ebay_products_marketplace; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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


ALTER TABLE template_tenant.ebay_products_marketplace OWNER TO stoflow_user;

--
-- Name: ebay_promoted_listings; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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


ALTER TABLE template_tenant.ebay_promoted_listings OWNER TO stoflow_user;

--
-- Name: ebay_promoted_listings_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.ebay_promoted_listings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.ebay_promoted_listings_id_seq OWNER TO stoflow_user;

--
-- Name: ebay_promoted_listings_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.ebay_promoted_listings_id_seq OWNED BY template_tenant.ebay_promoted_listings.id;


--
-- Name: etsy_credentials; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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


ALTER TABLE template_tenant.etsy_credentials OWNER TO stoflow_user;

--
-- Name: etsy_credentials_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.etsy_credentials_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.etsy_credentials_id_seq OWNER TO stoflow_user;

--
-- Name: etsy_credentials_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.etsy_credentials_id_seq OWNED BY template_tenant.etsy_credentials.id;


--
-- Name: marketplace_jobs; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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
    idempotency_key character varying(64),
    CONSTRAINT valid_status CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'running'::character varying, 'paused'::character varying, 'completed'::character varying, 'failed'::character varying, 'cancelled'::character varying, 'expired'::character varying])::text[])))
);


ALTER TABLE template_tenant.marketplace_jobs OWNER TO stoflow_user;

--
-- Name: COLUMN marketplace_jobs.idempotency_key; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.marketplace_jobs.idempotency_key IS 'Unique key to prevent duplicate publications (format: pub_<product_id>_<uuid>)';


--
-- Name: marketplace_tasks; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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


ALTER TABLE template_tenant.marketplace_tasks OWNER TO stoflow_user;

--
-- Name: pending_instructions; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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


ALTER TABLE template_tenant.pending_instructions OWNER TO stoflow_user;

--
-- Name: plugin_tasks_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.plugin_tasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.plugin_tasks_id_seq OWNER TO stoflow_user;

--
-- Name: plugin_tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.plugin_tasks_id_seq OWNED BY template_tenant.marketplace_tasks.id;


--
-- Name: product_colors; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

CREATE TABLE template_tenant.product_colors (
    product_id integer NOT NULL,
    color character varying(100) NOT NULL,
    is_primary boolean DEFAULT false NOT NULL
);


ALTER TABLE template_tenant.product_colors OWNER TO stoflow_user;

--
-- Name: product_condition_sups; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

CREATE TABLE template_tenant.product_condition_sups (
    product_id integer NOT NULL,
    condition_sup character varying(100) NOT NULL
);


ALTER TABLE template_tenant.product_condition_sups OWNER TO stoflow_user;

--
-- Name: product_images; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

CREATE TABLE template_tenant.product_images (
    id integer NOT NULL,
    product_id integer NOT NULL,
    image_path character varying(1000) NOT NULL,
    display_order integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE template_tenant.product_images OWNER TO stoflow_user;

--
-- Name: COLUMN product_images.product_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.product_images.product_id IS 'ID du produit (FK products.id, cascade delete)';


--
-- Name: COLUMN product_images.image_path; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.product_images.image_path IS 'Chemin relatif de l''image';


--
-- Name: COLUMN product_images.display_order; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.product_images.display_order IS 'Ordre d''affichage (0 = première)';


--
-- Name: product_images_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.product_images_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.product_images_id_seq OWNER TO stoflow_user;

--
-- Name: product_images_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.product_images_id_seq OWNED BY template_tenant.product_images.id;


--
-- Name: product_materials; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

CREATE TABLE template_tenant.product_materials (
    product_id integer NOT NULL,
    material character varying(100) NOT NULL,
    percentage integer,
    CONSTRAINT product_materials_percentage_check CHECK (((percentage >= 0) AND (percentage <= 100)))
);


ALTER TABLE template_tenant.product_materials OWNER TO stoflow_user;

--
-- Name: products; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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


ALTER TABLE template_tenant.products OWNER TO stoflow_user;

--
-- Name: COLUMN products.sku; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.sku IS 'SKU du produit';


--
-- Name: COLUMN products.title; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.title IS 'Titre du produit';


--
-- Name: COLUMN products.description; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.description IS 'Description complète';


--
-- Name: COLUMN products.price; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.price IS 'Prix de vente';


--
-- Name: COLUMN products.category; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.category IS 'Catégorie (FK product_attributes.categories.name_en)';


--
-- Name: COLUMN products.brand; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.brand IS 'Marque (FK product_attributes.brands.name)';


--
-- Name: COLUMN products.size_original; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.size_original IS 'Taille étiquette (FK product_attributes.sizes.name_en)';


--
-- Name: COLUMN products.fit; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.fit IS 'Coupe (FK product_attributes.fits.name_en)';


--
-- Name: COLUMN products.gender; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.gender IS 'Genre (FK product_attributes.genders.name_en)';


--
-- Name: COLUMN products.season; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.season IS 'Saison (FK product_attributes.seasons.name_en)';


--
-- Name: COLUMN products.rise; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.rise IS 'Hauteur de taille (pantalons)';


--
-- Name: COLUMN products.closure; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.closure IS 'Type de fermeture';


--
-- Name: COLUMN products.sleeve_length; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.sleeve_length IS 'Longueur de manche';


--
-- Name: COLUMN products.origin; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.origin IS 'Origine/provenance';


--
-- Name: COLUMN products.decade; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.decade IS 'Décennie (vintage)';


--
-- Name: COLUMN products.trend; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.trend IS 'Tendance';


--
-- Name: COLUMN products.location; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.location IS 'Localisation';


--
-- Name: COLUMN products.model; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.model IS 'Modèle';


--
-- Name: COLUMN products.dim1; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.dim1 IS 'Dimension 1 (cm)';


--
-- Name: COLUMN products.dim2; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.dim2 IS 'Dimension 2 (cm)';


--
-- Name: COLUMN products.dim3; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.dim3 IS 'Dimension 3 (cm)';


--
-- Name: COLUMN products.dim4; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.dim4 IS 'Dimension 4 (cm)';


--
-- Name: COLUMN products.dim5; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.dim5 IS 'Dimension 5 (cm)';


--
-- Name: COLUMN products.dim6; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.dim6 IS 'Dimension 6 (cm)';


--
-- Name: COLUMN products.images; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.images IS 'Images URLs (JSON array)';


--
-- Name: COLUMN products.pricing_edit; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.pricing_edit IS 'Édition limitée/exclusive';


--
-- Name: COLUMN products.pricing_rarity; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.pricing_rarity IS 'Rareté du produit';


--
-- Name: COLUMN products.pricing_quality; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.pricing_quality IS 'Qualité exceptionnelle';


--
-- Name: COLUMN products.pricing_details; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.pricing_details IS 'Détails valorisants';


--
-- Name: COLUMN products.pricing_style; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.pricing_style IS 'Style iconique';


--
-- Name: COLUMN products.marking; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.marking IS 'Marquages/logos';


--
-- Name: COLUMN products.sport; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.sport IS 'Sport (FK product_attributes.sports)';


--
-- Name: COLUMN products.neckline; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.neckline IS 'Encolure (FK product_attributes.necklines)';


--
-- Name: COLUMN products.length; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.length IS 'Longueur (FK product_attributes.lengths)';


--
-- Name: COLUMN products.pattern; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.products.pattern IS 'Motif (FK product_attributes.patterns)';


--
-- Name: products_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.products_id_seq OWNER TO stoflow_user;

--
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.products_id_seq OWNED BY template_tenant.products.id;


--
-- Name: publication_history; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

CREATE TABLE template_tenant.publication_history (
    id integer NOT NULL,
    product_id integer NOT NULL,
    status public.publication_status NOT NULL,
    platform_product_id character varying(100),
    error_message text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE template_tenant.publication_history OWNER TO stoflow_user;

--
-- Name: COLUMN publication_history.product_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.publication_history.product_id IS 'ID du produit (FK products.id)';


--
-- Name: COLUMN publication_history.status; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.publication_history.status IS 'Statut de la publication';


--
-- Name: COLUMN publication_history.platform_product_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.publication_history.platform_product_id IS 'ID du produit sur la plateforme';


--
-- Name: COLUMN publication_history.error_message; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.publication_history.error_message IS 'Message d''erreur si échec';


--
-- Name: COLUMN publication_history.metadata; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.publication_history.metadata IS 'Métadonnées supplémentaires';


--
-- Name: publication_history_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.publication_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.publication_history_id_seq OWNER TO stoflow_user;

--
-- Name: publication_history_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.publication_history_id_seq OWNED BY template_tenant.publication_history.id;


--
-- Name: vinted_connection; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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


ALTER TABLE template_tenant.vinted_connection OWNER TO stoflow_user;

--
-- Name: COLUMN vinted_connection.vinted_user_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_connection.vinted_user_id IS 'ID utilisateur Vinted (PK)';


--
-- Name: COLUMN vinted_connection.login; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_connection.login IS 'Login/username Vinted';


--
-- Name: COLUMN vinted_connection.user_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_connection.user_id IS 'FK vers public.users.id';


--
-- Name: vinted_connection_vinted_user_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.vinted_connection_vinted_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.vinted_connection_vinted_user_id_seq OWNER TO stoflow_user;

--
-- Name: vinted_connection_vinted_user_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.vinted_connection_vinted_user_id_seq OWNED BY template_tenant.vinted_connection.vinted_user_id;


--
-- Name: vinted_conversations; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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


ALTER TABLE template_tenant.vinted_conversations OWNER TO stoflow_user;

--
-- Name: COLUMN vinted_conversations.conversation_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_conversations.conversation_id IS 'Vinted conversation ID (PK)';


--
-- Name: COLUMN vinted_conversations.opposite_user_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_conversations.opposite_user_id IS 'Other participant Vinted ID';


--
-- Name: COLUMN vinted_conversations.opposite_user_login; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_conversations.opposite_user_login IS 'Other participant username';


--
-- Name: COLUMN vinted_conversations.opposite_user_photo_url; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_conversations.opposite_user_photo_url IS 'Other participant avatar URL';


--
-- Name: COLUMN vinted_conversations.last_message_preview; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_conversations.last_message_preview IS 'Preview of last message';


--
-- Name: COLUMN vinted_conversations.is_unread; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_conversations.is_unread IS 'Has unread messages';


--
-- Name: COLUMN vinted_conversations.unread_count; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_conversations.unread_count IS 'Number of unread messages';


--
-- Name: COLUMN vinted_conversations.item_count; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_conversations.item_count IS 'Number of items in conversation';


--
-- Name: COLUMN vinted_conversations.item_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_conversations.item_id IS 'Main item Vinted ID';


--
-- Name: COLUMN vinted_conversations.item_title; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_conversations.item_title IS 'Main item title';


--
-- Name: COLUMN vinted_conversations.item_photo_url; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_conversations.item_photo_url IS 'Main item photo URL';


--
-- Name: COLUMN vinted_conversations.transaction_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_conversations.transaction_id IS 'Linked transaction ID';


--
-- Name: COLUMN vinted_conversations.updated_at_vinted; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_conversations.updated_at_vinted IS 'Last update on Vinted';


--
-- Name: COLUMN vinted_conversations.created_at; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_conversations.created_at IS 'Local creation date';


--
-- Name: COLUMN vinted_conversations.updated_at; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_conversations.updated_at IS 'Local update date';


--
-- Name: COLUMN vinted_conversations.last_synced_at; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_conversations.last_synced_at IS 'Last sync with Vinted';


--
-- Name: vinted_conversations_conversation_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.vinted_conversations_conversation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.vinted_conversations_conversation_id_seq OWNER TO stoflow_user;

--
-- Name: vinted_conversations_conversation_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.vinted_conversations_conversation_id_seq OWNED BY template_tenant.vinted_conversations.conversation_id;


--
-- Name: vinted_error_logs; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

CREATE TABLE template_tenant.vinted_error_logs (
    id integer NOT NULL,
    product_id integer NOT NULL,
    operation character varying(20) NOT NULL,
    error_type character varying(50) NOT NULL,
    error_message text NOT NULL,
    error_details text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE template_tenant.vinted_error_logs OWNER TO stoflow_user;

--
-- Name: COLUMN vinted_error_logs.operation; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_error_logs.operation IS 'Type d''opération: publish, update, delete';


--
-- Name: COLUMN vinted_error_logs.error_type; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_error_logs.error_type IS 'Type d''erreur: mapping_error, api_error, image_error, validation_error';


--
-- Name: COLUMN vinted_error_logs.error_message; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_error_logs.error_message IS 'Message d''erreur principal';


--
-- Name: COLUMN vinted_error_logs.error_details; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_error_logs.error_details IS 'Détails supplémentaires (JSON, traceback, etc.)';


--
-- Name: vinted_error_logs_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.vinted_error_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.vinted_error_logs_id_seq OWNER TO stoflow_user;

--
-- Name: vinted_error_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.vinted_error_logs_id_seq OWNED BY template_tenant.vinted_error_logs.id;


--
-- Name: vinted_job_stats; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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


ALTER TABLE template_tenant.vinted_job_stats OWNER TO stoflow_user;

--
-- Name: vinted_job_stats_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.vinted_job_stats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.vinted_job_stats_id_seq OWNER TO stoflow_user;

--
-- Name: vinted_job_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.vinted_job_stats_id_seq OWNED BY template_tenant.vinted_job_stats.id;


--
-- Name: vinted_jobs_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.vinted_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.vinted_jobs_id_seq OWNER TO stoflow_user;

--
-- Name: vinted_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.vinted_jobs_id_seq OWNED BY template_tenant.marketplace_jobs.id;


--
-- Name: vinted_messages; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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


ALTER TABLE template_tenant.vinted_messages OWNER TO stoflow_user;

--
-- Name: COLUMN vinted_messages.conversation_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_messages.conversation_id IS 'FK to vinted_conversations';


--
-- Name: COLUMN vinted_messages.vinted_message_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_messages.vinted_message_id IS 'Vinted message ID';


--
-- Name: COLUMN vinted_messages.entity_type; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_messages.entity_type IS 'message, offer_request_message, status_message, action_message';


--
-- Name: COLUMN vinted_messages.sender_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_messages.sender_id IS 'Sender Vinted ID';


--
-- Name: COLUMN vinted_messages.sender_login; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_messages.sender_login IS 'Sender username';


--
-- Name: COLUMN vinted_messages.body; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_messages.body IS 'Message text content';


--
-- Name: COLUMN vinted_messages.title; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_messages.title IS 'Title for status/action messages';


--
-- Name: COLUMN vinted_messages.subtitle; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_messages.subtitle IS 'Subtitle for status/action messages';


--
-- Name: COLUMN vinted_messages.offer_price; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_messages.offer_price IS 'Offer price (e.g., 8.0)';


--
-- Name: COLUMN vinted_messages.offer_status; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_messages.offer_status IS 'Offer status title';


--
-- Name: COLUMN vinted_messages.is_from_current_user; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_messages.is_from_current_user IS 'Sent by current user';


--
-- Name: COLUMN vinted_messages.created_at_vinted; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_messages.created_at_vinted IS 'Creation time on Vinted';


--
-- Name: vinted_messages_id_seq; Type: SEQUENCE; Schema: template_tenant; Owner: stoflow_user
--

CREATE SEQUENCE template_tenant.vinted_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE template_tenant.vinted_messages_id_seq OWNER TO stoflow_user;

--
-- Name: vinted_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: template_tenant; Owner: stoflow_user
--

ALTER SEQUENCE template_tenant.vinted_messages_id_seq OWNED BY template_tenant.vinted_messages.id;


--
-- Name: vinted_products; Type: TABLE; Schema: template_tenant; Owner: stoflow_user
--

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


ALTER TABLE template_tenant.vinted_products OWNER TO stoflow_user;

--
-- Name: TABLE vinted_products; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON TABLE template_tenant.vinted_products IS 'Produits Vinted (standalone, pas de FK vers products)';


--
-- Name: COLUMN vinted_products.vinted_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.vinted_id IS 'ID unique Vinted';


--
-- Name: COLUMN vinted_products.photos_data; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.photos_data IS 'JSON des photos [{id, url, ...}]';


--
-- Name: COLUMN vinted_products.total_price; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.total_price IS 'Prix total avec frais';


--
-- Name: COLUMN vinted_products.brand_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.brand_id IS 'ID Vinted de la marque';


--
-- Name: COLUMN vinted_products.size_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.size_id IS 'ID Vinted de la taille';


--
-- Name: COLUMN vinted_products.catalog_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.catalog_id IS 'ID Vinted de la catégorie';


--
-- Name: COLUMN vinted_products.condition_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.condition_id IS 'ID Vinted de létat';


--
-- Name: COLUMN vinted_products.material; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.material IS 'Matière';


--
-- Name: COLUMN vinted_products.measurements; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.measurements IS 'Dimensions texte (l X cm / L Y cm)';


--
-- Name: COLUMN vinted_products.measurement_width; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.measurement_width IS 'Largeur en cm';


--
-- Name: COLUMN vinted_products.measurement_length; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.measurement_length IS 'Longueur en cm';


--
-- Name: COLUMN vinted_products.manufacturer_labelling; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.manufacturer_labelling IS 'Étiquetage du fabricant';


--
-- Name: COLUMN vinted_products.is_reserved; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.is_reserved IS 'Est réservé';


--
-- Name: COLUMN vinted_products.is_hidden; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.is_hidden IS 'Est masqué';


--
-- Name: COLUMN vinted_products.seller_id; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.seller_id IS 'ID vendeur Vinted';


--
-- Name: COLUMN vinted_products.seller_login; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.seller_login IS 'Login vendeur';


--
-- Name: COLUMN vinted_products.service_fee; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.service_fee IS 'Frais de service';


--
-- Name: COLUMN vinted_products.buyer_protection_fee; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.buyer_protection_fee IS 'Frais protection acheteur';


--
-- Name: COLUMN vinted_products.shipping_price; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.shipping_price IS 'Frais de port';


--
-- Name: COLUMN vinted_products.published_at; Type: COMMENT; Schema: template_tenant; Owner: stoflow_user
--

COMMENT ON COLUMN template_tenant.vinted_products.published_at IS 'Date de publication sur Vinted (from image timestamp)';


--
-- Name: ai_generation_logs; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.ai_generation_logs (
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


ALTER TABLE user_1.ai_generation_logs OWNER TO stoflow_user;

--
-- Name: COLUMN ai_generation_logs.product_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ai_generation_logs.product_id IS 'ID du produit (FK products.id)';


--
-- Name: COLUMN ai_generation_logs.model; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ai_generation_logs.model IS 'Modèle utilisé (gpt-4o-mini, etc.)';


--
-- Name: COLUMN ai_generation_logs.prompt_tokens; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ai_generation_logs.prompt_tokens IS 'Tokens utilisés dans le prompt';


--
-- Name: COLUMN ai_generation_logs.completion_tokens; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ai_generation_logs.completion_tokens IS 'Tokens générés dans la réponse';


--
-- Name: COLUMN ai_generation_logs.total_tokens; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ai_generation_logs.total_tokens IS 'Total tokens (prompt + completion)';


--
-- Name: COLUMN ai_generation_logs.total_cost; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ai_generation_logs.total_cost IS 'Coût total en $ (6 decimales)';


--
-- Name: COLUMN ai_generation_logs.cached; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ai_generation_logs.cached IS 'Résultat depuis cache ou API';


--
-- Name: COLUMN ai_generation_logs.generation_time_ms; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ai_generation_logs.generation_time_ms IS 'Temps de génération en ms';


--
-- Name: COLUMN ai_generation_logs.error_message; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ai_generation_logs.error_message IS 'Message d''erreur si échec';


--
-- Name: ai_generation_logs_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.ai_generation_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.ai_generation_logs_id_seq OWNER TO stoflow_user;

--
-- Name: ai_generation_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.ai_generation_logs_id_seq OWNED BY user_1.ai_generation_logs.id;


--
-- Name: batch_jobs; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.batch_jobs (
    id integer NOT NULL,
    batch_id character varying(100) NOT NULL,
    marketplace character varying(50) NOT NULL,
    action_code character varying(50) NOT NULL,
    total_count integer DEFAULT 0 NOT NULL,
    completed_count integer DEFAULT 0 NOT NULL,
    failed_count integer DEFAULT 0 NOT NULL,
    cancelled_count integer DEFAULT 0 NOT NULL,
    status user_1.batch_job_status DEFAULT 'pending'::user_1.batch_job_status NOT NULL,
    priority integer DEFAULT 3 NOT NULL,
    created_by_user_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone
);


ALTER TABLE user_1.batch_jobs OWNER TO stoflow_user;

--
-- Name: TABLE batch_jobs; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON TABLE user_1.batch_jobs IS 'Groups multiple marketplace jobs into a single batch operation';


--
-- Name: batch_jobs_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.batch_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.batch_jobs_id_seq OWNER TO stoflow_user;

--
-- Name: batch_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.batch_jobs_id_seq OWNED BY user_1.batch_jobs.id;


--
-- Name: ebay_credentials; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.ebay_credentials (
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


ALTER TABLE user_1.ebay_credentials OWNER TO stoflow_user;

--
-- Name: COLUMN ebay_credentials.ebay_user_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.ebay_user_id IS 'ID utilisateur eBay';


--
-- Name: COLUMN ebay_credentials.access_token; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.access_token IS 'OAuth2 Access Token (expire 2h)';


--
-- Name: COLUMN ebay_credentials.refresh_token; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.refresh_token IS 'OAuth2 Refresh Token (expire 18 mois)';


--
-- Name: COLUMN ebay_credentials.access_token_expires_at; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.access_token_expires_at IS 'Date d''expiration du access_token';


--
-- Name: COLUMN ebay_credentials.refresh_token_expires_at; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.refresh_token_expires_at IS 'Date d''expiration du refresh_token';


--
-- Name: COLUMN ebay_credentials.sandbox_mode; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.sandbox_mode IS 'True si utilise eBay Sandbox';


--
-- Name: COLUMN ebay_credentials.is_connected; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.is_connected IS 'True si les credentials sont valides';


--
-- Name: COLUMN ebay_credentials.last_sync; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.last_sync IS 'Dernière synchronisation réussie';


--
-- Name: COLUMN ebay_credentials.username; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.username IS 'Username eBay (ex: shop.ton.outfit)';


--
-- Name: COLUMN ebay_credentials.email; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.email IS 'Email du compte eBay';


--
-- Name: COLUMN ebay_credentials.account_type; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.account_type IS 'Type de compte: BUSINESS ou INDIVIDUAL';


--
-- Name: COLUMN ebay_credentials.business_name; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.business_name IS 'Nom de l''entreprise (si BUSINESS)';


--
-- Name: COLUMN ebay_credentials.first_name; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.first_name IS 'Prénom (si INDIVIDUAL)';


--
-- Name: COLUMN ebay_credentials.last_name; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.last_name IS 'Nom (si INDIVIDUAL)';


--
-- Name: COLUMN ebay_credentials.phone; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.phone IS 'Numéro de téléphone';


--
-- Name: COLUMN ebay_credentials.address; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.address IS 'Adresse complète';


--
-- Name: COLUMN ebay_credentials.marketplace; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.marketplace IS 'Marketplace d''inscription (EBAY_FR, EBAY_US, etc.)';


--
-- Name: COLUMN ebay_credentials.feedback_score; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.feedback_score IS 'Score de feedback';


--
-- Name: COLUMN ebay_credentials.feedback_percentage; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.feedback_percentage IS 'Pourcentage de feedback positif';


--
-- Name: COLUMN ebay_credentials.seller_level; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.seller_level IS 'Niveau vendeur (top_rated, above_standard, standard, below_standard)';


--
-- Name: COLUMN ebay_credentials.registration_date; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_credentials.registration_date IS 'Date d''inscription sur eBay';


--
-- Name: ebay_credentials_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.ebay_credentials_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.ebay_credentials_id_seq OWNER TO stoflow_user;

--
-- Name: ebay_credentials_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.ebay_credentials_id_seq OWNED BY user_1.ebay_credentials.id;


--
-- Name: ebay_orders; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.ebay_orders (
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


ALTER TABLE user_1.ebay_orders OWNER TO stoflow_user;

--
-- Name: ebay_orders_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.ebay_orders_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.ebay_orders_id_seq OWNER TO stoflow_user;

--
-- Name: ebay_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.ebay_orders_id_seq OWNED BY user_1.ebay_orders.id;


--
-- Name: ebay_orders_products; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.ebay_orders_products (
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


ALTER TABLE user_1.ebay_orders_products OWNER TO stoflow_user;

--
-- Name: ebay_orders_products_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.ebay_orders_products_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.ebay_orders_products_id_seq OWNER TO stoflow_user;

--
-- Name: ebay_orders_products_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.ebay_orders_products_id_seq OWNED BY user_1.ebay_orders_products.id;


--
-- Name: ebay_products; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.ebay_products (
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
    category_name character varying(255),
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
    location character varying(100),
    country character varying(2),
    published_at timestamp with time zone,
    last_synced_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE user_1.ebay_products OWNER TO stoflow_user;

--
-- Name: TABLE ebay_products; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON TABLE user_1.ebay_products IS 'Produits eBay importés depuis Inventory API';


--
-- Name: COLUMN ebay_products.ebay_sku; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_products.ebay_sku IS 'SKU unique eBay (inventory item)';


--
-- Name: COLUMN ebay_products.product_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_products.product_id IS 'FK optionnelle vers Product Stoflow (1:1)';


--
-- Name: COLUMN ebay_products.image_urls; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_products.image_urls IS 'JSON des URLs d images';


--
-- Name: COLUMN ebay_products.aspects; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.ebay_products.aspects IS 'JSON des aspects eBay (Brand, Color, Size, etc.)';


--
-- Name: ebay_products_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.ebay_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.ebay_products_id_seq OWNER TO stoflow_user;

--
-- Name: ebay_products_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.ebay_products_id_seq OWNED BY user_1.ebay_products.id;


--
-- Name: ebay_products_marketplace; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.ebay_products_marketplace (
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


ALTER TABLE user_1.ebay_products_marketplace OWNER TO stoflow_user;

--
-- Name: ebay_promoted_listings; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.ebay_promoted_listings (
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


ALTER TABLE user_1.ebay_promoted_listings OWNER TO stoflow_user;

--
-- Name: ebay_promoted_listings_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.ebay_promoted_listings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.ebay_promoted_listings_id_seq OWNER TO stoflow_user;

--
-- Name: ebay_promoted_listings_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.ebay_promoted_listings_id_seq OWNED BY user_1.ebay_promoted_listings.id;


--
-- Name: etsy_credentials; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.etsy_credentials (
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


ALTER TABLE user_1.etsy_credentials OWNER TO stoflow_user;

--
-- Name: etsy_credentials_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.etsy_credentials_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.etsy_credentials_id_seq OWNER TO stoflow_user;

--
-- Name: etsy_credentials_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.etsy_credentials_id_seq OWNED BY user_1.etsy_credentials.id;


--
-- Name: marketplace_jobs; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.marketplace_jobs (
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
    idempotency_key character varying(64),
    CONSTRAINT valid_status CHECK (((status)::text = ANY (ARRAY[('pending'::character varying)::text, ('running'::character varying)::text, ('paused'::character varying)::text, ('completed'::character varying)::text, ('failed'::character varying)::text, ('cancelled'::character varying)::text, ('expired'::character varying)::text])))
);


ALTER TABLE user_1.marketplace_jobs OWNER TO stoflow_user;

--
-- Name: COLUMN marketplace_jobs.idempotency_key; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.marketplace_jobs.idempotency_key IS 'Unique key to prevent duplicate publications (format: pub_<product_id>_<uuid>)';


--
-- Name: marketplace_tasks; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.marketplace_tasks (
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


ALTER TABLE user_1.marketplace_tasks OWNER TO stoflow_user;

--
-- Name: pending_instructions; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.pending_instructions (
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


ALTER TABLE user_1.pending_instructions OWNER TO stoflow_user;

--
-- Name: plugin_tasks_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.plugin_tasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.plugin_tasks_id_seq OWNER TO stoflow_user;

--
-- Name: plugin_tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.plugin_tasks_id_seq OWNED BY user_1.marketplace_tasks.id;


--
-- Name: product_colors; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.product_colors (
    product_id integer NOT NULL,
    color character varying(100) NOT NULL,
    is_primary boolean DEFAULT false NOT NULL
);


ALTER TABLE user_1.product_colors OWNER TO stoflow_user;

--
-- Name: product_condition_sups; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.product_condition_sups (
    product_id integer NOT NULL,
    condition_sup character varying(100) NOT NULL
);


ALTER TABLE user_1.product_condition_sups OWNER TO stoflow_user;

--
-- Name: product_images; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.product_images (
    id integer NOT NULL,
    product_id integer NOT NULL,
    image_path character varying(1000) NOT NULL,
    display_order integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE user_1.product_images OWNER TO stoflow_user;

--
-- Name: COLUMN product_images.product_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.product_images.product_id IS 'ID du produit (FK products.id, cascade delete)';


--
-- Name: COLUMN product_images.image_path; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.product_images.image_path IS 'Chemin relatif de l''image';


--
-- Name: COLUMN product_images.display_order; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.product_images.display_order IS 'Ordre d''affichage (0 = première)';


--
-- Name: product_images_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.product_images_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.product_images_id_seq OWNER TO stoflow_user;

--
-- Name: product_images_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.product_images_id_seq OWNED BY user_1.product_images.id;


--
-- Name: product_materials; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.product_materials (
    product_id integer NOT NULL,
    material character varying(100) NOT NULL,
    percentage integer,
    CONSTRAINT product_materials_percentage_check CHECK (((percentage >= 0) AND (percentage <= 100)))
);


ALTER TABLE user_1.product_materials OWNER TO stoflow_user;

--
-- Name: products; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.products (
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


ALTER TABLE user_1.products OWNER TO stoflow_user;

--
-- Name: COLUMN products.sku; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.sku IS 'SKU du produit';


--
-- Name: COLUMN products.title; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.title IS 'Titre du produit';


--
-- Name: COLUMN products.description; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.description IS 'Description complète';


--
-- Name: COLUMN products.price; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.price IS 'Prix de vente';


--
-- Name: COLUMN products.category; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.category IS 'Catégorie (FK product_attributes.categories.name_en)';


--
-- Name: COLUMN products.brand; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.brand IS 'Marque (FK product_attributes.brands.name)';


--
-- Name: COLUMN products.size_original; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.size_original IS 'Taille étiquette (FK product_attributes.sizes.name_en)';


--
-- Name: COLUMN products.fit; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.fit IS 'Coupe (FK product_attributes.fits.name_en)';


--
-- Name: COLUMN products.gender; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.gender IS 'Genre (FK product_attributes.genders.name_en)';


--
-- Name: COLUMN products.season; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.season IS 'Saison (FK product_attributes.seasons.name_en)';


--
-- Name: COLUMN products.rise; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.rise IS 'Hauteur de taille (pantalons)';


--
-- Name: COLUMN products.closure; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.closure IS 'Type de fermeture';


--
-- Name: COLUMN products.sleeve_length; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.sleeve_length IS 'Longueur de manche';


--
-- Name: COLUMN products.origin; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.origin IS 'Origine/provenance';


--
-- Name: COLUMN products.decade; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.decade IS 'Décennie (vintage)';


--
-- Name: COLUMN products.trend; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.trend IS 'Tendance';


--
-- Name: COLUMN products.location; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.location IS 'Localisation';


--
-- Name: COLUMN products.model; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.model IS 'Modèle';


--
-- Name: COLUMN products.dim1; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.dim1 IS 'Dimension 1 (cm)';


--
-- Name: COLUMN products.dim2; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.dim2 IS 'Dimension 2 (cm)';


--
-- Name: COLUMN products.dim3; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.dim3 IS 'Dimension 3 (cm)';


--
-- Name: COLUMN products.dim4; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.dim4 IS 'Dimension 4 (cm)';


--
-- Name: COLUMN products.dim5; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.dim5 IS 'Dimension 5 (cm)';


--
-- Name: COLUMN products.dim6; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.dim6 IS 'Dimension 6 (cm)';


--
-- Name: COLUMN products.images; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.images IS 'Images URLs (JSON array)';


--
-- Name: COLUMN products.pricing_edit; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.pricing_edit IS 'Édition limitée/exclusive';


--
-- Name: COLUMN products.pricing_rarity; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.pricing_rarity IS 'Rareté du produit';


--
-- Name: COLUMN products.pricing_quality; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.pricing_quality IS 'Qualité exceptionnelle';


--
-- Name: COLUMN products.pricing_details; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.pricing_details IS 'Détails valorisants';


--
-- Name: COLUMN products.pricing_style; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.pricing_style IS 'Style iconique';


--
-- Name: COLUMN products.marking; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.marking IS 'Marquages/logos';


--
-- Name: COLUMN products.sport; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.sport IS 'Sport (FK product_attributes.sports)';


--
-- Name: COLUMN products.neckline; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.neckline IS 'Encolure (FK product_attributes.necklines)';


--
-- Name: COLUMN products.length; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.length IS 'Longueur (FK product_attributes.lengths)';


--
-- Name: COLUMN products.pattern; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.products.pattern IS 'Motif (FK product_attributes.patterns)';


--
-- Name: products_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.products_id_seq OWNER TO stoflow_user;

--
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.products_id_seq OWNED BY user_1.products.id;


--
-- Name: publication_history; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.publication_history (
    id integer NOT NULL,
    product_id integer NOT NULL,
    status public.publication_status NOT NULL,
    platform_product_id character varying(100),
    error_message text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE user_1.publication_history OWNER TO stoflow_user;

--
-- Name: COLUMN publication_history.product_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.publication_history.product_id IS 'ID du produit (FK products.id)';


--
-- Name: COLUMN publication_history.status; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.publication_history.status IS 'Statut de la publication';


--
-- Name: COLUMN publication_history.platform_product_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.publication_history.platform_product_id IS 'ID du produit sur la plateforme';


--
-- Name: COLUMN publication_history.error_message; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.publication_history.error_message IS 'Message d''erreur si échec';


--
-- Name: COLUMN publication_history.metadata; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.publication_history.metadata IS 'Métadonnées supplémentaires';


--
-- Name: publication_history_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.publication_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.publication_history_id_seq OWNER TO stoflow_user;

--
-- Name: publication_history_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.publication_history_id_seq OWNED BY user_1.publication_history.id;


--
-- Name: vinted_connection; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.vinted_connection (
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


ALTER TABLE user_1.vinted_connection OWNER TO stoflow_user;

--
-- Name: COLUMN vinted_connection.vinted_user_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_connection.vinted_user_id IS 'ID utilisateur Vinted (PK)';


--
-- Name: COLUMN vinted_connection.login; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_connection.login IS 'Login/username Vinted';


--
-- Name: COLUMN vinted_connection.user_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_connection.user_id IS 'FK vers public.users.id';


--
-- Name: vinted_connection_vinted_user_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.vinted_connection_vinted_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.vinted_connection_vinted_user_id_seq OWNER TO stoflow_user;

--
-- Name: vinted_connection_vinted_user_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.vinted_connection_vinted_user_id_seq OWNED BY user_1.vinted_connection.vinted_user_id;


--
-- Name: vinted_conversations; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.vinted_conversations (
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


ALTER TABLE user_1.vinted_conversations OWNER TO stoflow_user;

--
-- Name: COLUMN vinted_conversations.conversation_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_conversations.conversation_id IS 'Vinted conversation ID (PK)';


--
-- Name: COLUMN vinted_conversations.opposite_user_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_conversations.opposite_user_id IS 'Other participant Vinted ID';


--
-- Name: COLUMN vinted_conversations.opposite_user_login; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_conversations.opposite_user_login IS 'Other participant username';


--
-- Name: COLUMN vinted_conversations.opposite_user_photo_url; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_conversations.opposite_user_photo_url IS 'Other participant avatar URL';


--
-- Name: COLUMN vinted_conversations.last_message_preview; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_conversations.last_message_preview IS 'Preview of last message';


--
-- Name: COLUMN vinted_conversations.is_unread; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_conversations.is_unread IS 'Has unread messages';


--
-- Name: COLUMN vinted_conversations.unread_count; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_conversations.unread_count IS 'Number of unread messages';


--
-- Name: COLUMN vinted_conversations.item_count; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_conversations.item_count IS 'Number of items in conversation';


--
-- Name: COLUMN vinted_conversations.item_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_conversations.item_id IS 'Main item Vinted ID';


--
-- Name: COLUMN vinted_conversations.item_title; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_conversations.item_title IS 'Main item title';


--
-- Name: COLUMN vinted_conversations.item_photo_url; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_conversations.item_photo_url IS 'Main item photo URL';


--
-- Name: COLUMN vinted_conversations.transaction_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_conversations.transaction_id IS 'Linked transaction ID';


--
-- Name: COLUMN vinted_conversations.updated_at_vinted; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_conversations.updated_at_vinted IS 'Last update on Vinted';


--
-- Name: COLUMN vinted_conversations.created_at; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_conversations.created_at IS 'Local creation date';


--
-- Name: COLUMN vinted_conversations.updated_at; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_conversations.updated_at IS 'Local update date';


--
-- Name: COLUMN vinted_conversations.last_synced_at; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_conversations.last_synced_at IS 'Last sync with Vinted';


--
-- Name: vinted_conversations_conversation_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.vinted_conversations_conversation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.vinted_conversations_conversation_id_seq OWNER TO stoflow_user;

--
-- Name: vinted_conversations_conversation_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.vinted_conversations_conversation_id_seq OWNED BY user_1.vinted_conversations.conversation_id;


--
-- Name: vinted_error_logs; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.vinted_error_logs (
    id integer NOT NULL,
    product_id integer NOT NULL,
    operation character varying(20) NOT NULL,
    error_type character varying(50) NOT NULL,
    error_message text NOT NULL,
    error_details text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE user_1.vinted_error_logs OWNER TO stoflow_user;

--
-- Name: COLUMN vinted_error_logs.operation; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_error_logs.operation IS 'Type d''opération: publish, update, delete';


--
-- Name: COLUMN vinted_error_logs.error_type; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_error_logs.error_type IS 'Type d''erreur: mapping_error, api_error, image_error, validation_error';


--
-- Name: COLUMN vinted_error_logs.error_message; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_error_logs.error_message IS 'Message d''erreur principal';


--
-- Name: COLUMN vinted_error_logs.error_details; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_error_logs.error_details IS 'Détails supplémentaires (JSON, traceback, etc.)';


--
-- Name: vinted_error_logs_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.vinted_error_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.vinted_error_logs_id_seq OWNER TO stoflow_user;

--
-- Name: vinted_error_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.vinted_error_logs_id_seq OWNED BY user_1.vinted_error_logs.id;


--
-- Name: vinted_job_stats; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.vinted_job_stats (
    id integer NOT NULL,
    action_type_id integer NOT NULL,
    date date NOT NULL,
    total_jobs integer DEFAULT 0 NOT NULL,
    success_count integer DEFAULT 0 NOT NULL,
    failure_count integer DEFAULT 0 NOT NULL,
    avg_duration_ms integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE user_1.vinted_job_stats OWNER TO stoflow_user;

--
-- Name: vinted_job_stats_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.vinted_job_stats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.vinted_job_stats_id_seq OWNER TO stoflow_user;

--
-- Name: vinted_job_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.vinted_job_stats_id_seq OWNED BY user_1.vinted_job_stats.id;


--
-- Name: vinted_jobs_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.vinted_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.vinted_jobs_id_seq OWNER TO stoflow_user;

--
-- Name: vinted_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.vinted_jobs_id_seq OWNED BY user_1.marketplace_jobs.id;


--
-- Name: vinted_messages; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.vinted_messages (
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


ALTER TABLE user_1.vinted_messages OWNER TO stoflow_user;

--
-- Name: COLUMN vinted_messages.conversation_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_messages.conversation_id IS 'FK to vinted_conversations';


--
-- Name: COLUMN vinted_messages.vinted_message_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_messages.vinted_message_id IS 'Vinted message ID';


--
-- Name: COLUMN vinted_messages.entity_type; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_messages.entity_type IS 'message, offer_request_message, status_message, action_message';


--
-- Name: COLUMN vinted_messages.sender_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_messages.sender_id IS 'Sender Vinted ID';


--
-- Name: COLUMN vinted_messages.sender_login; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_messages.sender_login IS 'Sender username';


--
-- Name: COLUMN vinted_messages.body; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_messages.body IS 'Message text content';


--
-- Name: COLUMN vinted_messages.title; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_messages.title IS 'Title for status/action messages';


--
-- Name: COLUMN vinted_messages.subtitle; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_messages.subtitle IS 'Subtitle for status/action messages';


--
-- Name: COLUMN vinted_messages.offer_price; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_messages.offer_price IS 'Offer price (e.g., 8.0)';


--
-- Name: COLUMN vinted_messages.offer_status; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_messages.offer_status IS 'Offer status title';


--
-- Name: COLUMN vinted_messages.is_from_current_user; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_messages.is_from_current_user IS 'Sent by current user';


--
-- Name: COLUMN vinted_messages.created_at_vinted; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_messages.created_at_vinted IS 'Creation time on Vinted';


--
-- Name: vinted_messages_id_seq; Type: SEQUENCE; Schema: user_1; Owner: stoflow_user
--

CREATE SEQUENCE user_1.vinted_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_1.vinted_messages_id_seq OWNER TO stoflow_user;

--
-- Name: vinted_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: user_1; Owner: stoflow_user
--

ALTER SEQUENCE user_1.vinted_messages_id_seq OWNED BY user_1.vinted_messages.id;


--
-- Name: vinted_products; Type: TABLE; Schema: user_1; Owner: stoflow_user
--

CREATE TABLE user_1.vinted_products (
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


ALTER TABLE user_1.vinted_products OWNER TO stoflow_user;

--
-- Name: TABLE vinted_products; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON TABLE user_1.vinted_products IS 'Produits Vinted (standalone, pas de FK vers products)';


--
-- Name: COLUMN vinted_products.vinted_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.vinted_id IS 'ID unique Vinted';


--
-- Name: COLUMN vinted_products.photos_data; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.photos_data IS 'JSON des photos [{id, url, ...}]';


--
-- Name: COLUMN vinted_products.total_price; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.total_price IS 'Prix total avec frais';


--
-- Name: COLUMN vinted_products.brand_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.brand_id IS 'ID Vinted de la marque';


--
-- Name: COLUMN vinted_products.size_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.size_id IS 'ID Vinted de la taille';


--
-- Name: COLUMN vinted_products.catalog_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.catalog_id IS 'ID Vinted de la catégorie';


--
-- Name: COLUMN vinted_products.condition_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.condition_id IS 'ID Vinted de létat';


--
-- Name: COLUMN vinted_products.material; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.material IS 'Matière';


--
-- Name: COLUMN vinted_products.measurements; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.measurements IS 'Dimensions texte (l X cm / L Y cm)';


--
-- Name: COLUMN vinted_products.measurement_width; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.measurement_width IS 'Largeur en cm';


--
-- Name: COLUMN vinted_products.measurement_length; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.measurement_length IS 'Longueur en cm';


--
-- Name: COLUMN vinted_products.manufacturer_labelling; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.manufacturer_labelling IS 'Étiquetage du fabricant';


--
-- Name: COLUMN vinted_products.is_reserved; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.is_reserved IS 'Est réservé';


--
-- Name: COLUMN vinted_products.is_hidden; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.is_hidden IS 'Est masqué';


--
-- Name: COLUMN vinted_products.seller_id; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.seller_id IS 'ID vendeur Vinted';


--
-- Name: COLUMN vinted_products.seller_login; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.seller_login IS 'Login vendeur';


--
-- Name: COLUMN vinted_products.service_fee; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.service_fee IS 'Frais de service';


--
-- Name: COLUMN vinted_products.buyer_protection_fee; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.buyer_protection_fee IS 'Frais protection acheteur';


--
-- Name: COLUMN vinted_products.shipping_price; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.shipping_price IS 'Frais de port';


--
-- Name: COLUMN vinted_products.published_at; Type: COMMENT; Schema: user_1; Owner: stoflow_user
--

COMMENT ON COLUMN user_1.vinted_products.published_at IS 'Date de publication sur Vinted (from image timestamp)';


--
-- Name: action_types; Type: TABLE; Schema: vinted; Owner: stoflow_user
--

CREATE TABLE vinted.action_types (
    id integer NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    priority integer NOT NULL,
    is_batch boolean NOT NULL,
    rate_limit_ms integer NOT NULL,
    max_retries integer NOT NULL,
    timeout_seconds integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE vinted.action_types OWNER TO stoflow_user;

--
-- Name: COLUMN action_types.code; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.action_types.code IS 'Unique code: publish, sync, orders, message, update, delete';


--
-- Name: COLUMN action_types.name; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.action_types.name IS 'Display name';


--
-- Name: COLUMN action_types.priority; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.action_types.priority IS '1=CRITICAL, 2=HIGH, 3=NORMAL, 4=LOW';


--
-- Name: COLUMN action_types.is_batch; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.action_types.is_batch IS 'True if action processes multiple items';


--
-- Name: COLUMN action_types.rate_limit_ms; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.action_types.rate_limit_ms IS 'Delay between requests in ms';


--
-- Name: action_types_id_seq; Type: SEQUENCE; Schema: vinted; Owner: stoflow_user
--

CREATE SEQUENCE vinted.action_types_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE vinted.action_types_id_seq OWNER TO stoflow_user;

--
-- Name: action_types_id_seq; Type: SEQUENCE OWNED BY; Schema: vinted; Owner: stoflow_user
--

ALTER SEQUENCE vinted.action_types_id_seq OWNED BY vinted.action_types.id;


--
-- Name: categories_id_seq; Type: SEQUENCE; Schema: vinted; Owner: stoflow_user
--

CREATE SEQUENCE vinted.categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE vinted.categories_id_seq OWNER TO stoflow_user;

--
-- Name: categories_id_seq; Type: SEQUENCE OWNED BY; Schema: vinted; Owner: stoflow_user
--

ALTER SEQUENCE vinted.categories_id_seq OWNED BY vinted.categories.id;


--
-- Name: deletions; Type: TABLE; Schema: vinted; Owner: stoflow_user
--

CREATE TABLE vinted.deletions (
    id integer NOT NULL,
    id_vinted bigint,
    id_site bigint,
    price numeric(10,2),
    date_published date,
    date_deleted date,
    view_count integer DEFAULT 0,
    favourite_count integer DEFAULT 0,
    conversations integer DEFAULT 0,
    days_active integer
);


ALTER TABLE vinted.deletions OWNER TO stoflow_user;

--
-- Name: COLUMN deletions.id_vinted; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.deletions.id_vinted IS 'ID Vinted du produit supprimé';


--
-- Name: COLUMN deletions.id_site; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.deletions.id_site IS 'ID produit Stoflow';


--
-- Name: COLUMN deletions.price; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.deletions.price IS 'Prix au moment suppression';


--
-- Name: COLUMN deletions.date_published; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.deletions.date_published IS 'Date publication initiale';


--
-- Name: COLUMN deletions.date_deleted; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.deletions.date_deleted IS 'Date suppression';


--
-- Name: COLUMN deletions.view_count; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.deletions.view_count IS 'Nombre de vues';


--
-- Name: COLUMN deletions.favourite_count; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.deletions.favourite_count IS 'Nombre de favoris';


--
-- Name: COLUMN deletions.conversations; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.deletions.conversations IS 'Nombre de conversations';


--
-- Name: COLUMN deletions.days_active; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.deletions.days_active IS 'Jours en ligne';


--
-- Name: deletions_id_seq; Type: SEQUENCE; Schema: vinted; Owner: stoflow_user
--

CREATE SEQUENCE vinted.deletions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE vinted.deletions_id_seq OWNER TO stoflow_user;

--
-- Name: deletions_id_seq; Type: SEQUENCE OWNED BY; Schema: vinted; Owner: stoflow_user
--

ALTER SEQUENCE vinted.deletions_id_seq OWNED BY vinted.deletions.id;


--
-- Name: mapping_id_seq; Type: SEQUENCE; Schema: vinted; Owner: stoflow_user
--

CREATE SEQUENCE vinted.mapping_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE vinted.mapping_id_seq OWNER TO stoflow_user;

--
-- Name: mapping_id_seq; Type: SEQUENCE OWNED BY; Schema: vinted; Owner: stoflow_user
--

ALTER SEQUENCE vinted.mapping_id_seq OWNED BY vinted.mapping.id;


--
-- Name: mapping_validation; Type: VIEW; Schema: vinted; Owner: stoflow_user
--

CREATE VIEW vinted.mapping_validation AS
 SELECT 'VINTED_NOT_MAPPED'::text AS issue,
    (vc.id)::text AS vinted_id,
    vc.title AS vinted_title,
    vc.gender AS vinted_gender,
    NULL::character varying AS my_category,
    NULL::character varying AS my_gender
   FROM (vinted.categories vc
     LEFT JOIN vinted.mapping vm ON ((vc.id = vm.vinted_id)))
  WHERE ((vc.is_active = true) AND (vm.id IS NULL))
UNION ALL
 SELECT 'NO_DEFAULT'::text AS issue,
    NULL::text AS vinted_id,
    NULL::character varying AS vinted_title,
    NULL::character varying AS vinted_gender,
    mapping.my_category,
    mapping.my_gender
   FROM vinted.mapping
  GROUP BY mapping.my_category, mapping.my_gender
 HAVING (sum(
        CASE
            WHEN mapping.is_default THEN 1
            ELSE 0
        END) = 0)
UNION ALL
 SELECT 'COUPLE_NOT_MAPPED'::text AS issue,
    NULL::text AS vinted_id,
    NULL::character varying AS vinted_title,
    NULL::character varying AS vinted_gender,
    c.name_en AS my_category,
    g.gender AS my_gender
   FROM (product_attributes.categories c
     CROSS JOIN ( VALUES ('men'::text), ('women'::text), ('boys'::text), ('girls'::text)) g(gender))
  WHERE ((g.gender = ANY ((c.genders)::text[])) AND (c.parent_category IS NOT NULL) AND ((c.name_en)::text <> ALL ((ARRAY['tops'::character varying, 'bottoms'::character varying, 'outerwear'::character varying, 'dresses-jumpsuits'::character varying, 'formalwear'::character varying, 'sportswear'::character varying, 'clothing'::character varying])::text[])) AND (NOT (EXISTS ( SELECT 1
           FROM vinted.mapping vm
          WHERE (((vm.my_category)::text = (c.name_en)::text) AND ((vm.my_gender)::text = g.gender))))));


ALTER TABLE vinted.mapping_validation OWNER TO stoflow_user;

--
-- Name: order_products; Type: TABLE; Schema: vinted; Owner: stoflow_user
--

CREATE TABLE vinted.order_products (
    id integer NOT NULL,
    transaction_id bigint NOT NULL,
    vinted_item_id bigint,
    product_id bigint,
    title character varying(255),
    price numeric(10,2),
    size character varying(100),
    brand character varying(255),
    photo_url text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE vinted.order_products OWNER TO stoflow_user;

--
-- Name: COLUMN order_products.transaction_id; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.order_products.transaction_id IS 'FK vers vinted_orders';


--
-- Name: COLUMN order_products.vinted_item_id; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.order_products.vinted_item_id IS 'ID article Vinted';


--
-- Name: COLUMN order_products.product_id; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.order_products.product_id IS 'ID produit Stoflow';


--
-- Name: COLUMN order_products.title; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.order_products.title IS 'Titre produit';


--
-- Name: COLUMN order_products.price; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.order_products.price IS 'Prix unitaire';


--
-- Name: COLUMN order_products.size; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.order_products.size IS 'Taille';


--
-- Name: COLUMN order_products.brand; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.order_products.brand IS 'Marque';


--
-- Name: COLUMN order_products.photo_url; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.order_products.photo_url IS 'URL photo principale';


--
-- Name: order_products_id_seq; Type: SEQUENCE; Schema: vinted; Owner: stoflow_user
--

CREATE SEQUENCE vinted.order_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE vinted.order_products_id_seq OWNER TO stoflow_user;

--
-- Name: order_products_id_seq; Type: SEQUENCE OWNED BY; Schema: vinted; Owner: stoflow_user
--

ALTER SEQUENCE vinted.order_products_id_seq OWNED BY vinted.order_products.id;


--
-- Name: orders; Type: TABLE; Schema: vinted; Owner: stoflow_user
--

CREATE TABLE vinted.orders (
    transaction_id bigint NOT NULL,
    buyer_id bigint,
    buyer_login character varying(255),
    seller_id bigint,
    seller_login character varying(255),
    status character varying(50),
    total_price numeric(10,2),
    currency character varying(3) DEFAULT 'EUR'::character varying,
    shipping_price numeric(10,2),
    service_fee numeric(10,2),
    buyer_protection_fee numeric(10,2),
    seller_revenue numeric(10,2),
    tracking_number character varying(100),
    carrier character varying(100),
    shipping_tracking_code character varying(100),
    created_at_vinted timestamp with time zone,
    shipped_at timestamp with time zone,
    delivered_at timestamp with time zone,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE vinted.orders OWNER TO stoflow_user;

--
-- Name: COLUMN orders.transaction_id; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.transaction_id IS 'ID transaction Vinted (PK)';


--
-- Name: COLUMN orders.buyer_id; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.buyer_id IS 'ID acheteur Vinted';


--
-- Name: COLUMN orders.buyer_login; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.buyer_login IS 'Login acheteur';


--
-- Name: COLUMN orders.seller_id; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.seller_id IS 'ID vendeur Vinted';


--
-- Name: COLUMN orders.seller_login; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.seller_login IS 'Login vendeur';


--
-- Name: COLUMN orders.status; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.status IS 'Statut commande';


--
-- Name: COLUMN orders.total_price; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.total_price IS 'Prix total';


--
-- Name: COLUMN orders.currency; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.currency IS 'Devise';


--
-- Name: COLUMN orders.shipping_price; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.shipping_price IS 'Frais de port';


--
-- Name: COLUMN orders.service_fee; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.service_fee IS 'Frais de service';


--
-- Name: COLUMN orders.buyer_protection_fee; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.buyer_protection_fee IS 'Protection acheteur';


--
-- Name: COLUMN orders.seller_revenue; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.seller_revenue IS 'Revenu vendeur net';


--
-- Name: COLUMN orders.tracking_number; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.tracking_number IS 'Numéro de suivi';


--
-- Name: COLUMN orders.carrier; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.carrier IS 'Transporteur';


--
-- Name: COLUMN orders.shipping_tracking_code; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.shipping_tracking_code IS 'Code suivi transporteur';


--
-- Name: COLUMN orders.created_at_vinted; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.created_at_vinted IS 'Date création Vinted';


--
-- Name: COLUMN orders.shipped_at; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.shipped_at IS 'Date expédition';


--
-- Name: COLUMN orders.delivered_at; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.delivered_at IS 'Date livraison';


--
-- Name: COLUMN orders.completed_at; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.completed_at IS 'Date finalisation';


--
-- Name: COLUMN orders.created_at; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.created_at IS 'Date création locale';


--
-- Name: COLUMN orders.updated_at; Type: COMMENT; Schema: vinted; Owner: stoflow_user
--

COMMENT ON COLUMN vinted.orders.updated_at IS 'Date MAJ locale';


--
-- Name: vinted_orders_transaction_id_seq; Type: SEQUENCE; Schema: vinted; Owner: stoflow_user
--

CREATE SEQUENCE vinted.vinted_orders_transaction_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE vinted.vinted_orders_transaction_id_seq OWNER TO stoflow_user;

--
-- Name: vinted_orders_transaction_id_seq; Type: SEQUENCE OWNED BY; Schema: vinted; Owner: stoflow_user
--

ALTER SEQUENCE vinted.vinted_orders_transaction_id_seq OWNED BY vinted.orders.transaction_id;


--
-- Name: category_mapping id; Type: DEFAULT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.category_mapping ALTER COLUMN id SET DEFAULT nextval('ebay.ebay_category_mapping_id_seq'::regclass);


--
-- Name: exchange_rate id; Type: DEFAULT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.exchange_rate ALTER COLUMN id SET DEFAULT nextval('ebay.exchange_rate_config_id_seq'::regclass);


--
-- Name: marketplace_config id; Type: DEFAULT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.marketplace_config ALTER COLUMN id SET DEFAULT nextval('ebay.marketplace_config_id_seq'::regclass);


--
-- Name: admin_audit_logs id; Type: DEFAULT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.admin_audit_logs ALTER COLUMN id SET DEFAULT nextval('public.admin_audit_logs_id_seq'::regclass);


--
-- Name: ai_credits id; Type: DEFAULT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.ai_credits ALTER COLUMN id SET DEFAULT nextval('public.ai_credits_id_seq'::regclass);


--
-- Name: doc_articles id; Type: DEFAULT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.doc_articles ALTER COLUMN id SET DEFAULT nextval('public.doc_articles_id_seq'::regclass);


--
-- Name: doc_categories id; Type: DEFAULT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.doc_categories ALTER COLUMN id SET DEFAULT nextval('public.doc_categories_id_seq'::regclass);


--
-- Name: migration_errors id; Type: DEFAULT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.migration_errors ALTER COLUMN id SET DEFAULT nextval('public.migration_errors_id_seq'::regclass);


--
-- Name: permissions id; Type: DEFAULT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.permissions ALTER COLUMN id SET DEFAULT nextval('public.permissions_id_seq'::regclass);


--
-- Name: role_permissions id; Type: DEFAULT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.role_permissions ALTER COLUMN id SET DEFAULT nextval('public.role_permissions_id_seq'::regclass);


--
-- Name: subscription_features id; Type: DEFAULT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.subscription_features ALTER COLUMN id SET DEFAULT nextval('public.subscription_features_id_seq'::regclass);


--
-- Name: subscription_quotas id; Type: DEFAULT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.subscription_quotas ALTER COLUMN id SET DEFAULT nextval('public.subscription_quotas_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: ai_generation_logs id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ai_generation_logs ALTER COLUMN id SET DEFAULT nextval('template_tenant.ai_generation_logs_id_seq'::regclass);


--
-- Name: batch_jobs id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.batch_jobs ALTER COLUMN id SET DEFAULT nextval('template_tenant.batch_jobs_id_seq'::regclass);


--
-- Name: ebay_credentials id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_credentials ALTER COLUMN id SET DEFAULT nextval('template_tenant.ebay_credentials_id_seq'::regclass);


--
-- Name: ebay_orders id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_orders ALTER COLUMN id SET DEFAULT nextval('template_tenant.ebay_orders_id_seq'::regclass);


--
-- Name: ebay_orders_products id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_orders_products ALTER COLUMN id SET DEFAULT nextval('template_tenant.ebay_orders_products_id_seq'::regclass);


--
-- Name: ebay_products id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_products ALTER COLUMN id SET DEFAULT nextval('template_tenant.ebay_products_id_seq'::regclass);


--
-- Name: ebay_promoted_listings id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_promoted_listings ALTER COLUMN id SET DEFAULT nextval('template_tenant.ebay_promoted_listings_id_seq'::regclass);


--
-- Name: etsy_credentials id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.etsy_credentials ALTER COLUMN id SET DEFAULT nextval('template_tenant.etsy_credentials_id_seq'::regclass);


--
-- Name: marketplace_jobs id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.marketplace_jobs ALTER COLUMN id SET DEFAULT nextval('template_tenant.vinted_jobs_id_seq'::regclass);


--
-- Name: marketplace_tasks id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.marketplace_tasks ALTER COLUMN id SET DEFAULT nextval('template_tenant.plugin_tasks_id_seq'::regclass);


--
-- Name: product_images id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.product_images ALTER COLUMN id SET DEFAULT nextval('template_tenant.product_images_id_seq'::regclass);


--
-- Name: products id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products ALTER COLUMN id SET DEFAULT nextval('template_tenant.products_id_seq'::regclass);


--
-- Name: publication_history id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.publication_history ALTER COLUMN id SET DEFAULT nextval('template_tenant.publication_history_id_seq'::regclass);


--
-- Name: vinted_connection vinted_user_id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_connection ALTER COLUMN vinted_user_id SET DEFAULT nextval('template_tenant.vinted_connection_vinted_user_id_seq'::regclass);


--
-- Name: vinted_conversations conversation_id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_conversations ALTER COLUMN conversation_id SET DEFAULT nextval('template_tenant.vinted_conversations_conversation_id_seq'::regclass);


--
-- Name: vinted_error_logs id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_error_logs ALTER COLUMN id SET DEFAULT nextval('template_tenant.vinted_error_logs_id_seq'::regclass);


--
-- Name: vinted_job_stats id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_job_stats ALTER COLUMN id SET DEFAULT nextval('template_tenant.vinted_job_stats_id_seq'::regclass);


--
-- Name: vinted_messages id; Type: DEFAULT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_messages ALTER COLUMN id SET DEFAULT nextval('template_tenant.vinted_messages_id_seq'::regclass);


--
-- Name: ai_generation_logs id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ai_generation_logs ALTER COLUMN id SET DEFAULT nextval('user_1.ai_generation_logs_id_seq'::regclass);


--
-- Name: batch_jobs id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.batch_jobs ALTER COLUMN id SET DEFAULT nextval('user_1.batch_jobs_id_seq'::regclass);


--
-- Name: ebay_credentials id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_credentials ALTER COLUMN id SET DEFAULT nextval('user_1.ebay_credentials_id_seq'::regclass);


--
-- Name: ebay_orders id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_orders ALTER COLUMN id SET DEFAULT nextval('user_1.ebay_orders_id_seq'::regclass);


--
-- Name: ebay_orders_products id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_orders_products ALTER COLUMN id SET DEFAULT nextval('user_1.ebay_orders_products_id_seq'::regclass);


--
-- Name: ebay_products id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_products ALTER COLUMN id SET DEFAULT nextval('user_1.ebay_products_id_seq'::regclass);


--
-- Name: ebay_promoted_listings id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_promoted_listings ALTER COLUMN id SET DEFAULT nextval('user_1.ebay_promoted_listings_id_seq'::regclass);


--
-- Name: etsy_credentials id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.etsy_credentials ALTER COLUMN id SET DEFAULT nextval('user_1.etsy_credentials_id_seq'::regclass);


--
-- Name: marketplace_jobs id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.marketplace_jobs ALTER COLUMN id SET DEFAULT nextval('user_1.vinted_jobs_id_seq'::regclass);


--
-- Name: marketplace_tasks id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.marketplace_tasks ALTER COLUMN id SET DEFAULT nextval('user_1.plugin_tasks_id_seq'::regclass);


--
-- Name: product_images id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.product_images ALTER COLUMN id SET DEFAULT nextval('user_1.product_images_id_seq'::regclass);


--
-- Name: products id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products ALTER COLUMN id SET DEFAULT nextval('user_1.products_id_seq'::regclass);


--
-- Name: publication_history id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.publication_history ALTER COLUMN id SET DEFAULT nextval('user_1.publication_history_id_seq'::regclass);


--
-- Name: vinted_connection vinted_user_id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_connection ALTER COLUMN vinted_user_id SET DEFAULT nextval('user_1.vinted_connection_vinted_user_id_seq'::regclass);


--
-- Name: vinted_conversations conversation_id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_conversations ALTER COLUMN conversation_id SET DEFAULT nextval('user_1.vinted_conversations_conversation_id_seq'::regclass);


--
-- Name: vinted_error_logs id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_error_logs ALTER COLUMN id SET DEFAULT nextval('user_1.vinted_error_logs_id_seq'::regclass);


--
-- Name: vinted_job_stats id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_job_stats ALTER COLUMN id SET DEFAULT nextval('user_1.vinted_job_stats_id_seq'::regclass);


--
-- Name: vinted_messages id; Type: DEFAULT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_messages ALTER COLUMN id SET DEFAULT nextval('user_1.vinted_messages_id_seq'::regclass);


--
-- Name: action_types id; Type: DEFAULT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.action_types ALTER COLUMN id SET DEFAULT nextval('vinted.action_types_id_seq'::regclass);


--
-- Name: categories id; Type: DEFAULT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.categories ALTER COLUMN id SET DEFAULT nextval('vinted.categories_id_seq'::regclass);


--
-- Name: deletions id; Type: DEFAULT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.deletions ALTER COLUMN id SET DEFAULT nextval('vinted.deletions_id_seq'::regclass);


--
-- Name: mapping id; Type: DEFAULT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.mapping ALTER COLUMN id SET DEFAULT nextval('vinted.mapping_id_seq'::regclass);


--
-- Name: order_products id; Type: DEFAULT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.order_products ALTER COLUMN id SET DEFAULT nextval('vinted.order_products_id_seq'::regclass);


--
-- Name: orders transaction_id; Type: DEFAULT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.orders ALTER COLUMN transaction_id SET DEFAULT nextval('vinted.vinted_orders_transaction_id_seq'::regclass);


--
-- Data for Name: aspect_closure; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_closure (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) FROM stdin;
Zip	Fermeture éclair	Reißverschluss	Cremallera	Cerniera	Rits	Fermeture éclair	Zamek błyskawiczny
Button	Bouton	Knopf	Botón	Bottone	Knoop	Bouton	Guzik
Buckle	Boucle	Schnalle	Hebilla	Fibbia	Gesp	Boucle	Klamra
Hook & Eye	Agrafe	Haken & Öse	Corchete	Gancio	Haak en oog	Agrafe	Haczyk
Drawstring	Cordon	Kordelzug	Cordón	Coulisse	Trekkoord	Cordon	Sznurek
Velcro	Velcro	Klett	Velcro	Velcro	Klittenband	Velcro	Rzep
Pull On	Enfiler	Schlupf	Sin cierre	Senza chiusura	Geen	Enfiler	Bez zapięcia
Snap	Pression	Druckknopf	Corchete	Bottone a pressione	Drukknoop	Pression	Zatrzask
\.


--
-- Data for Name: aspect_colour; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_colour (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) FROM stdin;
Black	Noir	Schwarz	Negro	Nero	Zwart	Noir	Czarny
White	Blanc	Weiß	Blanco	Bianco	Wit	Blanc	Biały
Blue	Bleu	Blau	Azul	Blu	Blauw	Bleu	Niebieski
Red	Rouge	Rot	Rojo	Rosso	Rood	Rouge	Czerwony
Green	Vert	Grün	Verde	Verde	Groen	Vert	Zielony
Yellow	Jaune	Gelb	Amarillo	Giallo	Geel	Jaune	Żółty
Orange	Orange	Orange	Naranja	Arancione	Oranje	Orange	Pomarańczowy
Pink	Rose	Rosa	Rosa	Rosa	Roze	Rose	Różowy
Purple	Violet	Lila	Púrpura	Viola	Paars	Violet	Fioletowy
Brown	Marron	Braun	Marrón	Marrone	Bruin	Marron	Brązowy
Grey	Gris	Grau	Gris	Grigio	Grijs	Gris	Szary
Beige	Beige	Beige	Beige	Beige	Beige	Beige	Beżowy
Navy	Bleu Marine	Marineblau	Azul Marino	Blu Navy	Marineblauw	Bleu Marine	Granatowy
Cream	Crème	Creme	Crema	Crema	Crème	Crème	Kremowy
Multicoloured	Multicolore	Mehrfarbig	Multicolor	Multicolore	Meerkleurig	Multicolore	Wielokolorowy
Khaki	Kaki	Khaki	Caqui	Cachi	Kaki	Kaki	Khaki
Gold	Or	Gold	Dorado	Oro	Goud	Or	Złoty
Silver	Argent	Silber	Plateado	Argento	Zilver	Argent	Srebrny
Burgundy	Bordeaux	Burgund	Burdeos	Bordeaux	Bordeauxrood	Bordeaux	Bordowy
Turquoise	Turquoise	Türkis	Turquesa	Turchese	Turquoise	Turquoise	Turkusowy
\.


--
-- Data for Name: aspect_department; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_department (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) FROM stdin;
Men	Homme	Herren	Hombre	Uomo	Heren	Homme	Mężczyźni
Women	Femme	Damen	Mujer	Donna	Dames	Femme	Kobiety
Unisex Adults	Adulte unisexe	Unisex Erwachsene	Adultos unisex	Adulto unisex	Unisex volwassenen	Adulte unisexe	Dorośli unisex
Boys	Garçon	Jungen	Niños	Bambino	Jongens	Garçon	Chłopcy
Girls	Fille	Mädchen	Niñas	Bambina	Meisjes	Fille	Dziewczynki
\.


--
-- Data for Name: aspect_features; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_features (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) FROM stdin;
Pockets	Poches	Taschen	Bolsillos	Tasche	Zakken	Poches	Kieszenie
Stretch	Stretch	Stretch	Elástico	Elasticizzato	Stretch	Stretch	Rozciągliwy
Lined	Doublé	Gefüttert	Forrado	Foderato	Gevoerd	Doublé	Podszewka
Hooded	Capuche	Kapuze	Capucha	Cappuccio	Capuchon	Capuche	Kaptur
Machine Washable	Lavable en machine	Maschinenwaschbar	Lavable a máquina	Lavabile in lavatrice	Machine wasbaar	Lavable en machine	Nadaje się do prania w pralce
Breathable	Respirant	Atmungsaktiv	Transpirable	Traspirante	Ademend	Respirant	Oddychający
Waterproof	Imperméable	Wasserdicht	Impermeable	Impermeabile	Waterdicht	Imperméable	Wodoodporny
Lightweight	Léger	Leicht	Ligero	Leggero	Lichtgewicht	Léger	Lekki
\.


--
-- Data for Name: aspect_fit; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_fit (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) FROM stdin;
Regular	Regular	Regular	Regular	Regular	Normaal	Regular	Regularny
Slim	Slim	Slim	Ajustado	Slim	Slim	Slim	Slim
Skinny	Skinny	Skinny	Pitillo	Skinny	Skinny	Skinny	Skinny
Loose	Ample	Weit	Ancho	Largo	Ruim	Ample	Luźny
Relaxed	Relaxed	Relaxed	Relajado	Rilassato	Relaxed	Relaxed	Swobodny
Oversized	Oversize	Oversized	Oversize	Oversize	Oversized	Oversize	Oversize
Bootcut	Bootcut	Bootcut	Bootcut	Bootcut	Bootcut	Bootcut	Bootcut
Straight	Droit	Gerade	Recto	Dritto	Recht	Droit	Prosty
Wide Leg	Jambe large	Weites Bein	Pierna ancha	Gamba larga	Wijde pijp	Jambe large	Szeroka nogawka
Tapered	Fuselé	Konisch	Estrecho	Affusolato	Taps toelopend	Fuselé	Zwężany
Athletic	Athlétique	Athletisch	Atlético	Atletico	Athletic	Athlétique	Atletyczny
\.


--
-- Data for Name: aspect_inside_leg; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_inside_leg (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) FROM stdin;
\.


--
-- Data for Name: aspect_material; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_material (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) FROM stdin;
Cotton	Coton	Baumwolle	Algodón	Cotone	Katoen	Coton	Bawełna
Polyester	Polyester	Polyester	Poliéster	Poliestere	Polyester	Polyester	Poliester
Denim	Jean	Denim	Mezclilla	Denim	Denim	Jean	Dżins
Leather	Cuir	Leder	Cuero	Pelle	Leer	Cuir	Skóra
Wool	Laine	Wolle	Lana	Lana	Wol	Laine	Wełna
Silk	Soie	Seide	Seda	Seta	Zijde	Soie	Jedwab
Linen	Lin	Leinen	Lino	Lino	Linnen	Lin	Len
Nylon	Nylon	Nylon	Nailon	Nylon	Nylon	Nylon	Nylon
Viscose	Viscose	Viskose	Viscosa	Viscosa	Viscose	Viscose	Wiskoza
Cashmere	Cachemire	Kaschmir	Cachemir	Cashmere	Kasjmier	Cachemire	Kaszmir
Velvet	Velours	Samt	Terciopelo	Velluto	Fluweel	Velours	Aksamit
Suede	Daim	Wildleder	Ante	Camoscio	Suède	Daim	Zamsz
Fleece	Polaire	Fleece	Forro polar	Pile	Fleece	Polaire	Polar
Elastane	Élasthanne	Elasthan	Elastano	Elastan	Elastaan	Élasthanne	Elastan
Synthetic	Synthétique	Synthetik	Sintético	Sintetico	Synthetisch	Synthétique	Syntetyczny
\.


--
-- Data for Name: aspect_name_mapping; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_name_mapping (aspect_key, ebay_gb, ebay_fr, ebay_de, ebay_it, ebay_es, ebay_nl, ebay_be, ebay_pl) FROM stdin;
brand	Brand	Marque	Marke	Marca	Marca	Merk	Marque	Marka
color	Colour	Couleur	Farbe	Colore	Color	Kleur	Couleur	Kolor
size	Size	Taille	Größe	Taglia	Talla	Maat	Taille	Rozmiar
condition	Condition	État	Zustand	Condizioni	Estado	Staat	État	Stan
material	Material	Matière	Material	Materiale	Material	Materiaal	Matière	Materiał
style	Style	Style	Stil	Stile	Estilo	Stijl	Style	Styl
season	Season	Saison	Jahreszeit	Stagione	Temporada	Seizoen	Saison	Sezon
gender	Department	Rayon	Abteilung	Reparto	Departamento	Afdeling	Rayon	Dział
sleeve_length	Sleeve Length	Longueur des manches	Ärmellänge	Lunghezza maniche	Largo de manga	Mouwlengte	Longueur des manches	Długość rękawa
fit	Fit	Coupe	Passform	Vestibilità	Ajuste	Pasvorm	Coupe	Krój
closure	Closure Type	Type de fermeture	Verschlussart	Tipo di chiusura	Tipo de cierre	Sluitingstype	Type de fermeture	Typ zapięcia
rise	Rise	Taille (hauteur)	Leibhöhe	Altezza vita	Altura de cintura	Taillehoogte	Taille (hauteur)	Wysokość talii
vintage	Vintage	Vintage	Vintage	Vintage	Vintage	Vintage	Vintage	Vintage
decade	Decade	Décennie	Jahrzehnt	Decennio	Década	Decennium	Décennie	Dekada
country	Country/Region of Manufacture	Pays de fabrication	Herstellungsland/-region	Paese di fabbricazione	País/región de fabricación	Land/regio van vervaardiging	Pays de fabrication	Kraj/region produkcji
pattern	Pattern	Motif	Muster	Fantasia	Patrón	Patroon	Motif	Wzór
features	Features	Caractéristiques	Besonderheiten	Caratteristiche	Características	Kenmerken	Caractéristiques	Cechy
\.


--
-- Data for Name: aspect_neckline; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_neckline (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) FROM stdin;
Crew Neck	Col rond	Rundhals	Cuello redondo	Girocollo	Ronde hals	Col rond	Okrągły
V-Neck	Col en V	V-Ausschnitt	Cuello en V	Scollo a V	V-hals	Col en V	Dekolt w serek
Collared	Col	Kragen	Con cuello	Con colletto	Kraag	Col	Z kołnierzem
Hooded	À capuche	Mit Kapuze	Con capucha	Con cappuccio	Met capuchon	À capuche	Z kapturem
Polo	Col polo	Polokragen	Cuello polo	Collo polo	Polokraag	Col polo	Polo
Turtleneck	Col roulé	Rollkragen	Cuello alto	Collo alto	Coltrui	Col roulé	Golf
Scoop Neck	Col dégagé	Rundausschnitt	Cuello redondo	Scollo tondo	Ronde hals	Col dégagé	Okrągły
\.


--
-- Data for Name: aspect_occasion; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_occasion (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) FROM stdin;
Casual	Décontracté	Freizeit	Casual	Casual	Casual	Décontracté	Codzienny
Formal	Formel	Formell	Formal	Formale	Formeel	Formel	Formalny
Party	Soirée	Party	Fiesta	Festa	Feest	Soirée	Imprezowy
Sport	Sport	Sport	Deporte	Sport	Sport	Sport	Sportowy
Work	Travail	Arbeit	Trabajo	Lavoro	Werk	Travail	Do pracy
Holiday	Vacances	Urlaub	Vacaciones	Vacanza	Vakantie	Vacances	Wakacyjny
\.


--
-- Data for Name: aspect_pattern; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_pattern (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) FROM stdin;
Solid	Uni	Uni	Liso	Tinta unita	Effen	Uni	Jednolity
Striped	Rayé	Gestreift	Rayas	Righe	Gestreept	Rayé	W paski
Checked	À carreaux	Kariert	Cuadros	A quadri	Geruit	À carreaux	W kratę
Floral	Fleuri	Geblümt	Floral	Floreale	Bloemen	Fleuri	W kwiaty
Animal Print	Imprimé animal	Tiermuster	Estampado animal	Animalier	Dierenprint	Imprimé animal	Zwierzęcy
Camouflage	Camouflage	Camouflage	Camuflaje	Mimetico	Camouflage	Camouflage	Moro
Paisley	Paisley	Paisley	Cachemir	Paisley	Paisley	Paisley	Paisley
Polka Dot	À pois	Gepunktet	Lunares	A pois	Stippen	À pois	W groszki
Graphic	Graphique	Grafik	Gráfico	Grafico	Grafisch	Graphique	Graficzny
Logo	Logo	Logo	Logotipo	Logo	Logo	Logo	Logo
\.


--
-- Data for Name: aspect_rise; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_rise (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) FROM stdin;
Low	Taille basse	Niedrig	Tiro bajo	Bassa	Laag	Taille basse	Niski
Mid	Taille moyenne	Mittel	Tiro medio	Media	Midden	Taille moyenne	Średni
High	Taille haute	Hoch	Tiro alto	Alta	Hoog	Taille haute	Wysoki
\.


--
-- Data for Name: aspect_size; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_size (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) FROM stdin;
XS	XS	XS	XS	XS	XS	XS	XS
S	S	S	S	S	S	S	S
M	M	M	M	M	M	M	M
L	L	L	L	L	L	L	L
XL	XL	XL	XL	XL	XL	XL	XL
XXL	XXL	XXL	XXL	XXL	XXL	XXL	XXL
One Size	Taille unique	Einheitsgröße	Talla única	Taglia unica	One size	Taille unique	Jeden rozmiar
\.


--
-- Data for Name: aspect_sleeve_length; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_sleeve_length (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) FROM stdin;
Short Sleeve	Manches courtes	Kurzarm	Manga corta	Manica corta	Korte mouw	Manches courtes	Krótki rękaw
Long Sleeve	Manches longues	Langarm	Manga larga	Manica lunga	Lange mouw	Manches longues	Długi rękaw
3/4 Sleeve	Manches 3/4	3/4-Arm	Manga 3/4	Manica 3/4	3/4 mouw	Manches 3/4	Rękaw 3/4
Sleeveless	Sans manches	Ärmellos	Sin mangas	Senza maniche	Mouwloos	Sans manches	Bez rękawów
\.


--
-- Data for Name: aspect_style; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_style (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) FROM stdin;
Casual	Décontracté	Casual	Casual	Casual	Casual	Décontracté	Casualowy
Formal	Habillé	Formal	Formal	Formale	Formeel	Habillé	Formalny
Sporty	Sportif	Sportlich	Deportivo	Sportivo	Sportief	Sportif	Sportowy
Vintage	Vintage	Vintage	Vintage	Vintage	Vintage	Vintage	Vintage
Streetwear	Streetwear	Streetwear	Streetwear	Streetwear	Streetwear	Streetwear	Streetwear
Basic	Basique	Basic	Básico	Basic	Basic	Basique	Podstawowy
Designer	Designer	Designer	Diseñador	Designer	Designer	Designer	Designerski
\.


--
-- Data for Name: aspect_type; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_type (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) FROM stdin;
Jeans	Jean	Jeans	Vaqueros	Jeans	Jeans	Jean	Dżinsy
T-Shirt	T-shirt	T-Shirt	Camiseta	T-shirt	T-shirt	T-shirt	T-shirt
Shirt	Chemise	Hemd	Camisa	Camicia	Overhemd	Chemise	Koszula
Jacket	Veste	Jacke	Chaqueta	Giacca	Jas	Veste	Kurtka
Coat	Manteau	Mantel	Abrigo	Cappotto	Jas	Manteau	Płaszcz
Dress	Robe	Kleid	Vestido	Vestito	Jurk	Robe	Sukienka
Skirt	Jupe	Rock	Falda	Gonna	Rok	Jupe	Spódnica
Trousers	Pantalon	Hose	Pantalón	Pantaloni	Broek	Pantalon	Spodnie
Shorts	Short	Shorts	Pantalón corto	Pantaloncini	Korte broek	Short	Szorty
Sweater	Pull	Pullover	Jersey	Maglione	Trui	Pull	Sweter
Hoodie	Sweat à capuche	Kapuzenpullover	Sudadera con capucha	Felpa con cappuccio	Hoodie	Sweat à capuche	Bluza z kapturem
Blazer	Blazer	Blazer	Blazer	Blazer	Blazer	Blazer	Marynarka
Polo	Polo	Poloshirt	Polo	Polo	Poloshirt	Polo	Polo
\.


--
-- Data for Name: aspect_waist_size; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.aspect_waist_size (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) FROM stdin;
\.


--
-- Data for Name: category_mapping; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.category_mapping (id, my_category, my_gender, ebay_category_id, ebay_name_en, created_at) FROM stdin;
1	t-shirt	men	15687	T-Shirts	2026-01-09 09:49:11.142491
2	t-shirt	women	53159	Tops & Shirts	2026-01-09 09:49:11.142491
3	tank-top	men	15687	T-Shirts	2026-01-09 09:49:11.142491
4	tank-top	women	53159	Tops & Shirts	2026-01-09 09:49:11.142491
5	shirt	men	57990	Casual Shirts & Tops	2026-01-09 09:49:11.142491
6	shirt	women	53159	Tops & Shirts	2026-01-09 09:49:11.142491
7	blouse	women	53159	Tops & Shirts	2026-01-09 09:49:11.142491
8	top	women	53159	Tops & Shirts	2026-01-09 09:49:11.142491
9	bodysuit	women	53159	Tops & Shirts	2026-01-09 09:49:11.142491
10	corset	women	53159	Tops & Shirts	2026-01-09 09:49:11.142491
11	bustier	women	53159	Tops & Shirts	2026-01-09 09:49:11.142491
12	camisole	women	53159	Tops & Shirts	2026-01-09 09:49:11.142491
13	crop-top	women	53159	Tops & Shirts	2026-01-09 09:49:11.142491
14	polo	men	185101	Polos	2026-01-09 09:49:11.142491
15	polo	women	53159	Tops & Shirts	2026-01-09 09:49:11.142491
16	sweater	men	11484	Jumpers & Cardigans	2026-01-09 09:49:11.142491
17	sweater	women	63866	Jumpers & Cardigans	2026-01-09 09:49:11.142491
18	cardigan	men	11484	Jumpers & Cardigans	2026-01-09 09:49:11.142491
19	cardigan	women	63866	Jumpers & Cardigans	2026-01-09 09:49:11.142491
20	sweatshirt	men	155183	Hoodies & Sweatshirts	2026-01-09 09:49:11.142491
21	sweatshirt	women	155226	Hoodies & Sweatshirts	2026-01-09 09:49:11.142491
22	hoodie	men	155183	Hoodies & Sweatshirts	2026-01-09 09:49:11.142491
23	hoodie	women	155226	Hoodies & Sweatshirts	2026-01-09 09:49:11.142491
24	fleece	men	155183	Hoodies & Sweatshirts	2026-01-09 09:49:11.142491
25	fleece	women	155226	Hoodies & Sweatshirts	2026-01-09 09:49:11.142491
26	half-zip	men	155183	Hoodies & Sweatshirts	2026-01-09 09:49:11.142491
27	half-zip	women	155226	Hoodies & Sweatshirts	2026-01-09 09:49:11.142491
28	overshirt	men	57990	Casual Shirts & Tops	2026-01-09 09:49:11.142491
29	overshirt	women	53159	Tops & Shirts	2026-01-09 09:49:11.142491
30	pants	men	57989	Trousers	2026-01-09 09:49:11.142491
31	pants	women	63863	Trousers	2026-01-09 09:49:11.142491
32	chinos	men	57989	Trousers	2026-01-09 09:49:11.142491
33	chinos	women	63863	Trousers	2026-01-09 09:49:11.142491
34	cargo-pants	men	57989	Trousers	2026-01-09 09:49:11.142491
35	cargo-pants	women	63863	Trousers	2026-01-09 09:49:11.142491
36	dress-pants	men	57989	Trousers	2026-01-09 09:49:11.142491
37	dress-pants	women	63863	Trousers	2026-01-09 09:49:11.142491
38	culottes	women	63863	Trousers	2026-01-09 09:49:11.142491
39	overalls	men	57989	Trousers	2026-01-09 09:49:11.142491
40	jeans	men	11483	Jeans	2026-01-09 09:49:11.142491
41	jeans	women	11554	Jeans	2026-01-09 09:49:11.142491
42	joggers	men	260956	Activewear Trousers	2026-01-09 09:49:11.142491
43	joggers	women	260954	Activewear Trousers	2026-01-09 09:49:11.142491
44	shorts	men	15689	Shorts	2026-01-09 09:49:11.142491
45	shorts	women	11555	Shorts	2026-01-09 09:49:11.142491
46	bermuda	men	15689	Shorts	2026-01-09 09:49:11.142491
47	bermuda	women	11555	Shorts	2026-01-09 09:49:11.142491
48	skirt	women	63864	Skirts	2026-01-09 09:49:11.142491
49	leggings	women	169001	Leggings	2026-01-09 09:49:11.142491
50	jacket	men	57988	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
51	jacket	women	63862	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
52	bomber	men	57988	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
53	bomber	women	63862	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
54	puffer	men	57988	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
55	puffer	women	63862	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
56	coat	men	57988	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
57	coat	women	63862	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
58	trench	men	57988	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
59	trench	women	63862	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
60	parka	men	57988	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
61	parka	women	63862	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
62	raincoat	men	57988	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
63	raincoat	women	63862	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
64	windbreaker	men	57988	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
65	windbreaker	women	63862	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
66	blazer	men	57988	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
67	blazer	women	63862	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
68	vest	men	57988	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
69	vest	women	63862	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
70	cape	women	63862	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
71	poncho	men	57988	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
72	poncho	women	63862	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
73	kimono	women	63862	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
74	suit-vest	men	57988	Coats Jackets & Waistcoats	2026-01-09 09:49:11.142491
75	dress	women	63861	Dresses	2026-01-09 09:49:11.142491
76	jumpsuit	women	3009	Jumpsuits & Playsuits	2026-01-09 09:49:11.142491
77	romper	women	3009	Jumpsuits & Playsuits	2026-01-09 09:49:11.142491
78	overalls	women	3009	Jumpsuits & Playsuits	2026-01-09 09:49:11.142491
79	suit	men	3001	Suits & Tailoring	2026-01-09 09:49:11.142491
80	suit	women	63865	Suits & Suit Separates	2026-01-09 09:49:11.142491
81	tuxedo	men	3001	Suits & Tailoring	2026-01-09 09:49:11.142491
82	womens-suit	women	63865	Suits & Suit Separates	2026-01-09 09:49:11.142491
83	sports-bra	women	185082	Activewear Tops	2026-01-09 09:49:11.142491
84	sports-top	men	185076	Activewear Tops	2026-01-09 09:49:11.142491
85	sports-top	women	185082	Activewear Tops	2026-01-09 09:49:11.142491
86	sports-shorts	men	260957	Activewear Shorts	2026-01-09 09:49:11.142491
87	sports-shorts	women	260955	Activewear Shorts	2026-01-09 09:49:11.142491
88	sports-leggings	women	260954	Activewear Trousers	2026-01-09 09:49:11.142491
89	sports-jersey	men	185076	Activewear Tops	2026-01-09 09:49:11.142491
90	sports-jersey	women	185082	Activewear Tops	2026-01-09 09:49:11.142491
91	tracksuit	men	185708	Tracksuits & Sets	2026-01-09 09:49:11.142491
92	tracksuit	women	185084	Tracksuits & Sets	2026-01-09 09:49:11.142491
93	swimsuit	men	15690	Swimwear	2026-01-09 09:49:11.142491
94	swimsuit	women	63867	Swimwear	2026-01-09 09:49:11.142491
95	bikini	women	63867	Swimwear	2026-01-09 09:49:11.142491
\.


--
-- Data for Name: exchange_rate; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.exchange_rate (id, currency, rate, source, created_at, updated_at) FROM stdin;
1	GBP	0.856000	ECB	2026-01-09 09:49:11.142491+00	2026-01-09 09:49:11.142491+00
2	PLN	4.320000	ECB	2026-01-09 09:49:11.142491+00	2026-01-09 09:49:11.142491+00
\.


--
-- Data for Name: marketplace_config; Type: TABLE DATA; Schema: ebay; Owner: stoflow_user
--

COPY ebay.marketplace_config (id, marketplace_id, country_code, site_id, currency, is_active, created_at, updated_at) FROM stdin;
1	EBAY_FR	FR	71	EUR	t	2026-01-09 09:49:11.142491+00	2026-01-09 09:49:11.142491+00
2	EBAY_GB	UK	3	GBP	t	2026-01-09 09:49:11.142491+00	2026-01-09 09:49:11.142491+00
3	EBAY_DE	DE	77	EUR	t	2026-01-09 09:49:11.142491+00	2026-01-09 09:49:11.142491+00
4	EBAY_IT	IT	101	EUR	t	2026-01-09 09:49:11.142491+00	2026-01-09 09:49:11.142491+00
5	EBAY_ES	ES	186	EUR	t	2026-01-09 09:49:11.142491+00	2026-01-09 09:49:11.142491+00
6	EBAY_NL	NL	146	EUR	t	2026-01-09 09:49:11.142491+00	2026-01-09 09:49:11.142491+00
7	EBAY_BE	BE	23	EUR	t	2026-01-09 09:49:11.142491+00	2026-01-09 09:49:11.142491+00
8	EBAY_PL	PL	212	PLN	t	2026-01-09 09:49:11.142491+00	2026-01-09 09:49:11.142491+00
\.


--
-- Data for Name: brands; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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
3sixteen	\N	623847	f	\N	\N
Adidas	\N	14	f	\N	\N
adidas	\N	14	f	\N	\N
Nike	\N	53	f	\N	\N
nike	\N	53	f	\N	\N
a.p.c.	\N	251	f	\N	\N
acne studios	\N	180798	f	\N	\N
acronym	\N	712647	f	\N	\N
affliction	\N	272035	f	\N	\N
akademiks	\N	130046	f	\N	\N
anchor blue	\N	44519	f	\N	\N
and wander	\N	1512834	f	\N	\N
arc'teryx	\N	319730	f	\N	\N
auralee	\N	2053426	f	\N	\N
avirex	\N	4565	f	\N	\N
bape	\N	4691320	f	\N	\N
battenwear	\N	1102097	f	\N	\N
ben davis	\N	85872	f	\N	\N
bershka	\N	140	f	\N	\N
big train	\N	2496245	f	\N	\N
blind	\N	56158	f	\N	\N
brixton	\N	56682	f	\N	\N
bugle boy	\N	306806	f	\N	\N
burberrys	\N	364	f	\N	\N
butter goods	\N	901821	f	\N	\N
calvin klein	\N	255	f	\N	\N
carhartt	\N	362	f	\N	\N
celio	\N	2615	f	\N	\N
chevignon	\N	12205	f	\N	\N
coogi	\N	21359	f	\N	\N
corteiz	\N	3036449	f	\N	\N
crooks & castles	\N	48527	f	\N	\N
denham	\N	102502	f	\N	\N
dickies	\N	65	f	\N	\N
diesel	\N	161	f	\N	\N
dime	\N	326479	f	\N	\N
divided	\N	15452320	f	\N	\N
dynam	\N	24329	f	\N	\N
ecko unltd	\N	30575	f	\N	\N
ecko unltd.	\N	30575	f	\N	\N
ed hardy	\N	1761	f	\N	\N
edwin	\N	4471	f	\N	\N
element	\N	2037	f	\N	\N
energie	\N	15985	f	\N	\N
engineered garments	\N	609050	f	\N	\N
enyce	\N	76428	f	\N	\N
evisu	\N	214088	f	\N	\N
foot korner	\N	381270	f	\N	\N
freenote cloth	\N	2125308	f	\N	\N
fubu	\N	57822	f	\N	\N
full count	\N	2890372	f	\N	\N
g-star raw	\N	2782756	f	\N	\N
g-unit	\N	42813	f	\N	\N
gant jeans	\N	6075	f	\N	\N
gap	\N	6	f	\N	\N
goldwin	\N	330213	f	\N	\N
gramicci	\N	896209	f	\N	\N
guess	\N	20	f	\N	\N
heron preston	\N	389625	f	\N	\N
homecore	\N	209540	f	\N	\N
houdini	\N	379143	f	\N	\N
huf	\N	14185	f	\N	\N
indigofera	\N	742615	f	\N	\N
iron heart	\N	492896	f	\N	\N
izod	\N	238478	f	\N	\N
jackwolfskin	\N	147650	f	\N	\N
japan blue	\N	451051	f	\N	\N
jizo	\N	10037867	f	\N	\N
jnco	\N	290909	f	\N	\N
kangaroo poo	\N	779366	f	\N	\N
kapital	\N	576107	f	\N	\N
karl kani	\N	13989	f	\N	\N
kiabi	\N	60	f	\N	\N
kiko kostadinov	\N	5821136	f	\N	\N
klättermusen	\N	1638071	f	\N	\N
lacoste	\N	304	f	\N	\N
lagerfeld	\N	103	f	\N	\N
lee	\N	63	f	\N	\N
lee cooper	\N	407	f	\N	\N
lemaire	\N	295938	f	\N	\N
levi's	\N	10	f	\N	\N
levi's made & crafted	\N	5982593	f	\N	\N
levi's vintage clothing	\N	5983207	f	\N	\N
maharishi	\N	326054	f	\N	\N
maison mihara yasuhiro	\N	2514944	f	\N	\N
majestic	\N	5725	f	\N	\N
marni	\N	12251	f	\N	\N
mecca	\N	238862	f	\N	\N
mlb	\N	77420	f	\N	\N
momotaro	\N	358913	f	\N	\N
mont bell	\N	15088880	f	\N	\N
montbell	\N	615130	f	\N	\N
naked & famous denim	\N	1148437	f	\N	\N
nascar	\N	185574	f	\N	\N
neighborhood	\N	330747	f	\N	\N
nfl	\N	33275	f	\N	\N
nigel cabourn	\N	696416	f	\N	\N
no fear	\N	26101	f	\N	\N
norrøna	\N	356632	f	\N	\N
nudie jeans	\N	95256	f	\N	\N
obey	\N	2069	f	\N	\N
oni arai	\N	17653347	f	\N	\N
orslow	\N	373463	f	\N	\N
our legacy	\N	218132	f	\N	\N
palace	\N	139960	f	\N	\N
pass port	\N	15497435	f	\N	\N
passport	\N	27217	f	\N	\N
pelle pelle	\N	6989	f	\N	\N
phat farm	\N	207738	f	\N	\N
poetic collective	\N	924571	f	\N	\N
pointer	\N	27275	f	\N	\N
polar skate	\N	375147	f	\N	\N
polar skate co.	\N	7006283	f	\N	\N
pop trading company	\N	906755	f	\N	\N
puma	\N	535	f	\N	\N
pure blue japan	\N	859861	f	\N	\N
ralph lauren	\N	88	f	\N	\N
rare humans	\N	5582686	f	\N	\N
red pepper	\N	717159	f	\N	\N
rica lewis	\N	506	f	\N	\N
robin's jean	\N	129064	f	\N	\N
rocawear	\N	29507	f	\N	\N
rogue territory	\N	770322	f	\N	\N
résolute	\N	862485	f	\N	\N
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


--
-- Data for Name: categories; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

COPY product_attributes.categories (name_en, parent_category, name_fr, name_de, name_it, name_es, name_nl, name_pl, genders) FROM stdin;
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
other	\N	Autre	Sonstiges	Altro	Otro	Overig	Inne	\N
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
sports-bra	sportswear	Brassière de sport	Sport-BH	Reggiseno sportivo	Sujetador deportivo	Sportbeha	Biustonosz sportowy	{women,girls}
sports-top	sportswear	T-shirt de sport	Sport-Top	Top sportivo	Top deportivo	Sporttop	Top sportowy	{men,women,boys,girls}
sports-jersey	sportswear	Maillot de sport	Sporttrikot	Maglia sportiva	Camiseta deportiva	Sportshirt	Koszulka sportowa	{men,women,boys,girls}
sports-shorts	sportswear	Short de sport	Sporthose	Shorts sportivi	Pantalones cortos deportivos	Sportshorts	Spodenki sportowe	{men,women,boys,girls}
sports-leggings	sportswear	Legging de sport	Sportleggings	Leggings sportivi	Leggings deportivos	Sportlegging	Legginsy sportowe	{women,girls}
bikini	sportswear	Bikini	Bikini	Bikini	Bikini	Bikini	Bikini	{women,girls}
dress	\N	Robe	Kleid	Vestito	Vestido	Jurk	Sukienka	{women,girls}
romper	\N	Combishort	Playsuit	Tutina	Mono corto	Playsuit	Kombinezon krótki	{women,girls}
overalls	\N	Salopette	Latzhose	Salopette	Peto	Tuinbroek	Ogrodniczki	{men,women,boys,girls}
swim suit	sportswear	Maillot de bain	Badeanzug	Costume da bagno	Bañador	Badpak	Kostium kąpielowy	{men,women,boys,girls}
track suit	sportswear	Survêtement	Trainingsanzug	Tuta	Chándal	Trainingspak	Dres	{men,women,boys,girls}
jump suit	\N	Combinaison	Jumpsuit	Tuta intera	Mono	Jumpsuit	Kombinezon	{men,women,boys,girls}
waistcoat	formalwear	Gilet de costume	Weste	Gilet	Chaleco de traje	Gilet	Kamizelka do garnituru	{men,boys,girls}
\.


--
-- Data for Name: closures; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: colors; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

COPY product_attributes.colors (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl, hex_code, vinted_id, parent_color) FROM stdin;
Charcoal	Gris anthracite	Anthrazit	Antracite	Gris marengo	Antraciet	Antracytowy	\N	3	Gray
Klein blue	\N	Klein-Blau	Blu Klein	Azul Klein	Klein blauw	Błękit Klein	#002FA7	\N	Blue
Vanilla yellow	\N	Vanillegelb	Giallo vaniglia	Amarillo vainilla	Vanillegeel	Waniliowy	#F3E5AB	\N	Yellow
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


--
-- Data for Name: condition_sups; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

COPY product_attributes.condition_sups (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
Faded	Délavé	Ausgeblichen	Sbiadito	Desteñido	Vervaagd	Wyblakły
Resewn	Recousu	Neu genäht	Ricucito	Recosido	Opnieuw genaaid	Przeszyty
Stretched	Étiré	Ausgeleiert	Sformato	Estirado	Uitgerekt	Rozciągnięty
Worn	Usé	Abgetragen	Usurato	Desgastado	Versleten	Zużyty
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


--
-- Data for Name: conditions; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: decades; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: dim1; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: dim2; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: dim3; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: dim4; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: dim5; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: dim6; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: fits; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: genders; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

COPY product_attributes.genders (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl, vinted_id, ebay_gender, etsy_gender) FROM stdin;
Boys	Garçon	Jungen	Bambini	Niños	Jongens	Chłopcy	\N	\N	\N
Girls	Fille	Mädchen	Bambine	Niñas	Meisjes	Dziewczynki	\N	\N	\N
Men	Homme	Herren	Uomo	Hombre	Heren	Mężczyźni	\N	\N	\N
Unisex	Unisexe	Unisex	Unisex	Unisex	Unisex	Unisex	\N	\N	\N
Women	Femme	Damen	Donna	Mujer	Dames	Kobiety	\N	\N	\N
\.


--
-- Data for Name: lengths; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: linings; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

COPY product_attributes.linings (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
Unlined	Sans doublure	Ungefüttert	Senza fodera	Sin forro	Ongevoerd	Bez podszewki
Fully lined	Entièrement doublé	Voll gefüttert	Foderato completamente	Completamente forrado	Volledig gevoerd	Całkowicie podszyte
Partially lined	Partiellement doublé	Teilweise gefüttert	Parzialmente foderato	Parcialmente forrado	Gedeeltelijk gevoerd	Częściowo podszyte
Fleece lined	Doublure polaire	Fleecegefüttert	Foderato in pile	Forro polar	Fleece gevoerd	Podszewka polarowa
\.


--
-- Data for Name: materials; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: necklines; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: origins; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: patterns; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: rises; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

COPY product_attributes.rises (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
High-rise	Taille haute	High-Rise	Vita alta	Tiro alto	Hoge taille	Wysoki stan
Low-rise	Taille basse	Low-Rise	Vita bassa	Tiro bajo	Lage taille	Niski stan
Mid-rise	Taille moyenne	Mid-Rise	Vita media	Tiro medio	Middelhoge taille	Średni stan
Regular rise	Taille normale	Regular Rise	Vita normale	Tiro normal	Normale taille	Normalny stan
Super low-rise	Taille très basse	Super Low-Rise	Vita molto bassa	Tiro muy bajo	Zeer lage taille	Bardzo niski stan
Ultra high-rise	Taille très haute	Ultra High-Rise	Vita molto alta	Tiro muy alto	Zeer hoge taille	Bardzo wysoki stan
\.


--
-- Data for Name: seasons; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

COPY product_attributes.seasons (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
Spring	Printemps	Frühling	Primavera	Primavera	Lente	Wiosna
Summer	Été	Sommer	Estate	Verano	Zomer	Lato
Autumn	Automne	Herbst	Autunno	Otoño	Herfst	Jesień
Winter	Hiver	Winter	Inverno	Invierno	Winter	Zima
All seasons	Toutes saisons	Ganzjährig	Tutte le stagioni	Todas las temporadas	Alle seizoenen	Wszystkie pory roku
\.


--
-- Data for Name: sizes_normalized; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: sizes_original; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

COPY product_attributes.sizes_original (name, created_at) FROM stdin;
\.


--
-- Data for Name: sleeve_lengths; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

COPY product_attributes.sleeve_lengths (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
3/4 sleeve	Manches 3/4	3/4-Arm	Manica 3/4	Manga 3/4	3/4 mouw	Rękaw 3/4
Long sleeve	Manches longues	Langarm	Manica lunga	Manga larga	Lange mouw	Długi rękaw
Short sleeve	Manches courtes	Kurzarm	Manica corta	Manga corta	Korte mouw	Krótki rękaw
Sleeveless	Sans manches	Ärmellos	Senza maniche	Sin mangas	Mouwloos	Bez rękawów
\.


--
-- Data for Name: sports; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: stretches; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

COPY product_attributes.stretches (name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl) FROM stdin;
No stretch	Aucun stretch	Kein stretch	Nessun stretch	Sin elasticidad	Geen stretch	Bez Rozciągliwości
Slight stretch	Léger stretch	Leichter stretch	Leggero stretch	elasticidad Ligera	Lichte stretch	Lekka rozciągliwość
Moderate stretch	stretch Modéré	Mäßiger stretch	stretch Moderato	elasticidad Moderada	Matige stretch	Umiarkowana rozciągliwość
Super stretch	Super stretch	Super stretch	Super stretch	Super elasticidad	Super stretch	Super rozciągliwość
\.


--
-- Data for Name: trends; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: unique_features; Type: TABLE DATA; Schema: product_attributes; Owner: stoflow_user
--

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


--
-- Data for Name: admin_audit_logs; Type: TABLE DATA; Schema: public; Owner: stoflow_user
--

COPY public.admin_audit_logs (id, admin_id, action, resource_type, resource_id, resource_name, details, ip_address, user_agent, created_at) FROM stdin;
\.


--
-- Data for Name: ai_credits; Type: TABLE DATA; Schema: public; Owner: stoflow_user
--

COPY public.ai_credits (id, user_id, ai_credits_purchased, ai_credits_used_this_month, last_reset_date, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: stoflow_user
--

COPY public.alembic_version (version_num) FROM stdin;
53a8b38c9737
\.


--
-- Data for Name: clothing_prices; Type: TABLE DATA; Schema: public; Owner: stoflow_user
--

COPY public.clothing_prices (brand, category, base_price, updated_at) FROM stdin;
\.


--
-- Data for Name: doc_articles; Type: TABLE DATA; Schema: public; Owner: stoflow_user
--

COPY public.doc_articles (id, category_id, slug, title, summary, content, display_order, is_active, created_at, updated_at) FROM stdin;
1	1	premiers-pas	Premiers pas avec Stoflow	Découvrez comment démarrer avec Stoflow et configurer votre compte.	# Premiers pas avec Stoflow\n\nBienvenue sur Stoflow ! Ce guide vous accompagne dans vos premiers pas.\n\n## 1. Créer votre compte\n\nRendez-vous sur la page d'inscription et remplissez le formulaire avec vos informations.\n\n## 2. Connecter votre première marketplace\n\nUne fois connecté, accédez à **Paramètres > Intégrations** pour connecter Vinted, eBay ou Etsy.\n\n## 3. Créer votre premier produit\n\nCliquez sur **Produits > Créer un produit** pour ajouter votre premier article.\n\n---\n\nBesoin d'aide ? Consultez notre FAQ ou contactez notre support.	0	t	2026-01-09 09:49:11.142491+00	2026-01-09 09:49:11.142491+00
2	1	creer-produit	Comment créer un produit	Apprenez à créer et publier vos produits sur les marketplaces.	# Comment créer un produit\n\nCe guide vous explique comment créer un produit dans Stoflow.\n\n## Étape 1 : Informations de base\n\n- **Titre** : Le nom de votre produit\n- **Description** : Une description détaillée\n- **Prix** : Le prix de vente\n\n## Étape 2 : Photos\n\nAjoutez jusqu'à 10 photos de votre produit. La première photo sera la photo principale.\n\n## Étape 3 : Attributs\n\nSélectionnez la catégorie, la taille, la couleur et les autres attributs.\n\n## Étape 4 : Publication\n\nCliquez sur **Publier** pour envoyer votre produit sur les marketplaces connectées.	1	t	2026-01-09 09:49:11.142491+00	2026-01-09 09:49:11.142491+00
3	2	abonnement	Questions sur les abonnements	Tout savoir sur les plans et tarifs Stoflow.	# Questions sur les abonnements\n\n## Quels sont les plans disponibles ?\n\nStoflow propose 4 plans :\n- **Gratuit** : Pour découvrir la plateforme (50 produits, 1 marketplace)\n- **Pro** : Pour les vendeurs actifs (500 produits, toutes marketplaces)\n- **Business** : Pour les professionnels (2000 produits)\n- **Enterprise** : Pour les grandes équipes (illimité)\n\n## Puis-je changer de plan ?\n\nOui, vous pouvez upgrader ou downgrader à tout moment depuis **Paramètres > Abonnement**.\n\n## Comment fonctionne la facturation ?\n\nLa facturation est mensuelle ou annuelle (avec 20% de réduction).	0	t	2026-01-09 09:49:11.142491+00	2026-01-09 09:49:11.142491+00
\.


--
-- Data for Name: doc_categories; Type: TABLE DATA; Schema: public; Owner: stoflow_user
--

COPY public.doc_categories (id, slug, name, description, icon, display_order, is_active, created_at, updated_at) FROM stdin;
1	guide	Guide d'utilisation	Apprenez à utiliser Stoflow étape par étape	pi-book	0	t	2026-01-09 09:49:11.142491+00	2026-01-09 09:49:11.142491+00
2	faq	FAQ	Questions fréquemment posées	pi-question-circle	1	t	2026-01-09 09:49:11.142491+00	2026-01-09 09:49:11.142491+00
\.


--
-- Data for Name: migration_errors; Type: TABLE DATA; Schema: public; Owner: stoflow_user
--

COPY public.migration_errors (id, schema_name, product_id, migration_name, error_type, error_details, migrated_at) FROM stdin;
\.


--
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: stoflow_user
--

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


--
-- Data for Name: revoked_tokens; Type: TABLE DATA; Schema: public; Owner: stoflow_user
--

COPY public.revoked_tokens (token_hash, revoked_at, expires_at) FROM stdin;
\.


--
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: stoflow_user
--

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


--
-- Data for Name: subscription_features; Type: TABLE DATA; Schema: public; Owner: stoflow_user
--

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


--
-- Data for Name: subscription_quotas; Type: TABLE DATA; Schema: public; Owner: stoflow_user
--

COPY public.subscription_quotas (id, tier, max_products, max_platforms, ai_credits_monthly, price, display_name, description, annual_discount_percent, is_popular, cta_text, display_order) FROM stdin;
1	FREE	30	2	15	0.00	Gratuit	Pour découvrir Stoflow	0	f	Commencer	0
2	STARTER	150	3	75	19.00	Pro	Pour les vendeurs actifs	20	t	Essai gratuit 14 jours	1
3	PRO	500	5	250	49.00	Business	Pour les professionnels	20	f	Essai gratuit 14 jours	2
4	ENTERPRISE	999999	999999	999999	199.00	Enterprise	Pour les grandes équipes	20	f	Nous contacter	3
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: stoflow_user
--

COPY public.users (id, email, hashed_password, full_name, role, is_active, last_login, subscription_tier, subscription_status, created_at, updated_at, business_name, account_type, business_type, estimated_products, siret, vat_number, phone, country, language, subscription_tier_id, current_products_count, current_platforms_count, stripe_customer_id, stripe_subscription_id, failed_login_attempts, last_failed_login, locked_until, email_verified, email_verification_token, email_verification_expires, password_changed_at) FROM stdin;
1	plugin-test@stoflow.com	$2b$12$7jNMi2j2ER/wP3Ar92k4CODQRa4RoSp0mHW5l14.5PQvtx9xjWU9W	Plugin Test	ADMIN	t	\N	PRO	active	2026-01-09 10:34:17.974241+00	2026-01-09 10:34:17.974241+00	\N	individual	\N	\N	\N	\N	\N	FR	fr	3	0	0	\N	\N	0	\N	\N	t	\N	\N	\N
\.


--
-- Data for Name: ai_generation_logs; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.ai_generation_logs (id, product_id, model, prompt_tokens, completion_tokens, total_tokens, total_cost, cached, generation_time_ms, error_message, created_at) FROM stdin;
\.


--
-- Data for Name: batch_jobs; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.batch_jobs (id, batch_id, marketplace, action_code, total_count, completed_count, failed_count, cancelled_count, status, priority, created_by_user_id, created_at, started_at, completed_at) FROM stdin;
\.


--
-- Data for Name: ebay_credentials; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.ebay_credentials (id, ebay_user_id, access_token, refresh_token, access_token_expires_at, refresh_token_expires_at, sandbox_mode, is_connected, last_sync, created_at, updated_at, username, email, account_type, business_name, first_name, last_name, phone, address, marketplace, feedback_score, feedback_percentage, seller_level, registration_date) FROM stdin;
\.


--
-- Data for Name: ebay_orders; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.ebay_orders (id, order_id, marketplace_id, buyer_username, buyer_email, shipping_name, shipping_address, shipping_city, shipping_postal_code, shipping_country, total_price, currency, shipping_cost, order_fulfillment_status, order_payment_status, creation_date, paid_date, tracking_number, shipping_carrier, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: ebay_orders_products; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.ebay_orders_products (id, order_id, line_item_id, sku, sku_original, title, quantity, unit_price, total_price, currency, legacy_item_id, created_at) FROM stdin;
\.


--
-- Data for Name: ebay_products; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.ebay_products (id, ebay_sku, product_id, title, description, price, currency, brand, size, color, material, category_id, category_name, condition, condition_description, quantity, availability_type, marketplace_id, ebay_listing_id, ebay_offer_id, image_urls, aspects, status, listing_format, listing_duration, package_weight_value, package_weight_unit, location, country, published_at, last_synced_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: ebay_products_marketplace; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.ebay_products_marketplace (sku_derived, product_id, marketplace_id, ebay_offer_id, ebay_listing_id, status, error_message, published_at, sold_at, last_sync_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: ebay_promoted_listings; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.ebay_promoted_listings (id, campaign_id, campaign_name, marketplace_id, product_id, sku_derived, ad_id, listing_id, bid_percentage, ad_status, total_clicks, total_impressions, total_sales, total_sales_amount, total_ad_fees, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: etsy_credentials; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.etsy_credentials (id, access_token, refresh_token, access_token_expires_at, refresh_token_expires_at, shop_id, shop_name, shop_url, user_id_etsy, email, is_connected, last_sync, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: marketplace_jobs; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.marketplace_jobs (id, batch_id, action_type_id, product_id, status, priority, error_message, retry_count, started_at, completed_at, expires_at, created_at, result_data, marketplace, batch_job_id, idempotency_key) FROM stdin;
\.


--
-- Data for Name: marketplace_tasks; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.marketplace_tasks (id, task_type, status, payload, result, error_message, product_id, created_at, started_at, completed_at, retry_count, max_retries, platform, http_method, path, job_id, description) FROM stdin;
\.


--
-- Data for Name: pending_instructions; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.pending_instructions (id, user_id, action, status, result, error, created_at, completed_at, expires_at) FROM stdin;
\.


--
-- Data for Name: product_colors; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.product_colors (product_id, color, is_primary) FROM stdin;
\.


--
-- Data for Name: product_condition_sups; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.product_condition_sups (product_id, condition_sup) FROM stdin;
\.


--
-- Data for Name: product_images; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.product_images (id, product_id, image_path, display_order, created_at) FROM stdin;
\.


--
-- Data for Name: product_materials; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.product_materials (product_id, material, percentage) FROM stdin;
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.products (id, sku, title, description, price, category, brand, size_original, fit, gender, season, rise, closure, sleeve_length, origin, decade, trend, location, model, dim1, dim2, dim3, dim4, dim5, dim6, stock_quantity, images, status, scheduled_publish_at, published_at, sold_at, deleted_at, integration_metadata, created_at, updated_at, pricing_edit, pricing_rarity, pricing_quality, pricing_details, pricing_style, marking, sport, neckline, length, pattern, condition, size_normalized, unique_feature, stretch, version_number) FROM stdin;
\.


--
-- Data for Name: publication_history; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.publication_history (id, product_id, status, platform_product_id, error_message, metadata, created_at) FROM stdin;
\.


--
-- Data for Name: vinted_connection; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.vinted_connection (vinted_user_id, login, user_id, created_at, last_sync, is_connected, disconnected_at, last_datadome_ping, datadome_status, item_count, total_items_count, given_item_count, taken_item_count, followers_count, feedback_count, feedback_reputation, positive_feedback_count, negative_feedback_count, is_business, is_on_holiday, stats_updated_at) FROM stdin;
\.


--
-- Data for Name: vinted_conversations; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.vinted_conversations (conversation_id, opposite_user_id, opposite_user_login, opposite_user_photo_url, last_message_preview, is_unread, unread_count, item_count, item_id, item_title, item_photo_url, transaction_id, updated_at_vinted, created_at, updated_at, last_synced_at) FROM stdin;
\.


--
-- Data for Name: vinted_error_logs; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.vinted_error_logs (id, product_id, operation, error_type, error_message, error_details, created_at) FROM stdin;
\.


--
-- Data for Name: vinted_job_stats; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.vinted_job_stats (id, action_type_id, date, total_jobs, success_count, failure_count, avg_duration_ms, created_at) FROM stdin;
\.


--
-- Data for Name: vinted_messages; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.vinted_messages (id, conversation_id, vinted_message_id, entity_type, sender_id, sender_login, body, title, subtitle, offer_price, offer_status, is_from_current_user, created_at_vinted, created_at) FROM stdin;
\.


--
-- Data for Name: vinted_products; Type: TABLE DATA; Schema: template_tenant; Owner: stoflow_user
--

COPY template_tenant.vinted_products (vinted_id, title, description, price, currency, brand, size, color, category, status, condition, is_draft, is_closed, view_count, favourite_count, url, photos_data, created_at, updated_at, total_price, brand_id, size_id, catalog_id, condition_id, material, measurements, measurement_width, measurement_length, manufacturer_labelling, is_reserved, is_hidden, seller_id, seller_login, service_fee, buyer_protection_fee, shipping_price, published_at, product_id, color1_id, color2_id, color2, status_id, is_unisex, measurement_unit, item_attributes) FROM stdin;
\.


--
-- Data for Name: ai_generation_logs; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.ai_generation_logs (id, product_id, model, prompt_tokens, completion_tokens, total_tokens, total_cost, cached, generation_time_ms, error_message, created_at) FROM stdin;
\.


--
-- Data for Name: batch_jobs; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.batch_jobs (id, batch_id, marketplace, action_code, total_count, completed_count, failed_count, cancelled_count, status, priority, created_by_user_id, created_at, started_at, completed_at) FROM stdin;
\.


--
-- Data for Name: ebay_credentials; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.ebay_credentials (id, ebay_user_id, access_token, refresh_token, access_token_expires_at, refresh_token_expires_at, sandbox_mode, is_connected, last_sync, created_at, updated_at, username, email, account_type, business_name, first_name, last_name, phone, address, marketplace, feedback_score, feedback_percentage, seller_level, registration_date) FROM stdin;
\.


--
-- Data for Name: ebay_orders; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.ebay_orders (id, order_id, marketplace_id, buyer_username, buyer_email, shipping_name, shipping_address, shipping_city, shipping_postal_code, shipping_country, total_price, currency, shipping_cost, order_fulfillment_status, order_payment_status, creation_date, paid_date, tracking_number, shipping_carrier, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: ebay_orders_products; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.ebay_orders_products (id, order_id, line_item_id, sku, sku_original, title, quantity, unit_price, total_price, currency, legacy_item_id, created_at) FROM stdin;
\.


--
-- Data for Name: ebay_products; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.ebay_products (id, ebay_sku, product_id, title, description, price, currency, brand, size, color, material, category_id, category_name, condition, condition_description, quantity, availability_type, marketplace_id, ebay_listing_id, ebay_offer_id, image_urls, aspects, status, listing_format, listing_duration, package_weight_value, package_weight_unit, location, country, published_at, last_synced_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: ebay_products_marketplace; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.ebay_products_marketplace (sku_derived, product_id, marketplace_id, ebay_offer_id, ebay_listing_id, status, error_message, published_at, sold_at, last_sync_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: ebay_promoted_listings; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.ebay_promoted_listings (id, campaign_id, campaign_name, marketplace_id, product_id, sku_derived, ad_id, listing_id, bid_percentage, ad_status, total_clicks, total_impressions, total_sales, total_sales_amount, total_ad_fees, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: etsy_credentials; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.etsy_credentials (id, access_token, refresh_token, access_token_expires_at, refresh_token_expires_at, shop_id, shop_name, shop_url, user_id_etsy, email, is_connected, last_sync, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: marketplace_jobs; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.marketplace_jobs (id, batch_id, action_type_id, product_id, status, priority, error_message, retry_count, started_at, completed_at, expires_at, created_at, result_data, marketplace, batch_job_id, idempotency_key) FROM stdin;
\.


--
-- Data for Name: marketplace_tasks; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.marketplace_tasks (id, task_type, status, payload, result, error_message, product_id, created_at, started_at, completed_at, retry_count, max_retries, platform, http_method, path, job_id, description) FROM stdin;
\.


--
-- Data for Name: pending_instructions; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.pending_instructions (id, user_id, action, status, result, error, created_at, completed_at, expires_at) FROM stdin;
\.


--
-- Data for Name: product_colors; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.product_colors (product_id, color, is_primary) FROM stdin;
\.


--
-- Data for Name: product_condition_sups; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.product_condition_sups (product_id, condition_sup) FROM stdin;
\.


--
-- Data for Name: product_images; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.product_images (id, product_id, image_path, display_order, created_at) FROM stdin;
\.


--
-- Data for Name: product_materials; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.product_materials (product_id, material, percentage) FROM stdin;
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.products (id, sku, title, description, price, category, brand, size_original, fit, gender, season, rise, closure, sleeve_length, origin, decade, trend, location, model, dim1, dim2, dim3, dim4, dim5, dim6, stock_quantity, images, status, scheduled_publish_at, published_at, sold_at, deleted_at, integration_metadata, created_at, updated_at, pricing_edit, pricing_rarity, pricing_quality, pricing_details, pricing_style, marking, sport, neckline, length, pattern, condition, size_normalized, unique_feature, stretch, version_number) FROM stdin;
\.


--
-- Data for Name: publication_history; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.publication_history (id, product_id, status, platform_product_id, error_message, metadata, created_at) FROM stdin;
\.


--
-- Data for Name: vinted_connection; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.vinted_connection (vinted_user_id, login, user_id, created_at, last_sync, is_connected, disconnected_at, last_datadome_ping, datadome_status, item_count, total_items_count, given_item_count, taken_item_count, followers_count, feedback_count, feedback_reputation, positive_feedback_count, negative_feedback_count, is_business, is_on_holiday, stats_updated_at) FROM stdin;
\.


--
-- Data for Name: vinted_conversations; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.vinted_conversations (conversation_id, opposite_user_id, opposite_user_login, opposite_user_photo_url, last_message_preview, is_unread, unread_count, item_count, item_id, item_title, item_photo_url, transaction_id, updated_at_vinted, created_at, updated_at, last_synced_at) FROM stdin;
\.


--
-- Data for Name: vinted_error_logs; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.vinted_error_logs (id, product_id, operation, error_type, error_message, error_details, created_at) FROM stdin;
\.


--
-- Data for Name: vinted_job_stats; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.vinted_job_stats (id, action_type_id, date, total_jobs, success_count, failure_count, avg_duration_ms, created_at) FROM stdin;
\.


--
-- Data for Name: vinted_messages; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.vinted_messages (id, conversation_id, vinted_message_id, entity_type, sender_id, sender_login, body, title, subtitle, offer_price, offer_status, is_from_current_user, created_at_vinted, created_at) FROM stdin;
\.


--
-- Data for Name: vinted_products; Type: TABLE DATA; Schema: user_1; Owner: stoflow_user
--

COPY user_1.vinted_products (vinted_id, title, description, price, currency, brand, size, color, category, status, condition, is_draft, is_closed, view_count, favourite_count, url, photos_data, created_at, updated_at, total_price, brand_id, size_id, catalog_id, condition_id, material, measurements, measurement_width, measurement_length, manufacturer_labelling, is_reserved, is_hidden, seller_id, seller_login, service_fee, buyer_protection_fee, shipping_price, published_at, product_id, color1_id, color2_id, color2, status_id, is_unisex, measurement_unit, item_attributes) FROM stdin;
\.


--
-- Data for Name: action_types; Type: TABLE DATA; Schema: vinted; Owner: stoflow_user
--

COPY vinted.action_types (id, code, name, description, priority, is_batch, rate_limit_ms, max_retries, timeout_seconds, created_at) FROM stdin;
1	message	Respond to message	Reply to Vinted buyer messages	1	f	1000	3	30	2026-01-09 09:49:11.142491+00
2	orders	Fetch orders	Retrieve new orders/sales from Vinted	3	t	1500	3	60	2026-01-09 09:49:11.142491+00
3	publish	Publish product	Create a new listing on Vinted	3	f	2500	3	120	2026-01-09 09:49:11.142491+00
4	update	Update product	Modify price, description, photos	3	f	2000	3	60	2026-01-09 09:49:11.142491+00
5	delete	Delete product	Remove listing from Vinted	4	f	2000	3	30	2026-01-09 09:49:11.142491+00
6	sync	Sync products	Synchronize all products with Vinted	4	t	1500	3	300	2026-01-09 09:49:11.142491+00
7	link_product	Link Product	Link VintedProduct to Product and download images	3	f	500	3	120	2026-01-09 10:26:16.75036+00
8	sync_orders_ebay	Synchroniser les commandes eBay	Synchronise les commandes depuis eBay Fulfillment API vers la base de données locale	2	f	2000	3	300	2026-01-09 10:26:16.75036+00
\.


--
-- Data for Name: categories; Type: TABLE DATA; Schema: vinted; Owner: stoflow_user
--

COPY vinted.categories (id, code, title, parent_id, path, is_leaf, gender, is_active) FROM stdin;
84	\N	Maillots de bain	\N	\N	t	men	t
176	\N	Autres robes	\N	\N	t	women	t
178	\N	Mini	\N	\N	t	women	t
179	\N	Robes en jean	\N	\N	t	women	t
184	\N	Pantalons en cuir	\N	\N	t	women	t
185	\N	Pantalons skinny	\N	\N	t	women	t
187	\N	Pantalons ajustés	\N	\N	t	women	t
189	\N	Autres pantalons	\N	\N	t	women	t
190	\N	Pulls col V	\N	\N	t	women	t
191	\N	Pulls col roulé	\N	\N	t	women	t
192	\N	Sweats longs	\N	\N	t	women	t
194	\N	Cardigans	\N	\N	t	women	t
195	\N	Boléros	\N	\N	t	women	t
196	\N	Sweats & sweats à capuche	\N	\N	t	women	t
197	\N	Autres pull-overs & sweat-shirts	\N	\N	t	women	t
198	\N	Minijupes	\N	\N	t	women	t
199	\N	Jupes midi	\N	\N	t	women	t
200	\N	Jupes longues	\N	\N	t	women	t
203	\N	Shorts longueur genou	\N	\N	t	women	t
204	\N	Pantacourts	\N	\N	t	women	t
205	\N	Autres shorts	\N	\N	t	women	t
218	\N	Une pièce	\N	\N	t	women	t
219	\N	Deux pièces	\N	\N	t	women	t
221	\N	T-shirts	\N	\N	t	women	t
222	\N	Chemises	\N	\N	t	women	t
223	\N	Blouses manches courtes	\N	\N	t	women	t
224	\N	Blouses manches longues	\N	\N	t	women	t
225	\N	Blouses ¾	\N	\N	t	women	t
227	\N	Tuniques	\N	\N	t	women	t
228	\N	Autres hauts	\N	\N	t	women	t
259	\N	Pantalons skinny	\N	\N	t	men	t
260	\N	Pantalons à jambes larges	\N	\N	t	men	t
261	\N	Pantalons de costume	\N	\N	t	men	t
263	\N	Autres pantalons	\N	\N	t	men	t
264	\N	Sweats à col V	\N	\N	t	men	t
265	\N	Pulls à col roulé	\N	\N	t	men	t
266	\N	Cardigans	\N	\N	t	men	t
267	\N	Pulls et pulls à capuche	\N	\N	t	men	t
268	\N	Autres	\N	\N	t	men	t
271	\N	Pantacourts	\N	\N	t	men	t
272	\N	Autres shorts	\N	\N	t	men	t
525	\N	Leggings	\N	\N	t	women	t
526	\N	Sarouels	\N	\N	t	women	t
529	\N	Pulls d'hiver	\N	\N	t	women	t
532	\N	Blazers	\N	\N	t	women	t
534	\N	Débardeurs	\N	\N	t	women	t
538	\N	Short en jean	\N	\N	t	women	t
560	\N	T-shirts sans manches	\N	\N	t	men	t
571	\N	Vêtements d'extérieur	\N	\N	t	women	t
572	\N	Survêtements	\N	\N	t	women	t
573	\N	Pantalons & leggings	\N	\N	t	women	t
576	\N	Hauts & t-shirts	\N	\N	t	women	t
577	\N	Sweats et sweats à capuche	\N	\N	t	women	t
578	\N	Shorts	\N	\N	t	women	t
581	\N	Vêtements d'extérieur	\N	\N	t	men	t
582	\N	Survêtements	\N	\N	t	men	t
583	\N	Pantalons	\N	\N	t	men	t
584	\N	Hauts et t-shirts	\N	\N	t	men	t
585	\N	Pulls & sweats	\N	\N	t	men	t
586	\N	Shorts	\N	\N	t	men	t
1041	\N	Tops courts	\N	\N	t	women	t
1042	\N	Tops épaules dénudées	\N	\N	t	women	t
1043	\N	Blouses	\N	\N	t	women	t
1044	\N	Tops dos nu	\N	\N	t	women	t
1045	\N	Cols roulés	\N	\N	t	women	t
1055	\N	Robes longues	\N	\N	t	women	t
1056	\N	Midi	\N	\N	t	women	t
1057	\N	Robes chics	\N	\N	t	women	t
1058	\N	Petites robes noires	\N	\N	t	women	t
1059	\N	Robes casual	\N	\N	t	women	t
1060	\N	Robes dos nu	\N	\N	t	women	t
1061	\N	Robes sans bretelles	\N	\N	t	women	t
1065	\N	Robes d'été	\N	\N	t	women	t
1066	\N	Autres sweats	\N	\N	t	women	t
1067	\N	Kimonos	\N	\N	t	women	t
1070	\N	Pantalons courts & chinos	\N	\N	t	women	t
1071	\N	Pantalons à jambes larges	\N	\N	t	women	t
1076	\N	Cabans	\N	\N	t	women	t
1078	\N	Blousons aviateur	\N	\N	t	women	t
1079	\N	Vestes en jean	\N	\N	t	women	t
1080	\N	Imperméables	\N	\N	t	women	t
1086	\N	Vestes polaires	\N	\N	t	women	t
1087	\N	Parkas	\N	\N	t	women	t
1090	\N	Manteaux en fausse fourrure	\N	\N	t	women	t
1099	\N	Shorts taille haute	\N	\N	t	women	t
1100	\N	Shorts en cuir	\N	\N	t	women	t
1103	\N	Shorts cargo	\N	\N	t	women	t
1125	\N	Ensembles tailleur/pantalon	\N	\N	t	women	t
1126	\N	Jupes et robes tailleurs	\N	\N	t	women	t
1128	\N	Tailleurs pièces séparées	\N	\N	t	women	t
1131	\N	Combinaisons	\N	\N	t	women	t
1132	\N	Combi Shorts	\N	\N	t	women	t
1134	\N	Autres combinaisons & combishorts	\N	\N	t	women	t
1201	\N	Shorts et pantacourts	\N	\N	t	boys	t
1204	\N	Vêtements de sport	\N	\N	t	boys	t
1223	\N	Blousons aviateur	\N	\N	t	men	t
1224	\N	Vestes en jean	\N	\N	t	men	t
1225	\N	Duffle-coats	\N	\N	t	men	t
1226	\N	Vestes Harrington	\N	\N	t	men	t
1227	\N	Parkas	\N	\N	t	men	t
1230	\N	Trenchs	\N	\N	t	men	t
1248	\N	Jupes	\N	\N	t	girls	t
1250	\N	Shorts et pantacourts	\N	\N	t	girls	t
1253	\N	Vêtements de sport	\N	\N	t	girls	t
1439	\N	Brassières	\N	\N	t	women	t
1518	\N	Vestes sans manches	\N	\N	t	girls	t
1535	\N	T-shirts	\N	\N	t	girls	t
1536	\N	Polos	\N	\N	t	girls	t
1537	\N	Chemises	\N	\N	t	girls	t
1538	\N	Chemises manches courtes	\N	\N	t	girls	t
1539	\N	Chemises manches longues	\N	\N	t	girls	t
1540	\N	Chemises sans manches	\N	\N	t	girls	t
1541	\N	Tuniques	\N	\N	t	girls	t
1542	\N	Pulls	\N	\N	t	girls	t
1543	\N	Pulls col V	\N	\N	t	girls	t
1544	\N	Pulls à col roulé	\N	\N	t	girls	t
1548	\N	Gilets zippés	\N	\N	t	girls	t
1550	\N	Pulls à capuche & sweatshirts	\N	\N	t	girls	t
1551	\N	Gilets	\N	\N	t	girls	t
1553	\N	Robes longues	\N	\N	t	girls	t
1554	\N	Robes courtes	\N	\N	t	girls	t
1559	\N	Jeans	\N	\N	t	girls	t
1560	\N	Jeans slim	\N	\N	t	girls	t
1562	\N	Pantalons pattes d'éléphant	\N	\N	t	girls	t
1565	\N	Leggings	\N	\N	t	girls	t
1568	\N	Salopettes	\N	\N	t	girls	t
1590	\N	Maillot de bain 1 pièce	\N	\N	t	girls	t
1592	\N	Maillot de bain 2 pièces	\N	\N	t	girls	t
1646	\N	Vestes sans manches	\N	\N	t	boys	t
1662	\N	T-shirts	\N	\N	t	boys	t
1663	\N	Polos	\N	\N	t	boys	t
1664	\N	Chemises	\N	\N	t	boys	t
1665	\N	Chemises manches courtes	\N	\N	t	boys	t
1666	\N	Chemises manches longues	\N	\N	t	boys	t
1667	\N	Chemises sans manches	\N	\N	t	boys	t
1668	\N	Pulls	\N	\N	t	boys	t
1669	\N	Pulls col V	\N	\N	t	boys	t
1670	\N	Pulls à col roulé	\N	\N	t	boys	t
1671	\N	Gilets zippés	\N	\N	t	boys	t
1672	\N	Pulls à capuche et sweatshirts	\N	\N	t	boys	t
1673	\N	Gilets	\N	\N	t	boys	t
1696	\N	Jeans	\N	\N	t	boys	t
1697	\N	Jeans slim	\N	\N	t	boys	t
1698	\N	Pantalons pattes d'éléphant	\N	\N	t	boys	t
1701	\N	Leggings	\N	\N	t	boys	t
1702	\N	Salopettes	\N	\N	t	boys	t
1750	\N	Maillots de bain	\N	\N	t	boys	t
1773	\N	Capes et ponchos	\N	\N	t	women	t
1775	\N	Fêtes et cocktails	\N	\N	t	women	t
1778	\N	Robes de soirée	\N	\N	t	women	t
1779	\N	Robes d'hiver	\N	\N	t	women	t
1786	\N	Blazers	\N	\N	t	men	t
1787	\N	Pantalons de costume	\N	\N	t	men	t
1788	\N	Gilets de costume	\N	\N	t	men	t
1789	\N	Ensembles costume	\N	\N	t	men	t
1801	\N	Chemises à carreaux	\N	\N	t	men	t
1802	\N	Chemises en jean	\N	\N	t	men	t
1803	\N	Chemises unies	\N	\N	t	men	t
1804	\N	Chemises à motifs	\N	\N	t	men	t
1805	\N	Chemises à rayures	\N	\N	t	men	t
1806	\N	T-shirts unis	\N	\N	t	men	t
1807	\N	T-shirts imprimés	\N	\N	t	men	t
1808	\N	T-shirts à rayures	\N	\N	t	men	t
1809	\N	Polos	\N	\N	t	men	t
1810	\N	T-shirts à manches longues	\N	\N	t	men	t
1811	\N	Sweats	\N	\N	t	men	t
1812	\N	Pulls à capuche avec zip	\N	\N	t	men	t
1813	\N	Pulls ras de cou	\N	\N	t	men	t
1814	\N	Sweats longs	\N	\N	t	men	t
1815	\N	Pulls d'hiver	\N	\N	t	men	t
1816	\N	Jeans troués	\N	\N	t	men	t
1817	\N	Jeans skinny	\N	\N	t	men	t
1818	\N	Jeans slim	\N	\N	t	men	t
1819	\N	Jeans coupe droite	\N	\N	t	men	t
1820	\N	Chinos	\N	\N	t	men	t
1821	\N	Jogging	\N	\N	t	men	t
1822	\N	Shorts cargo	\N	\N	t	men	t
1823	\N	Shorts chino	\N	\N	t	men	t
1824	\N	Shorts en jean	\N	\N	t	men	t
1825	\N	Vestes	\N	\N	t	men	t
1834	\N	Trenchs	\N	\N	t	women	t
1835	\N	Bodies	\N	\N	t	women	t
1837	\N	Tops peplum	\N	\N	t	women	t
1838	\N	Shorts taille basse	\N	\N	t	women	t
1839	\N	Jeans boyfriend	\N	\N	t	women	t
1840	\N	Jeans courts	\N	\N	t	women	t
1841	\N	Jeans évasés	\N	\N	t	women	t
1842	\N	Jeans taille haute	\N	\N	t	women	t
1843	\N	Jeans troués	\N	\N	t	women	t
1844	\N	Jeans skinny	\N	\N	t	women	t
1845	\N	Jeans droits	\N	\N	t	women	t
1846	\N	Pantalons droits	\N	\N	t	women	t
1858	\N	Vestes polaires	\N	\N	t	men	t
1859	\N	Imperméables	\N	\N	t	men	t
1861	\N	Cabans	\N	\N	t	men	t
1865	\N	Autres chemises	\N	\N	t	men	t
1868	\N	Autres T-shirts	\N	\N	t	men	t
1870	\N	Autres	\N	\N	t	boys	t
1874	\N	Vestes	\N	\N	t	women	t
1877	\N	Autre	\N	\N	t	girls	t
1878	\N	Autre	\N	\N	t	girls	t
1880	\N	Autres	\N	\N	t	girls	t
1886	\N	Autre	\N	\N	t	boys	t
1887	\N	Autre	\N	\N	t	boys	t
2079	\N	Sarouels	\N	\N	t	girls	t
2082	\N	Sarouels	\N	\N	t	boys	t
2524	\N	Vestes sans manches	\N	\N	t	women	t
2525	\N	Duffle-coats	\N	\N	t	women	t
2526	\N	Pardessus et manteaux longs	\N	\N	t	women	t
2527	\N	Perfectos et blousons de moto	\N	\N	t	women	t
2528	\N	Vestes militaires et utilitaires	\N	\N	t	women	t
2529	\N	Vestes chemises	\N	\N	t	women	t
2530	\N	Vestes de ski et snowboard	\N	\N	t	women	t
2531	\N	Blousons teddy	\N	\N	t	women	t
2532	\N	Vestes coupe-vent	\N	\N	t	women	t
2533	\N	Pardessus et manteaux longs	\N	\N	t	men	t
2534	\N	Perfectos et blousons de moto	\N	\N	t	men	t
2535	\N	Vestes militaires et utilitaires	\N	\N	t	men	t
2536	\N	Doudounes	\N	\N	t	men	t
2537	\N	Vestes matelassées	\N	\N	t	men	t
2538	\N	Vestes chemises	\N	\N	t	men	t
2539	\N	Vestes de ski et snowboard	\N	\N	t	men	t
2540	\N	Duffle-coats	\N	\N	t	girls	t
2541	\N	Parkas	\N	\N	t	girls	t
2542	\N	Cabans	\N	\N	t	girls	t
2543	\N	Trenchs	\N	\N	t	girls	t
2544	\N	Blazers	\N	\N	t	girls	t
2545	\N	Blousons aviateur	\N	\N	t	girls	t
2546	\N	Vestes en jean	\N	\N	t	girls	t
2547	\N	Vestes polaires	\N	\N	t	girls	t
2548	\N	Doudounes	\N	\N	t	girls	t
2549	\N	Vestes coupe-vent	\N	\N	t	girls	t
2550	\N	Blousons teddy	\N	\N	t	men	t
2551	\N	Vestes coupe-vent	\N	\N	t	men	t
2552	\N	Ponchos	\N	\N	t	men	t
2553	\N	Vestes sans manches	\N	\N	t	men	t
2556	\N	Ponchos	\N	\N	t	girls	t
2558	\N	Imperméables	\N	\N	t	girls	t
2561	\N	Duffle-coats	\N	\N	t	boys	t
2562	\N	Parkas	\N	\N	t	boys	t
2563	\N	Cabans	\N	\N	t	boys	t
2564	\N	Trenchs	\N	\N	t	boys	t
2571	\N	Blazers	\N	\N	t	boys	t
2573	\N	Blousons aviateur	\N	\N	t	boys	t
2574	\N	Vestes en jean	\N	\N	t	boys	t
2575	\N	Vestes polaires	\N	\N	t	boys	t
2576	\N	Doudounes	\N	\N	t	boys	t
2577	\N	Vestes coupe-vent	\N	\N	t	boys	t
2604	\N	Ponchos	\N	\N	t	boys	t
2606	\N	Imperméables	\N	\N	t	boys	t
2614	\N	Doudounes	\N	\N	t	women	t
2596	\N	Vestes matelassées	\N	\N	t	women	t
2927	\N	Jupes longueur genou	\N	\N	t	women	t
2928	\N	Jupes asymétriques	\N	\N	t	women	t
2929	\N	Jupes-shorts	\N	\N	t	women	t
3267	\N	Maillots	\N	\N	t	men	t
3268	\N	Maillots	\N	\N	t	women	t
14	\N	Vestes	\N	\N	t	women	t
\.


--
-- Data for Name: deletions; Type: TABLE DATA; Schema: vinted; Owner: stoflow_user
--

COPY vinted.deletions (id, id_vinted, id_site, price, date_published, date_deleted, view_count, favourite_count, conversations, days_active) FROM stdin;
\.


--
-- Data for Name: mapping; Type: TABLE DATA; Schema: vinted; Owner: stoflow_user
--

COPY vinted.mapping (id, vinted_id, vinted_gender, my_category, my_gender, my_fit, my_length, my_rise, my_material, my_pattern, my_neckline, my_sleeve_length, is_default) FROM stdin;
14	1696	boys	jeans	Boys	\N	\N	\N	\N	\N	\N	\N	t
38	1662	boys	t-shirt	Boys	\N	\N	\N	\N	\N	\N	\N	t
41	1662	boys	tank-top	Boys	\N	\N	\N	\N	\N	\N	\N	t
54	1664	boys	shirt	Boys	\N	\N	\N	\N	\N	\N	\N	t
89	1668	boys	sweater	Boys	\N	\N	\N	\N	\N	\N	\N	t
92	1887	boys	sweater	Boys	\N	\N	\N	\N	\N	\N	\N	f
100	1673	boys	cardigan	Boys	\N	\N	\N	\N	\N	\N	\N	t
108	1672	boys	sweatshirt	Boys	\N	\N	\N	\N	\N	\N	\N	t
114	1672	boys	hoodie	Boys	\N	\N	\N	\N	\N	\N	\N	t
122	2575	boys	half-zip	Boys	\N	\N	\N	\N	\N	\N	\N	t
128	1663	boys	polo	Boys	\N	\N	\N	\N	\N	\N	\N	t
144	2082	boys	pants	Boys	\N	\N	\N	\N	\N	\N	\N	f
145	1870	boys	pants	Boys	\N	\N	\N	\N	\N	\N	\N	f
149	1870	boys	cargo-pants	Boys	\N	\N	\N	\N	\N	\N	\N	t
250	1646	boys	vest	Boys	\N	\N	\N	\N	\N	\N	\N	t
153	1870	boys	chinos	Boys	\N	\N	\N	\N	\N	\N	\N	t
157	1870	boys	joggers	Boys	\N	\N	\N	\N	\N	\N	\N	t
161	1870	boys	dress-pants	Boys	\N	\N	\N	\N	\N	\N	\N	t
174	1201	boys	shorts	Boys	\N	\N	\N	\N	\N	\N	\N	t
178	1201	boys	bermuda	Boys	\N	\N	\N	\N	\N	\N	\N	t
187	1701	boys	leggings	Boys	\N	\N	\N	\N	\N	\N	\N	t
211	2573	boys	bomber	Boys	\N	\N	\N	\N	\N	\N	\N	t
215	2576	boys	puffer	Boys	\N	\N	\N	\N	\N	\N	\N	t
225	2563	boys	coat	Boys	\N	\N	\N	\N	\N	\N	\N	t
226	2561	boys	coat	Boys	\N	\N	\N	\N	\N	\N	\N	f
230	2564	boys	trench	Boys	\N	\N	\N	\N	\N	\N	\N	t
234	2562	boys	parka	Boys	\N	\N	\N	\N	\N	\N	\N	t
238	2606	boys	raincoat	Boys	\N	\N	\N	\N	\N	\N	\N	t
242	2577	boys	windbreaker	Boys	\N	\N	\N	\N	\N	\N	\N	t
246	2571	boys	blazer	Boys	\N	\N	\N	\N	\N	\N	\N	t
256	2604	boys	poncho	Boys	\N	\N	\N	\N	\N	\N	\N	t
264	1702	boys	overalls	Boys	\N	\N	\N	\N	\N	\N	\N	t
285	1204	boys	sports-top	Boys	\N	\N	\N	\N	\N	\N	\N	t
289	1204	boys	sports-shorts	Boys	\N	\N	\N	\N	\N	\N	\N	t
295	1204	boys	sports-jersey	Boys	\N	\N	\N	\N	\N	\N	\N	t
307	1886	boys	t-shirt	Boys	\N	\N	\N	\N	\N	\N	\N	f
203	2574	boys	jacket	Boys	\N	\N	\N	\N	\N	\N	\N	t
15	1697	boys	jeans	Boys	\N	\N	\N	\N	\N	\N	\N	f
143	1698	boys	pants	Boys	Flare	\N	\N	\N	\N	\N	\N	t
12	1559	girls	jeans	Girls	\N	\N	\N	\N	\N	\N	\N	t
37	1535	girls	t-shirt	Girls	\N	\N	\N	\N	\N	\N	\N	t
42	1535	girls	tank-top	Girls	\N	\N	\N	\N	\N	\N	\N	t
50	1537	girls	shirt	Girls	\N	\N	\N	\N	\N	\N	\N	t
62	1537	girls	blouse	Girls	\N	\N	\N	\N	\N	\N	\N	t
68	1541	girls	top	Girls	\N	\N	\N	\N	\N	\N	\N	t
69	1878	girls	top	Girls	\N	\N	\N	\N	\N	\N	\N	f
71	1535	girls	crop-top	Girls	\N	\N	\N	\N	\N	\N	\N	t
85	1542	girls	sweater	Girls	\N	\N	\N	\N	\N	\N	\N	t
88	1877	girls	sweater	Girls	\N	\N	\N	\N	\N	\N	\N	f
98	1551	girls	cardigan	Girls	\N	\N	\N	\N	\N	\N	\N	t
99	1548	girls	cardigan	Girls	\N	\N	\N	\N	\N	\N	\N	f
107	1550	girls	sweatshirt	Girls	\N	\N	\N	\N	\N	\N	\N	t
113	1550	girls	hoodie	Girls	\N	\N	\N	\N	\N	\N	\N	t
121	2547	girls	half-zip	Girls	\N	\N	\N	\N	\N	\N	\N	t
127	1536	girls	polo	Girls	\N	\N	\N	\N	\N	\N	\N	t
141	2079	girls	pants	Girls	\N	\N	\N	\N	\N	\N	\N	f
142	1880	girls	pants	Girls	\N	\N	\N	\N	\N	\N	\N	f
148	1880	girls	cargo-pants	Girls	\N	\N	\N	\N	\N	\N	\N	t
152	1880	girls	chinos	Girls	\N	\N	\N	\N	\N	\N	\N	t
156	1880	girls	joggers	Girls	\N	\N	\N	\N	\N	\N	\N	t
160	1880	girls	dress-pants	Girls	\N	\N	\N	\N	\N	\N	\N	t
173	1250	girls	shorts	Girls	\N	\N	\N	\N	\N	\N	\N	t
177	1250	girls	bermuda	Girls	\N	\N	\N	\N	\N	\N	\N	t
184	1248	girls	skirt	Girls	\N	\N	\N	\N	\N	\N	\N	t
186	1565	girls	leggings	Girls	\N	\N	\N	\N	\N	\N	\N	t
189	1250	girls	culottes	Girls	\N	\N	\N	\N	\N	\N	\N	t
210	2545	girls	bomber	Girls	\N	\N	\N	\N	\N	\N	\N	t
214	2548	girls	puffer	Girls	\N	\N	\N	\N	\N	\N	\N	t
223	2542	girls	coat	Girls	\N	\N	\N	\N	\N	\N	\N	t
224	2540	girls	coat	Girls	\N	\N	\N	\N	\N	\N	\N	f
229	2543	girls	trench	Girls	\N	\N	\N	\N	\N	\N	\N	t
233	2541	girls	parka	Girls	\N	\N	\N	\N	\N	\N	\N	t
237	2558	girls	raincoat	Girls	\N	\N	\N	\N	\N	\N	\N	t
241	2549	girls	windbreaker	Girls	\N	\N	\N	\N	\N	\N	\N	t
245	2544	girls	blazer	Girls	\N	\N	\N	\N	\N	\N	\N	t
249	1518	girls	vest	Girls	\N	\N	\N	\N	\N	\N	\N	t
252	1518	girls	cape	Girls	\N	\N	\N	\N	\N	\N	\N	t
255	2556	girls	poncho	Girls	\N	\N	\N	\N	\N	\N	\N	t
263	1568	girls	overalls	Girls	\N	\N	\N	\N	\N	\N	\N	t
268	1568	girls	romper	Girls	\N	\N	\N	\N	\N	\N	\N	t
281	1253	girls	sports-bra	Girls	\N	\N	\N	\N	\N	\N	\N	t
284	1253	girls	sports-top	Girls	\N	\N	\N	\N	\N	\N	\N	t
288	1253	girls	sports-shorts	Girls	\N	\N	\N	\N	\N	\N	\N	t
291	1565	girls	sports-leggings	Girls	\N	\N	\N	\N	\N	\N	\N	t
294	1253	girls	sports-jersey	Girls	\N	\N	\N	\N	\N	\N	\N	t
305	1592	girls	bikini	Girls	\N	\N	\N	\N	\N	\N	\N	t
202	2546	girls	jacket	Girls	\N	\N	\N	\N	\N	\N	\N	t
13	1560	girls	jeans	Girls	\N	\N	\N	\N	\N	\N	\N	f
140	1562	girls	pants	Girls	Flare	\N	\N	\N	\N	\N	\N	t
11	1816	men	jeans	Men	\N	\N	\N	\N	\N	\N	\N	f
40	560	men	tank-top	Men	\N	\N	\N	\N	\N	\N	\N	t
49	1865	men	shirt	Men	\N	\N	\N	\N	\N	\N	\N	f
84	1815	men	sweater	Men	\N	\N	\N	\N	\N	\N	\N	f
96	266	men	cardigan	Men	\N	\N	\N	\N	\N	\N	\N	t
97	1825	men	cardigan	Men	\N	\N	\N	\N	\N	\N	\N	f
104	1811	men	sweatshirt	Men	\N	\N	\N	\N	\N	\N	\N	t
105	1814	men	sweatshirt	Men	\N	\N	\N	\N	\N	\N	\N	f
106	268	men	sweatshirt	Men	\N	\N	\N	\N	\N	\N	\N	f
110	267	men	hoodie	Men	\N	\N	\N	\N	\N	\N	\N	t
111	1812	men	hoodie	Men	\N	\N	\N	\N	\N	\N	\N	f
112	585	men	hoodie	Men	\N	\N	\N	\N	\N	\N	\N	f
120	1858	men	half-zip	Men	\N	\N	\N	\N	\N	\N	\N	t
124	2538	men	overshirt	Men	\N	\N	\N	\N	\N	\N	\N	t
126	1809	men	polo	Men	\N	\N	\N	\N	\N	\N	\N	t
138	263	men	pants	Men	\N	\N	\N	\N	\N	\N	\N	f
139	583	men	pants	Men	\N	\N	\N	\N	\N	\N	\N	f
147	263	men	cargo-pants	Men	\N	\N	\N	\N	\N	\N	\N	t
151	1820	men	chinos	Men	\N	\N	\N	\N	\N	\N	\N	t
155	1821	men	joggers	Men	\N	\N	\N	\N	\N	\N	\N	t
159	261	men	dress-pants	Men	\N	\N	\N	\N	\N	\N	\N	t
169	1822	men	shorts	Men	\N	\N	\N	\N	\N	\N	\N	t
170	1823	men	shorts	Men	\N	\N	\N	\N	\N	\N	\N	f
172	272	men	shorts	Men	\N	\N	\N	\N	\N	\N	\N	f
176	271	men	bermuda	Men	\N	\N	\N	\N	\N	\N	\N	t
197	2535	men	jacket	Men	\N	\N	\N	\N	\N	\N	\N	f
198	2537	men	jacket	Men	\N	\N	\N	\N	\N	\N	\N	f
199	1226	men	jacket	Men	\N	\N	\N	\N	\N	\N	\N	f
200	2539	men	jacket	Men	\N	\N	\N	\N	\N	\N	\N	f
201	581	men	jacket	Men	\N	\N	\N	\N	\N	\N	\N	f
207	1223	men	bomber	Men	\N	\N	\N	\N	\N	\N	\N	t
208	2550	men	bomber	Men	\N	\N	\N	\N	\N	\N	\N	f
209	2534	men	bomber	Men	\N	\N	\N	\N	\N	\N	\N	f
213	2536	men	puffer	Men	\N	\N	\N	\N	\N	\N	\N	t
220	1861	men	coat	Men	\N	\N	\N	\N	\N	\N	\N	t
221	1225	men	coat	Men	\N	\N	\N	\N	\N	\N	\N	f
222	2533	men	coat	Men	\N	\N	\N	\N	\N	\N	\N	f
228	1230	men	trench	Men	\N	\N	\N	\N	\N	\N	\N	t
232	1227	men	parka	Men	\N	\N	\N	\N	\N	\N	\N	t
236	1859	men	raincoat	Men	\N	\N	\N	\N	\N	\N	\N	t
240	2551	men	windbreaker	Men	\N	\N	\N	\N	\N	\N	\N	t
244	1786	men	blazer	Men	\N	\N	\N	\N	\N	\N	\N	t
248	2553	men	vest	Men	\N	\N	\N	\N	\N	\N	\N	t
254	2552	men	poncho	Men	\N	\N	\N	\N	\N	\N	\N	t
266	268	men	overalls	Men	\N	\N	\N	\N	\N	\N	\N	t
269	1789	men	suit	Men	\N	\N	\N	\N	\N	\N	\N	t
270	1787	men	suit	Men	\N	\N	\N	\N	\N	\N	\N	f
275	1789	men	tuxedo	Men	\N	\N	\N	\N	\N	\N	\N	t
283	584	men	sports-top	Men	\N	\N	\N	\N	\N	\N	\N	t
287	586	men	sports-shorts	Men	\N	\N	\N	\N	\N	\N	\N	t
293	3267	men	sports-jersey	Men	\N	\N	\N	\N	\N	\N	\N	t
306	1868	men	t-shirt	Men	\N	\N	\N	\N	\N	\N	\N	f
46	1802	men	shirt	Men	\N	\N	\N	\N	\N	\N	\N	f
171	1824	men	shorts	Men	\N	\N	\N	\N	\N	\N	\N	f
196	1224	men	jacket	Men	\N	\N	\N	\N	\N	\N	\N	t
137	260	men	pants	Men	\N	\N	\N	\N	\N	\N	\N	f
10	1818	men	jeans	Men	\N	\N	\N	\N	\N	\N	\N	f
34	1807	men	t-shirt	Men	\N	\N	\N	\N	\N	\N	\N	f
48	1804	men	shirt	Men	\N	\N	\N	\N	\N	\N	\N	f
9	1817	men	jeans	Men	Skinny	\N	\N	\N	\N	\N	\N	f
136	259	men	pants	Men	Skinny	\N	\N	\N	\N	\N	\N	t
8	1819	men	jeans	Men	Straight	\N	\N	\N	\N	\N	\N	t
7	1843	women	jeans	Women	\N	\N	\N	\N	\N	\N	\N	f
16	1059	women	dress	Women	\N	\N	\N	\N	\N	\N	\N	t
21	1775	women	dress	Women	\N	\N	\N	\N	\N	\N	\N	f
22	1778	women	dress	Women	\N	\N	\N	\N	\N	\N	\N	f
23	1060	women	dress	Women	\N	\N	\N	\N	\N	\N	\N	f
24	1065	women	dress	Women	\N	\N	\N	\N	\N	\N	\N	f
25	1779	women	dress	Women	\N	\N	\N	\N	\N	\N	\N	f
26	1057	women	dress	Women	\N	\N	\N	\N	\N	\N	\N	f
27	1061	women	dress	Women	\N	\N	\N	\N	\N	\N	\N	f
28	1058	women	dress	Women	\N	\N	\N	\N	\N	\N	\N	f
29	176	women	dress	Women	\N	\N	\N	\N	\N	\N	\N	f
32	221	women	t-shirt	Women	\N	\N	\N	\N	\N	\N	\N	t
39	534	women	tank-top	Women	\N	\N	\N	\N	\N	\N	\N	t
43	222	women	shirt	Women	\N	\N	\N	\N	\N	\N	\N	t
58	1043	women	blouse	Women	\N	\N	\N	\N	\N	\N	\N	t
61	225	women	blouse	Women	\N	\N	\N	\N	\N	\N	3/4 sleeve	f
63	1837	women	top	Women	\N	\N	\N	\N	\N	\N	\N	t
66	227	women	top	Women	\N	\N	\N	\N	\N	\N	\N	f
67	228	women	top	Women	\N	\N	\N	\N	\N	\N	\N	f
70	1041	women	crop-top	Women	\N	\N	\N	\N	\N	\N	\N	t
73	1041	women	bustier	Women	\N	\N	\N	\N	\N	\N	\N	t
74	534	women	camisole	Women	\N	\N	\N	\N	\N	\N	\N	t
75	1041	women	corset	Women	\N	\N	\N	\N	\N	\N	\N	t
76	529	women	sweater	Women	\N	\N	\N	\N	\N	\N	\N	t
80	1066	women	sweater	Women	\N	\N	\N	\N	\N	\N	\N	f
93	194	women	cardigan	Women	\N	\N	\N	\N	\N	\N	\N	t
94	195	women	cardigan	Women	\N	\N	\N	\N	\N	\N	\N	f
95	1874	women	cardigan	Women	\N	\N	\N	\N	\N	\N	\N	f
101	196	women	sweatshirt	Women	\N	\N	\N	\N	\N	\N	\N	t
102	192	women	sweatshirt	Women	\N	\N	\N	\N	\N	\N	\N	f
103	197	women	sweatshirt	Women	\N	\N	\N	\N	\N	\N	\N	f
109	577	women	hoodie	Women	\N	\N	\N	\N	\N	\N	\N	t
119	1086	women	half-zip	Women	\N	\N	\N	\N	\N	\N	\N	t
123	2529	women	overshirt	Women	\N	\N	\N	\N	\N	\N	\N	t
125	221	women	polo	Women	\N	\N	\N	\N	\N	\N	\N	t
134	189	women	pants	Women	\N	\N	\N	\N	\N	\N	\N	f
135	526	women	pants	Women	\N	\N	\N	\N	\N	\N	\N	f
146	1846	women	cargo-pants	Women	\N	\N	\N	\N	\N	\N	\N	t
150	1070	women	chinos	Women	\N	\N	\N	\N	\N	\N	\N	t
154	525	women	joggers	Women	\N	\N	\N	\N	\N	\N	\N	t
158	189	women	dress-pants	Women	\N	\N	\N	\N	\N	\N	\N	t
162	1103	women	shorts	Women	\N	\N	\N	\N	\N	\N	\N	t
167	204	women	shorts	Women	\N	\N	\N	\N	\N	\N	\N	f
168	205	women	shorts	Women	\N	\N	\N	\N	\N	\N	\N	f
175	203	women	bermuda	Women	\N	\N	\N	\N	\N	\N	\N	t
183	2928	women	skirt	Women	\N	\N	\N	\N	\N	\N	\N	f
185	525	women	leggings	Women	\N	\N	\N	\N	\N	\N	\N	t
188	2929	women	culottes	Women	\N	\N	\N	\N	\N	\N	\N	t
191	2528	women	jacket	Women	\N	\N	\N	\N	\N	\N	\N	f
192	2596	women	jacket	Women	\N	\N	\N	\N	\N	\N	\N	f
193	2530	women	jacket	Women	\N	\N	\N	\N	\N	\N	\N	f
194	571	women	jacket	Women	\N	\N	\N	\N	\N	\N	\N	f
195	14	women	jacket	Women	\N	\N	\N	\N	\N	\N	\N	f
204	1078	women	bomber	Women	\N	\N	\N	\N	\N	\N	\N	t
205	2531	women	bomber	Women	\N	\N	\N	\N	\N	\N	\N	f
206	2527	women	bomber	Women	\N	\N	\N	\N	\N	\N	\N	f
212	2614	women	puffer	Women	\N	\N	\N	\N	\N	\N	\N	t
216	1076	women	coat	Women	\N	\N	\N	\N	\N	\N	\N	t
217	2525	women	coat	Women	\N	\N	\N	\N	\N	\N	\N	f
218	1090	women	coat	Women	\N	\N	\N	\N	\N	\N	\N	f
219	2526	women	coat	Women	\N	\N	\N	\N	\N	\N	\N	f
227	1834	women	trench	Women	\N	\N	\N	\N	\N	\N	\N	t
231	1087	women	parka	Women	\N	\N	\N	\N	\N	\N	\N	t
235	1080	women	raincoat	Women	\N	\N	\N	\N	\N	\N	\N	t
239	2532	women	windbreaker	Women	\N	\N	\N	\N	\N	\N	\N	t
243	532	women	blazer	Women	\N	\N	\N	\N	\N	\N	\N	t
247	2524	women	vest	Women	\N	\N	\N	\N	\N	\N	\N	t
251	1773	women	cape	Women	\N	\N	\N	\N	\N	\N	\N	t
253	1067	women	poncho	Women	\N	\N	\N	\N	\N	\N	\N	t
257	1067	women	kimono	Women	\N	\N	\N	\N	\N	\N	\N	t
265	1134	women	overalls	Women	\N	\N	\N	\N	\N	\N	\N	t
267	1132	women	romper	Women	\N	\N	\N	\N	\N	\N	\N	t
271	1125	women	suit	Women	\N	\N	\N	\N	\N	\N	\N	t
280	1439	women	sports-bra	Women	\N	\N	\N	\N	\N	\N	\N	t
282	576	women	sports-top	Women	\N	\N	\N	\N	\N	\N	\N	t
286	578	women	sports-shorts	Women	\N	\N	\N	\N	\N	\N	\N	t
290	573	women	sports-leggings	Women	\N	\N	\N	\N	\N	\N	\N	t
292	3268	women	sports-jersey	Women	\N	\N	\N	\N	\N	\N	\N	t
304	219	women	bikini	Women	\N	\N	\N	\N	\N	\N	\N	t
20	179	women	dress	Women	\N	\N	\N	\N	\N	\N	\N	f
165	538	women	shorts	Women	\N	\N	\N	\N	\N	\N	\N	f
190	1079	women	jacket	Women	\N	\N	\N	\N	\N	\N	\N	t
133	184	women	pants	Women	\N	\N	\N	\N	\N	\N	\N	f
166	1100	women	shorts	Women	\N	\N	\N	\N	\N	\N	\N	f
132	1071	women	pants	Women	\N	\N	\N	\N	\N	\N	\N	f
4	1839	women	jeans	Women	\N	\N	\N	\N	\N	\N	\N	f
131	187	women	pants	Women	\N	\N	\N	\N	\N	\N	\N	f
3	1841	women	jeans	Women	Flare	\N	\N	\N	\N	\N	\N	f
2	1844	women	jeans	Women	Skinny	\N	\N	\N	\N	\N	\N	f
130	185	women	pants	Women	Skinny	\N	\N	\N	\N	\N	\N	f
1	1845	women	jeans	Women	Straight	\N	\N	\N	\N	\N	\N	t
129	1846	women	pants	Women	Straight	\N	\N	\N	\N	\N	\N	t
5	1842	women	jeans	Women	\N	\N	High-rise	\N	\N	\N	\N	f
163	1099	women	shorts	Women	\N	\N	High-rise	\N	\N	\N	\N	f
164	1838	women	shorts	Women	\N	\N	Low-rise	\N	\N	\N	\N	f
56	1666	boys	shirt	Boys	\N	\N	\N	\N	\N	\N	Long sleeve	f
52	1539	girls	shirt	Girls	\N	\N	\N	\N	\N	\N	Long sleeve	f
36	1810	men	t-shirt	Men	\N	\N	\N	\N	\N	\N	Long sleeve	f
60	224	women	blouse	Women	\N	\N	\N	\N	\N	\N	Long sleeve	f
55	1665	boys	shirt	Boys	\N	\N	\N	\N	\N	\N	Short sleeve	f
51	1538	girls	shirt	Girls	\N	\N	\N	\N	\N	\N	Short sleeve	f
59	223	women	blouse	Women	\N	\N	\N	\N	\N	\N	Short sleeve	f
57	1667	boys	shirt	Boys	\N	\N	\N	\N	\N	\N	Sleeveless	f
53	1540	girls	shirt	Girls	\N	\N	\N	\N	\N	\N	Sleeveless	f
81	1813	men	sweater	Men	\N	\N	\N	\N	\N	Crew neck	\N	t
65	1044	women	top	Women	\N	\N	\N	\N	\N	Halter	\N	f
64	1042	women	top	Women	\N	\N	\N	\N	\N	Off-shoulder	\N	f
91	1670	boys	sweater	Boys	\N	\N	\N	\N	\N	Turtleneck	\N	f
87	1544	girls	sweater	Girls	\N	\N	\N	\N	\N	Turtleneck	\N	f
83	265	men	sweater	Men	\N	\N	\N	\N	\N	Turtleneck	\N	f
77	1045	women	sweater	Women	\N	\N	\N	\N	\N	Turtleneck	\N	f
79	191	women	sweater	Women	\N	\N	\N	\N	\N	Turtleneck	\N	f
90	1669	boys	sweater	Boys	\N	\N	\N	\N	\N	V-neck	\N	f
86	1543	girls	sweater	Girls	\N	\N	\N	\N	\N	V-neck	\N	f
82	264	men	sweater	Men	\N	\N	\N	\N	\N	V-neck	\N	f
78	190	women	sweater	Women	\N	\N	\N	\N	\N	V-neck	\N	f
6	1840	women	jeans	Women	\N	Cropped	\N	\N	\N	\N	\N	f
180	2927	women	skirt	Women	\N	Knee length	\N	\N	\N	\N	\N	f
31	1553	girls	dress	Girls	\N	Maxi	\N	\N	\N	\N	\N	f
19	1055	women	dress	Women	\N	Maxi	\N	\N	\N	\N	\N	f
182	200	women	skirt	Women	\N	Maxi	\N	\N	\N	\N	\N	f
18	1056	women	dress	Women	\N	Midi	\N	\N	\N	\N	\N	f
181	199	women	skirt	Women	\N	Midi	\N	\N	\N	\N	\N	f
30	1554	girls	dress	Girls	\N	Mini	\N	\N	\N	\N	\N	t
17	178	women	dress	Women	\N	Mini	\N	\N	\N	\N	\N	f
179	198	women	skirt	Women	\N	Mini	\N	\N	\N	\N	\N	t
45	1801	men	shirt	Men	\N	\N	\N	\N	Checkered	\N	\N	f
33	1806	men	t-shirt	Men	\N	\N	\N	\N	Solid	\N	\N	t
44	1803	men	shirt	Men	\N	\N	\N	\N	Solid	\N	\N	t
35	1808	men	t-shirt	Men	\N	\N	\N	\N	Striped	\N	\N	f
47	1805	men	shirt	Men	\N	\N	\N	\N	Striped	\N	\N	f
303	1750	boys	swim suit	Boys	\N	\N	\N	\N	\N	\N	\N	t
302	1590	girls	swim suit	Girls	\N	\N	\N	\N	\N	\N	\N	t
301	84	men	swim suit	Men	\N	\N	\N	\N	\N	\N	\N	t
300	218	women	swim suit	Women	\N	\N	\N	\N	\N	\N	\N	t
72	1835	women	body suit	Women	\N	\N	\N	\N	\N	\N	\N	t
299	1204	boys	track suit	Boys	\N	\N	\N	\N	\N	\N	\N	t
298	1253	girls	track suit	Girls	\N	\N	\N	\N	\N	\N	\N	t
297	582	men	track suit	Men	\N	\N	\N	\N	\N	\N	\N	t
296	572	women	track suit	Women	\N	\N	\N	\N	\N	\N	\N	t
261	1702	boys	jump suit	Boys	\N	\N	\N	\N	\N	\N	\N	t
260	1568	girls	jump suit	Girls	\N	\N	\N	\N	\N	\N	\N	t
262	268	men	jump suit	Men	\N	\N	\N	\N	\N	\N	\N	t
258	1131	women	jump suit	Women	\N	\N	\N	\N	\N	\N	\N	t
259	1134	women	jump suit	Women	\N	\N	\N	\N	\N	\N	\N	f
278	1673	boys	waistcoat	Boys	\N	\N	\N	\N	\N	\N	\N	t
279	1671	boys	waistcoat	Boys	\N	\N	\N	\N	\N	\N	\N	f
277	1551	girls	waistcoat	Girls	\N	\N	\N	\N	\N	\N	\N	t
276	1788	men	waistcoat	Men	\N	\N	\N	\N	\N	\N	\N	t
118	2575	boys	fleece jacket	Boys	\N	\N	\N	\N	\N	\N	\N	t
117	2547	girls	fleece jacket	Girls	\N	\N	\N	\N	\N	\N	\N	t
116	1858	men	fleece jacket	Men	\N	\N	\N	\N	\N	\N	\N	t
115	1086	women	fleece jacket	Women	\N	\N	\N	\N	\N	\N	\N	t
\.


--
-- Data for Name: order_products; Type: TABLE DATA; Schema: vinted; Owner: stoflow_user
--

COPY vinted.order_products (id, transaction_id, vinted_item_id, product_id, title, price, size, brand, photo_url, created_at) FROM stdin;
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: vinted; Owner: stoflow_user
--

COPY vinted.orders (transaction_id, buyer_id, buyer_login, seller_id, seller_login, status, total_price, currency, shipping_price, service_fee, buyer_protection_fee, seller_revenue, tracking_number, carrier, shipping_tracking_code, created_at_vinted, shipped_at, delivered_at, completed_at, created_at, updated_at) FROM stdin;
\.


--
-- Name: ebay_category_mapping_id_seq; Type: SEQUENCE SET; Schema: ebay; Owner: stoflow_user
--

SELECT pg_catalog.setval('ebay.ebay_category_mapping_id_seq', 95, true);


--
-- Name: exchange_rate_config_id_seq; Type: SEQUENCE SET; Schema: ebay; Owner: stoflow_user
--

SELECT pg_catalog.setval('ebay.exchange_rate_config_id_seq', 2, true);


--
-- Name: marketplace_config_id_seq; Type: SEQUENCE SET; Schema: ebay; Owner: stoflow_user
--

SELECT pg_catalog.setval('ebay.marketplace_config_id_seq', 8, true);


--
-- Name: admin_audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: stoflow_user
--

SELECT pg_catalog.setval('public.admin_audit_logs_id_seq', 1, false);


--
-- Name: ai_credits_id_seq; Type: SEQUENCE SET; Schema: public; Owner: stoflow_user
--

SELECT pg_catalog.setval('public.ai_credits_id_seq', 1, false);


--
-- Name: doc_articles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: stoflow_user
--

SELECT pg_catalog.setval('public.doc_articles_id_seq', 3, true);


--
-- Name: doc_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: stoflow_user
--

SELECT pg_catalog.setval('public.doc_categories_id_seq', 2, true);


--
-- Name: migration_errors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: stoflow_user
--

SELECT pg_catalog.setval('public.migration_errors_id_seq', 1, false);


--
-- Name: permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: stoflow_user
--

SELECT pg_catalog.setval('public.permissions_id_seq', 25, true);


--
-- Name: role_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: stoflow_user
--

SELECT pg_catalog.setval('public.role_permissions_id_seq', 53, true);


--
-- Name: subscription_features_id_seq; Type: SEQUENCE SET; Schema: public; Owner: stoflow_user
--

SELECT pg_catalog.setval('public.subscription_features_id_seq', 15, true);


--
-- Name: subscription_quotas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: stoflow_user
--

SELECT pg_catalog.setval('public.subscription_quotas_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: stoflow_user
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: ai_generation_logs_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.ai_generation_logs_id_seq', 1, false);


--
-- Name: batch_jobs_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.batch_jobs_id_seq', 1, false);


--
-- Name: ebay_credentials_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.ebay_credentials_id_seq', 1, false);


--
-- Name: ebay_orders_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.ebay_orders_id_seq', 1, false);


--
-- Name: ebay_orders_products_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.ebay_orders_products_id_seq', 1, false);


--
-- Name: ebay_products_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.ebay_products_id_seq', 1, false);


--
-- Name: ebay_promoted_listings_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.ebay_promoted_listings_id_seq', 1, false);


--
-- Name: etsy_credentials_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.etsy_credentials_id_seq', 1, false);


--
-- Name: plugin_tasks_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.plugin_tasks_id_seq', 1, false);


--
-- Name: product_images_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.product_images_id_seq', 1, false);


--
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.products_id_seq', 1, false);


--
-- Name: publication_history_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.publication_history_id_seq', 1, false);


--
-- Name: vinted_connection_vinted_user_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.vinted_connection_vinted_user_id_seq', 1, false);


--
-- Name: vinted_conversations_conversation_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.vinted_conversations_conversation_id_seq', 1, false);


--
-- Name: vinted_error_logs_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.vinted_error_logs_id_seq', 1, false);


--
-- Name: vinted_job_stats_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.vinted_job_stats_id_seq', 1, false);


--
-- Name: vinted_jobs_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.vinted_jobs_id_seq', 1, false);


--
-- Name: vinted_messages_id_seq; Type: SEQUENCE SET; Schema: template_tenant; Owner: stoflow_user
--

SELECT pg_catalog.setval('template_tenant.vinted_messages_id_seq', 1, false);


--
-- Name: ai_generation_logs_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.ai_generation_logs_id_seq', 1, false);


--
-- Name: batch_jobs_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.batch_jobs_id_seq', 1, false);


--
-- Name: ebay_credentials_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.ebay_credentials_id_seq', 1, false);


--
-- Name: ebay_orders_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.ebay_orders_id_seq', 1, false);


--
-- Name: ebay_orders_products_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.ebay_orders_products_id_seq', 1, false);


--
-- Name: ebay_products_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.ebay_products_id_seq', 1, false);


--
-- Name: ebay_promoted_listings_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.ebay_promoted_listings_id_seq', 1, false);


--
-- Name: etsy_credentials_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.etsy_credentials_id_seq', 1, false);


--
-- Name: plugin_tasks_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.plugin_tasks_id_seq', 1, false);


--
-- Name: product_images_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.product_images_id_seq', 1, false);


--
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.products_id_seq', 1, false);


--
-- Name: publication_history_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.publication_history_id_seq', 1, false);


--
-- Name: vinted_connection_vinted_user_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.vinted_connection_vinted_user_id_seq', 1, false);


--
-- Name: vinted_conversations_conversation_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.vinted_conversations_conversation_id_seq', 1, false);


--
-- Name: vinted_error_logs_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.vinted_error_logs_id_seq', 1, false);


--
-- Name: vinted_job_stats_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.vinted_job_stats_id_seq', 1, false);


--
-- Name: vinted_jobs_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.vinted_jobs_id_seq', 1, false);


--
-- Name: vinted_messages_id_seq; Type: SEQUENCE SET; Schema: user_1; Owner: stoflow_user
--

SELECT pg_catalog.setval('user_1.vinted_messages_id_seq', 1, false);


--
-- Name: action_types_id_seq; Type: SEQUENCE SET; Schema: vinted; Owner: stoflow_user
--

SELECT pg_catalog.setval('vinted.action_types_id_seq', 6, true);


--
-- Name: categories_id_seq; Type: SEQUENCE SET; Schema: vinted; Owner: stoflow_user
--

SELECT pg_catalog.setval('vinted.categories_id_seq', 1, false);


--
-- Name: deletions_id_seq; Type: SEQUENCE SET; Schema: vinted; Owner: stoflow_user
--

SELECT pg_catalog.setval('vinted.deletions_id_seq', 1, false);


--
-- Name: mapping_id_seq; Type: SEQUENCE SET; Schema: vinted; Owner: stoflow_user
--

SELECT pg_catalog.setval('vinted.mapping_id_seq', 307, true);


--
-- Name: order_products_id_seq; Type: SEQUENCE SET; Schema: vinted; Owner: stoflow_user
--

SELECT pg_catalog.setval('vinted.order_products_id_seq', 1, false);


--
-- Name: vinted_orders_transaction_id_seq; Type: SEQUENCE SET; Schema: vinted; Owner: stoflow_user
--

SELECT pg_catalog.setval('vinted.vinted_orders_transaction_id_seq', 1, false);


--
-- Name: aspect_closure aspect_closure_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_closure
    ADD CONSTRAINT aspect_closure_pkey PRIMARY KEY (ebay_gb);


--
-- Name: aspect_colour aspect_colour_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_colour
    ADD CONSTRAINT aspect_colour_pkey PRIMARY KEY (ebay_gb);


--
-- Name: aspect_department aspect_department_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_department
    ADD CONSTRAINT aspect_department_pkey PRIMARY KEY (ebay_gb);


--
-- Name: aspect_features aspect_features_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_features
    ADD CONSTRAINT aspect_features_pkey PRIMARY KEY (ebay_gb);


--
-- Name: aspect_fit aspect_fit_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_fit
    ADD CONSTRAINT aspect_fit_pkey PRIMARY KEY (ebay_gb);


--
-- Name: aspect_inside_leg aspect_inside_leg_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_inside_leg
    ADD CONSTRAINT aspect_inside_leg_pkey PRIMARY KEY (ebay_gb);


--
-- Name: aspect_name_mapping aspect_mappings_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_name_mapping
    ADD CONSTRAINT aspect_mappings_pkey PRIMARY KEY (aspect_key);


--
-- Name: aspect_material aspect_material_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_material
    ADD CONSTRAINT aspect_material_pkey PRIMARY KEY (ebay_gb);


--
-- Name: aspect_neckline aspect_neckline_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_neckline
    ADD CONSTRAINT aspect_neckline_pkey PRIMARY KEY (ebay_gb);


--
-- Name: aspect_occasion aspect_occasion_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_occasion
    ADD CONSTRAINT aspect_occasion_pkey PRIMARY KEY (ebay_gb);


--
-- Name: aspect_pattern aspect_pattern_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_pattern
    ADD CONSTRAINT aspect_pattern_pkey PRIMARY KEY (ebay_gb);


--
-- Name: aspect_rise aspect_rise_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_rise
    ADD CONSTRAINT aspect_rise_pkey PRIMARY KEY (ebay_gb);


--
-- Name: aspect_size aspect_size_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_size
    ADD CONSTRAINT aspect_size_pkey PRIMARY KEY (ebay_gb);


--
-- Name: aspect_sleeve_length aspect_sleeve_length_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_sleeve_length
    ADD CONSTRAINT aspect_sleeve_length_pkey PRIMARY KEY (ebay_gb);


--
-- Name: aspect_style aspect_style_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_style
    ADD CONSTRAINT aspect_style_pkey PRIMARY KEY (ebay_gb);


--
-- Name: aspect_type aspect_type_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_type
    ADD CONSTRAINT aspect_type_pkey PRIMARY KEY (ebay_gb);


--
-- Name: aspect_waist_size aspect_waist_size_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.aspect_waist_size
    ADD CONSTRAINT aspect_waist_size_pkey PRIMARY KEY (ebay_gb);


--
-- Name: category_mapping ebay_category_mapping_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.category_mapping
    ADD CONSTRAINT ebay_category_mapping_pkey PRIMARY KEY (id);


--
-- Name: exchange_rate exchange_rate_config_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.exchange_rate
    ADD CONSTRAINT exchange_rate_config_pkey PRIMARY KEY (id);


--
-- Name: marketplace_config marketplace_config_pkey; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.marketplace_config
    ADD CONSTRAINT marketplace_config_pkey PRIMARY KEY (id);


--
-- Name: exchange_rate uq_currency; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.exchange_rate
    ADD CONSTRAINT uq_currency UNIQUE (currency);


--
-- Name: category_mapping uq_ebay_category_mapping; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.category_mapping
    ADD CONSTRAINT uq_ebay_category_mapping UNIQUE (my_category, my_gender);


--
-- Name: marketplace_config uq_marketplace_id; Type: CONSTRAINT; Schema: ebay; Owner: stoflow_user
--

ALTER TABLE ONLY ebay.marketplace_config
    ADD CONSTRAINT uq_marketplace_id UNIQUE (marketplace_id);


--
-- Name: brands brands_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.brands
    ADD CONSTRAINT brands_pkey PRIMARY KEY (name);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (name_en);


--
-- Name: closures closures_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.closures
    ADD CONSTRAINT closures_pkey PRIMARY KEY (name_en);


--
-- Name: colors colors_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.colors
    ADD CONSTRAINT colors_pkey PRIMARY KEY (name_en);


--
-- Name: condition_sups condition_sup_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.condition_sups
    ADD CONSTRAINT condition_sup_pkey PRIMARY KEY (name_en);


--
-- Name: conditions conditions_new_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.conditions
    ADD CONSTRAINT conditions_new_pkey PRIMARY KEY (note);


--
-- Name: decades decades_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.decades
    ADD CONSTRAINT decades_pkey PRIMARY KEY (name_en);


--
-- Name: dim1 dim1_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.dim1
    ADD CONSTRAINT dim1_pkey PRIMARY KEY (value);


--
-- Name: dim2 dim2_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.dim2
    ADD CONSTRAINT dim2_pkey PRIMARY KEY (value);


--
-- Name: dim3 dim3_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.dim3
    ADD CONSTRAINT dim3_pkey PRIMARY KEY (value);


--
-- Name: dim4 dim4_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.dim4
    ADD CONSTRAINT dim4_pkey PRIMARY KEY (value);


--
-- Name: dim5 dim5_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.dim5
    ADD CONSTRAINT dim5_pkey PRIMARY KEY (value);


--
-- Name: dim6 dim6_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.dim6
    ADD CONSTRAINT dim6_pkey PRIMARY KEY (value);


--
-- Name: fits fits_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.fits
    ADD CONSTRAINT fits_pkey PRIMARY KEY (name_en);


--
-- Name: genders genders_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.genders
    ADD CONSTRAINT genders_pkey PRIMARY KEY (name_en);


--
-- Name: lengths lengths_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.lengths
    ADD CONSTRAINT lengths_pkey PRIMARY KEY (name_en);


--
-- Name: linings linings_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.linings
    ADD CONSTRAINT linings_pkey PRIMARY KEY (name_en);


--
-- Name: materials materials_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.materials
    ADD CONSTRAINT materials_pkey PRIMARY KEY (name_en);


--
-- Name: necklines necklines_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.necklines
    ADD CONSTRAINT necklines_pkey PRIMARY KEY (name_en);


--
-- Name: origins origins_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.origins
    ADD CONSTRAINT origins_pkey PRIMARY KEY (name_en);


--
-- Name: patterns patterns_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.patterns
    ADD CONSTRAINT patterns_pkey PRIMARY KEY (name_en);


--
-- Name: rises rises_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.rises
    ADD CONSTRAINT rises_pkey PRIMARY KEY (name_en);


--
-- Name: seasons seasons_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.seasons
    ADD CONSTRAINT seasons_pkey PRIMARY KEY (name_en);


--
-- Name: sizes_normalized sizes_normalized_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.sizes_normalized
    ADD CONSTRAINT sizes_normalized_pkey PRIMARY KEY (name_en);


--
-- Name: sizes_original sizes_original_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.sizes_original
    ADD CONSTRAINT sizes_original_pkey PRIMARY KEY (name);


--
-- Name: sleeve_lengths sleeve_lengths_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.sleeve_lengths
    ADD CONSTRAINT sleeve_lengths_pkey PRIMARY KEY (name_en);


--
-- Name: sports sports_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.sports
    ADD CONSTRAINT sports_pkey PRIMARY KEY (name_en);


--
-- Name: stretches stretches_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.stretches
    ADD CONSTRAINT stretches_pkey PRIMARY KEY (name_en);


--
-- Name: trends trends_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.trends
    ADD CONSTRAINT trends_pkey PRIMARY KEY (name_en);


--
-- Name: unique_features unique_features_pkey; Type: CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.unique_features
    ADD CONSTRAINT unique_features_pkey PRIMARY KEY (name_en);


--
-- Name: admin_audit_logs admin_audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.admin_audit_logs
    ADD CONSTRAINT admin_audit_logs_pkey PRIMARY KEY (id);


--
-- Name: ai_credits ai_credits_pkey; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.ai_credits
    ADD CONSTRAINT ai_credits_pkey PRIMARY KEY (id);


--
-- Name: ai_credits ai_credits_user_id_key; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.ai_credits
    ADD CONSTRAINT ai_credits_user_id_key UNIQUE (user_id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: clothing_prices clothing_prices_pkey; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.clothing_prices
    ADD CONSTRAINT clothing_prices_pkey PRIMARY KEY (brand, category);


--
-- Name: doc_articles doc_articles_pkey; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.doc_articles
    ADD CONSTRAINT doc_articles_pkey PRIMARY KEY (id);


--
-- Name: doc_categories doc_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.doc_categories
    ADD CONSTRAINT doc_categories_pkey PRIMARY KEY (id);


--
-- Name: migration_errors idx_migration_errors_schema_product; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.migration_errors
    ADD CONSTRAINT idx_migration_errors_schema_product UNIQUE (schema_name, product_id, migration_name, error_type);


--
-- Name: migration_errors migration_errors_pkey; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.migration_errors
    ADD CONSTRAINT migration_errors_pkey PRIMARY KEY (id);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: revoked_tokens revoked_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.revoked_tokens
    ADD CONSTRAINT revoked_tokens_pkey PRIMARY KEY (token_hash);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (id);


--
-- Name: subscription_features subscription_features_pkey; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.subscription_features
    ADD CONSTRAINT subscription_features_pkey PRIMARY KEY (id);


--
-- Name: subscription_quotas subscription_quotas_pkey; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.subscription_quotas
    ADD CONSTRAINT subscription_quotas_pkey PRIMARY KEY (id);


--
-- Name: role_permissions uq_role_permission; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT uq_role_permission UNIQUE (role, permission_id);


--
-- Name: subscription_quotas uq_subscription_quotas_tier; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.subscription_quotas
    ADD CONSTRAINT uq_subscription_quotas_tier UNIQUE (tier);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ai_generation_logs ai_generation_logs_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ai_generation_logs
    ADD CONSTRAINT ai_generation_logs_pkey PRIMARY KEY (id);


--
-- Name: batch_jobs batch_jobs_batch_id_key; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.batch_jobs
    ADD CONSTRAINT batch_jobs_batch_id_key UNIQUE (batch_id);


--
-- Name: batch_jobs batch_jobs_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.batch_jobs
    ADD CONSTRAINT batch_jobs_pkey PRIMARY KEY (id);


--
-- Name: ebay_credentials ebay_credentials_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_credentials
    ADD CONSTRAINT ebay_credentials_pkey PRIMARY KEY (id);


--
-- Name: ebay_orders ebay_orders_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_orders
    ADD CONSTRAINT ebay_orders_pkey PRIMARY KEY (id);


--
-- Name: ebay_orders_products ebay_orders_products_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_orders_products
    ADD CONSTRAINT ebay_orders_products_pkey PRIMARY KEY (id);


--
-- Name: ebay_products ebay_products_ebay_sku_key; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_products
    ADD CONSTRAINT ebay_products_ebay_sku_key UNIQUE (ebay_sku);


--
-- Name: ebay_products_marketplace ebay_products_marketplace_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_products_marketplace
    ADD CONSTRAINT ebay_products_marketplace_pkey PRIMARY KEY (sku_derived);


--
-- Name: ebay_products ebay_products_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_products
    ADD CONSTRAINT ebay_products_pkey PRIMARY KEY (id);


--
-- Name: ebay_products ebay_products_product_id_key; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_products
    ADD CONSTRAINT ebay_products_product_id_key UNIQUE (product_id);


--
-- Name: ebay_promoted_listings ebay_promoted_listings_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_promoted_listings
    ADD CONSTRAINT ebay_promoted_listings_pkey PRIMARY KEY (id);


--
-- Name: etsy_credentials etsy_credentials_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.etsy_credentials
    ADD CONSTRAINT etsy_credentials_pkey PRIMARY KEY (id);


--
-- Name: marketplace_jobs marketplace_jobs_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.marketplace_jobs
    ADD CONSTRAINT marketplace_jobs_pkey PRIMARY KEY (id);


--
-- Name: marketplace_tasks marketplace_tasks_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.marketplace_tasks
    ADD CONSTRAINT marketplace_tasks_pkey PRIMARY KEY (id);


--
-- Name: pending_instructions pending_instructions_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.pending_instructions
    ADD CONSTRAINT pending_instructions_pkey PRIMARY KEY (id);


--
-- Name: product_colors pk_product_colors; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.product_colors
    ADD CONSTRAINT pk_product_colors PRIMARY KEY (product_id, color);


--
-- Name: product_condition_sups pk_product_condition_sups; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.product_condition_sups
    ADD CONSTRAINT pk_product_condition_sups PRIMARY KEY (product_id, condition_sup);


--
-- Name: product_materials pk_product_materials; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.product_materials
    ADD CONSTRAINT pk_product_materials PRIMARY KEY (product_id, material);


--
-- Name: product_images product_images_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.product_images
    ADD CONSTRAINT product_images_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: publication_history publication_history_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.publication_history
    ADD CONSTRAINT publication_history_pkey PRIMARY KEY (id);


--
-- Name: ebay_promoted_listings uq_ad_id; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_promoted_listings
    ADD CONSTRAINT uq_ad_id UNIQUE (ad_id);


--
-- Name: ebay_orders uq_order_id; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_orders
    ADD CONSTRAINT uq_order_id UNIQUE (order_id);


--
-- Name: vinted_products uq_template_vinted_products_product_id; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_products
    ADD CONSTRAINT uq_template_vinted_products_product_id UNIQUE (product_id);


--
-- Name: vinted_connection vinted_connection_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_connection
    ADD CONSTRAINT vinted_connection_pkey PRIMARY KEY (vinted_user_id);


--
-- Name: vinted_conversations vinted_conversations_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_conversations
    ADD CONSTRAINT vinted_conversations_pkey PRIMARY KEY (conversation_id);


--
-- Name: vinted_error_logs vinted_error_logs_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_error_logs
    ADD CONSTRAINT vinted_error_logs_pkey PRIMARY KEY (id);


--
-- Name: vinted_job_stats vinted_job_stats_action_type_id_date_key; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_job_stats
    ADD CONSTRAINT vinted_job_stats_action_type_id_date_key UNIQUE (action_type_id, date);


--
-- Name: vinted_job_stats vinted_job_stats_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_job_stats
    ADD CONSTRAINT vinted_job_stats_pkey PRIMARY KEY (id);


--
-- Name: vinted_messages vinted_messages_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_messages
    ADD CONSTRAINT vinted_messages_pkey PRIMARY KEY (id);


--
-- Name: vinted_products vinted_products_pkey; Type: CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_products
    ADD CONSTRAINT vinted_products_pkey PRIMARY KEY (vinted_id);


--
-- Name: ai_generation_logs ai_generation_logs_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ai_generation_logs
    ADD CONSTRAINT ai_generation_logs_pkey PRIMARY KEY (id);


--
-- Name: batch_jobs batch_jobs_batch_id_key; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.batch_jobs
    ADD CONSTRAINT batch_jobs_batch_id_key UNIQUE (batch_id);


--
-- Name: batch_jobs batch_jobs_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.batch_jobs
    ADD CONSTRAINT batch_jobs_pkey PRIMARY KEY (id);


--
-- Name: ebay_credentials ebay_credentials_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_credentials
    ADD CONSTRAINT ebay_credentials_pkey PRIMARY KEY (id);


--
-- Name: ebay_orders ebay_orders_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_orders
    ADD CONSTRAINT ebay_orders_pkey PRIMARY KEY (id);


--
-- Name: ebay_orders_products ebay_orders_products_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_orders_products
    ADD CONSTRAINT ebay_orders_products_pkey PRIMARY KEY (id);


--
-- Name: ebay_products ebay_products_ebay_sku_key; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_products
    ADD CONSTRAINT ebay_products_ebay_sku_key UNIQUE (ebay_sku);


--
-- Name: ebay_products_marketplace ebay_products_marketplace_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_products_marketplace
    ADD CONSTRAINT ebay_products_marketplace_pkey PRIMARY KEY (sku_derived);


--
-- Name: ebay_products ebay_products_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_products
    ADD CONSTRAINT ebay_products_pkey PRIMARY KEY (id);


--
-- Name: ebay_products ebay_products_product_id_key; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_products
    ADD CONSTRAINT ebay_products_product_id_key UNIQUE (product_id);


--
-- Name: ebay_promoted_listings ebay_promoted_listings_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_promoted_listings
    ADD CONSTRAINT ebay_promoted_listings_pkey PRIMARY KEY (id);


--
-- Name: etsy_credentials etsy_credentials_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.etsy_credentials
    ADD CONSTRAINT etsy_credentials_pkey PRIMARY KEY (id);


--
-- Name: marketplace_jobs marketplace_jobs_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.marketplace_jobs
    ADD CONSTRAINT marketplace_jobs_pkey PRIMARY KEY (id);


--
-- Name: marketplace_tasks marketplace_tasks_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.marketplace_tasks
    ADD CONSTRAINT marketplace_tasks_pkey PRIMARY KEY (id);


--
-- Name: pending_instructions pending_instructions_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.pending_instructions
    ADD CONSTRAINT pending_instructions_pkey PRIMARY KEY (id);


--
-- Name: product_colors pk_product_colors; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.product_colors
    ADD CONSTRAINT pk_product_colors PRIMARY KEY (product_id, color);


--
-- Name: product_condition_sups pk_product_condition_sups; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.product_condition_sups
    ADD CONSTRAINT pk_product_condition_sups PRIMARY KEY (product_id, condition_sup);


--
-- Name: product_materials pk_product_materials; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.product_materials
    ADD CONSTRAINT pk_product_materials PRIMARY KEY (product_id, material);


--
-- Name: product_images product_images_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.product_images
    ADD CONSTRAINT product_images_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: publication_history publication_history_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.publication_history
    ADD CONSTRAINT publication_history_pkey PRIMARY KEY (id);


--
-- Name: ebay_promoted_listings uq_ad_id; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_promoted_listings
    ADD CONSTRAINT uq_ad_id UNIQUE (ad_id);


--
-- Name: ebay_orders uq_order_id; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_orders
    ADD CONSTRAINT uq_order_id UNIQUE (order_id);


--
-- Name: vinted_products uq_template_vinted_products_product_id; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_products
    ADD CONSTRAINT uq_template_vinted_products_product_id UNIQUE (product_id);


--
-- Name: vinted_connection vinted_connection_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_connection
    ADD CONSTRAINT vinted_connection_pkey PRIMARY KEY (vinted_user_id);


--
-- Name: vinted_conversations vinted_conversations_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_conversations
    ADD CONSTRAINT vinted_conversations_pkey PRIMARY KEY (conversation_id);


--
-- Name: vinted_error_logs vinted_error_logs_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_error_logs
    ADD CONSTRAINT vinted_error_logs_pkey PRIMARY KEY (id);


--
-- Name: vinted_job_stats vinted_job_stats_action_type_id_date_key; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_job_stats
    ADD CONSTRAINT vinted_job_stats_action_type_id_date_key UNIQUE (action_type_id, date);


--
-- Name: vinted_job_stats vinted_job_stats_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_job_stats
    ADD CONSTRAINT vinted_job_stats_pkey PRIMARY KEY (id);


--
-- Name: vinted_messages vinted_messages_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_messages
    ADD CONSTRAINT vinted_messages_pkey PRIMARY KEY (id);


--
-- Name: vinted_products vinted_products_pkey; Type: CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_products
    ADD CONSTRAINT vinted_products_pkey PRIMARY KEY (vinted_id);


--
-- Name: action_types vinted_action_types_code_key; Type: CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.action_types
    ADD CONSTRAINT vinted_action_types_code_key UNIQUE (code);


--
-- Name: action_types vinted_action_types_pkey; Type: CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.action_types
    ADD CONSTRAINT vinted_action_types_pkey PRIMARY KEY (id);


--
-- Name: categories vinted_categories_pkey; Type: CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.categories
    ADD CONSTRAINT vinted_categories_pkey PRIMARY KEY (id);


--
-- Name: deletions vinted_deletions_pkey; Type: CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.deletions
    ADD CONSTRAINT vinted_deletions_pkey PRIMARY KEY (id);


--
-- Name: mapping vinted_mapping_pkey; Type: CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.mapping
    ADD CONSTRAINT vinted_mapping_pkey PRIMARY KEY (id);


--
-- Name: order_products vinted_order_products_pkey; Type: CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.order_products
    ADD CONSTRAINT vinted_order_products_pkey PRIMARY KEY (id);


--
-- Name: orders vinted_orders_pkey; Type: CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.orders
    ADD CONSTRAINT vinted_orders_pkey PRIMARY KEY (transaction_id);


--
-- Name: idx_aspect_mappings_ebay_gb; Type: INDEX; Schema: ebay; Owner: stoflow_user
--

CREATE INDEX idx_aspect_mappings_ebay_gb ON ebay.aspect_name_mapping USING btree (ebay_gb);


--
-- Name: idx_ebay_category_lookup; Type: INDEX; Schema: ebay; Owner: stoflow_user
--

CREATE INDEX idx_ebay_category_lookup ON ebay.category_mapping USING btree (my_category, my_gender);


--
-- Name: idx_marketplace_config_active; Type: INDEX; Schema: ebay; Owner: stoflow_user
--

CREATE INDEX idx_marketplace_config_active ON ebay.marketplace_config USING btree (is_active);


--
-- Name: idx_marketplace_config_marketplace_id; Type: INDEX; Schema: ebay; Owner: stoflow_user
--

CREATE INDEX idx_marketplace_config_marketplace_id ON ebay.marketplace_config USING btree (marketplace_id);


--
-- Name: idx_colors_parent_color; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX idx_colors_parent_color ON product_attributes.colors USING btree (parent_color);


--
-- Name: idx_linings_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX idx_linings_name_en ON product_attributes.linings USING btree (name_en);


--
-- Name: idx_stretches_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX idx_stretches_name_en ON product_attributes.stretches USING btree (name_en);


--
-- Name: ix_materials_vinted_id; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_materials_vinted_id ON product_attributes.materials USING btree (vinted_id);


--
-- Name: ix_product_attributes_brands_name; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_brands_name ON product_attributes.brands USING btree (name);


--
-- Name: ix_product_attributes_categories_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_categories_name_en ON product_attributes.categories USING btree (name_en);


--
-- Name: ix_product_attributes_categories_parent_category; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_categories_parent_category ON product_attributes.categories USING btree (parent_category);


--
-- Name: ix_product_attributes_closures_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_closures_name_en ON product_attributes.closures USING btree (name_en);


--
-- Name: ix_product_attributes_colors_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_colors_name_en ON product_attributes.colors USING btree (name_en);


--
-- Name: ix_product_attributes_condition_sup_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_condition_sup_name_en ON product_attributes.condition_sups USING btree (name_en);


--
-- Name: ix_product_attributes_decades_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_decades_name_en ON product_attributes.decades USING btree (name_en);


--
-- Name: ix_product_attributes_fits_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_fits_name_en ON product_attributes.fits USING btree (name_en);


--
-- Name: ix_product_attributes_genders_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_genders_name_en ON product_attributes.genders USING btree (name_en);


--
-- Name: ix_product_attributes_lengths_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_lengths_name_en ON product_attributes.lengths USING btree (name_en);


--
-- Name: ix_product_attributes_materials_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_materials_name_en ON product_attributes.materials USING btree (name_en);


--
-- Name: ix_product_attributes_necklines_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_necklines_name_en ON product_attributes.necklines USING btree (name_en);


--
-- Name: ix_product_attributes_origins_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_origins_name_en ON product_attributes.origins USING btree (name_en);


--
-- Name: ix_product_attributes_patterns_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_patterns_name_en ON product_attributes.patterns USING btree (name_en);


--
-- Name: ix_product_attributes_rises_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_rises_name_en ON product_attributes.rises USING btree (name_en);


--
-- Name: ix_product_attributes_seasons_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_seasons_name_en ON product_attributes.seasons USING btree (name_en);


--
-- Name: ix_product_attributes_sizes_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_sizes_name_en ON product_attributes.sizes_normalized USING btree (name_en);


--
-- Name: ix_product_attributes_sleeve_lengths_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_sleeve_lengths_name_en ON product_attributes.sleeve_lengths USING btree (name_en);


--
-- Name: ix_product_attributes_sports_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_sports_name_en ON product_attributes.sports USING btree (name_en);


--
-- Name: ix_product_attributes_trends_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_trends_name_en ON product_attributes.trends USING btree (name_en);


--
-- Name: ix_product_attributes_unique_features_name_en; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_product_attributes_unique_features_name_en ON product_attributes.unique_features USING btree (name_en);


--
-- Name: ix_sizes_original_name; Type: INDEX; Schema: product_attributes; Owner: stoflow_user
--

CREATE INDEX ix_sizes_original_name ON product_attributes.sizes_original USING btree (name);


--
-- Name: idx_migration_errors_error_type; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX idx_migration_errors_error_type ON public.migration_errors USING btree (error_type);


--
-- Name: idx_migration_errors_migrated_at; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX idx_migration_errors_migrated_at ON public.migration_errors USING btree (migrated_at DESC);


--
-- Name: idx_migration_errors_schema_name; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX idx_migration_errors_schema_name ON public.migration_errors USING btree (schema_name);


--
-- Name: idx_revoked_tokens_expires_at; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX idx_revoked_tokens_expires_at ON public.revoked_tokens USING btree (expires_at);


--
-- Name: idx_revoked_tokens_token_hash; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX idx_revoked_tokens_token_hash ON public.revoked_tokens USING btree (token_hash);


--
-- Name: ix_audit_action; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_audit_action ON public.admin_audit_logs USING btree (action);


--
-- Name: ix_audit_admin_id; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_audit_admin_id ON public.admin_audit_logs USING btree (admin_id);


--
-- Name: ix_audit_created_at; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_audit_created_at ON public.admin_audit_logs USING btree (created_at);


--
-- Name: ix_audit_resource_type; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_audit_resource_type ON public.admin_audit_logs USING btree (resource_type);


--
-- Name: ix_doc_articles_category_id; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_doc_articles_category_id ON public.doc_articles USING btree (category_id);


--
-- Name: ix_doc_articles_display_order; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_doc_articles_display_order ON public.doc_articles USING btree (display_order);


--
-- Name: ix_doc_articles_slug; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE UNIQUE INDEX ix_doc_articles_slug ON public.doc_articles USING btree (slug);


--
-- Name: ix_doc_categories_display_order; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_doc_categories_display_order ON public.doc_categories USING btree (display_order);


--
-- Name: ix_doc_categories_slug; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE UNIQUE INDEX ix_doc_categories_slug ON public.doc_categories USING btree (slug);


--
-- Name: ix_public_ai_credits_id; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_public_ai_credits_id ON public.ai_credits USING btree (id);


--
-- Name: ix_public_ai_credits_user_id; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE UNIQUE INDEX ix_public_ai_credits_user_id ON public.ai_credits USING btree (user_id);


--
-- Name: ix_public_permissions_code; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE UNIQUE INDEX ix_public_permissions_code ON public.permissions USING btree (code);


--
-- Name: ix_public_permissions_id; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_public_permissions_id ON public.permissions USING btree (id);


--
-- Name: ix_public_role_permissions_id; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_public_role_permissions_id ON public.role_permissions USING btree (id);


--
-- Name: ix_public_role_permissions_permission_id; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_public_role_permissions_permission_id ON public.role_permissions USING btree (permission_id);


--
-- Name: ix_public_role_permissions_role; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_public_role_permissions_role ON public.role_permissions USING btree (role);


--
-- Name: ix_public_users_email; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE UNIQUE INDEX ix_public_users_email ON public.users USING btree (email);


--
-- Name: ix_public_users_id; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_public_users_id ON public.users USING btree (id);


--
-- Name: ix_subscription_features_subscription_quota_id; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_subscription_features_subscription_quota_id ON public.subscription_features USING btree (subscription_quota_id);


--
-- Name: ix_subscription_quotas_id; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_subscription_quotas_id ON public.subscription_quotas USING btree (id);


--
-- Name: ix_subscription_quotas_tier; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_subscription_quotas_tier ON public.subscription_quotas USING btree (tier);


--
-- Name: ix_users_email_verification_token; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_users_email_verification_token ON public.users USING btree (email_verification_token) WHERE (email_verification_token IS NOT NULL);


--
-- Name: ix_users_locked_until; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE INDEX ix_users_locked_until ON public.users USING btree (locked_until) WHERE (locked_until IS NOT NULL);


--
-- Name: ix_users_stripe_customer_id; Type: INDEX; Schema: public; Owner: stoflow_user
--

CREATE UNIQUE INDEX ix_users_stripe_customer_id ON public.users USING btree (stripe_customer_id);


--
-- Name: idx_batch_jobs_batch_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_batch_jobs_batch_id ON template_tenant.batch_jobs USING btree (batch_id);


--
-- Name: idx_batch_jobs_created_at; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_batch_jobs_created_at ON template_tenant.batch_jobs USING btree (created_at);


--
-- Name: idx_batch_jobs_marketplace; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_batch_jobs_marketplace ON template_tenant.batch_jobs USING btree (marketplace, status);


--
-- Name: idx_batch_jobs_status; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_batch_jobs_status ON template_tenant.batch_jobs USING btree (status, created_at);


--
-- Name: idx_ebay_op_order_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_op_order_id ON template_tenant.ebay_orders_products USING btree (order_id);


--
-- Name: idx_ebay_op_sku; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_op_sku ON template_tenant.ebay_orders_products USING btree (sku);


--
-- Name: idx_ebay_op_sku_original; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_op_sku_original ON template_tenant.ebay_orders_products USING btree (sku_original);


--
-- Name: idx_ebay_orders_fulfillment_status; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_orders_fulfillment_status ON template_tenant.ebay_orders USING btree (order_fulfillment_status);


--
-- Name: idx_ebay_orders_marketplace; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_orders_marketplace ON template_tenant.ebay_orders USING btree (marketplace_id);


--
-- Name: idx_ebay_orders_order_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_orders_order_id ON template_tenant.ebay_orders USING btree (order_id);


--
-- Name: idx_ebay_pl_campaign; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_pl_campaign ON template_tenant.ebay_promoted_listings USING btree (campaign_id);


--
-- Name: idx_ebay_pl_marketplace; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_pl_marketplace ON template_tenant.ebay_promoted_listings USING btree (marketplace_id);


--
-- Name: idx_ebay_pl_product_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_pl_product_id ON template_tenant.ebay_promoted_listings USING btree (product_id);


--
-- Name: idx_ebay_pl_status; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_pl_status ON template_tenant.ebay_promoted_listings USING btree (ad_status);


--
-- Name: idx_ebay_pm_listing_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_pm_listing_id ON template_tenant.ebay_products_marketplace USING btree (ebay_listing_id);


--
-- Name: idx_ebay_pm_marketplace; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_pm_marketplace ON template_tenant.ebay_products_marketplace USING btree (marketplace_id);


--
-- Name: idx_ebay_pm_product_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_pm_product_id ON template_tenant.ebay_products_marketplace USING btree (product_id);


--
-- Name: idx_ebay_pm_status; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_pm_status ON template_tenant.ebay_products_marketplace USING btree (status);


--
-- Name: idx_ebay_products_brand; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_products_brand ON template_tenant.ebay_products USING btree (brand);


--
-- Name: idx_ebay_products_ebay_listing_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_products_ebay_listing_id ON template_tenant.ebay_products USING btree (ebay_listing_id);


--
-- Name: idx_ebay_products_ebay_sku; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_products_ebay_sku ON template_tenant.ebay_products USING btree (ebay_sku);


--
-- Name: idx_ebay_products_marketplace_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_products_marketplace_id ON template_tenant.ebay_products USING btree (marketplace_id);


--
-- Name: idx_ebay_products_product_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_products_product_id ON template_tenant.ebay_products USING btree (product_id);


--
-- Name: idx_ebay_products_status; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_ebay_products_status ON template_tenant.ebay_products USING btree (status);


--
-- Name: idx_marketplace_jobs_batch_job_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_marketplace_jobs_batch_job_id ON template_tenant.marketplace_jobs USING btree (batch_job_id);


--
-- Name: idx_marketplace_jobs_marketplace; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_marketplace_jobs_marketplace ON template_tenant.marketplace_jobs USING btree (marketplace);


--
-- Name: idx_pending_instructions_user_status; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_pending_instructions_user_status ON template_tenant.pending_instructions USING btree (user_id, status);


--
-- Name: idx_product_colors_color; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_product_colors_color ON template_tenant.product_colors USING btree (color);


--
-- Name: idx_product_colors_product_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_product_colors_product_id ON template_tenant.product_colors USING btree (product_id);


--
-- Name: idx_product_condition_sups_condition_sup; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_product_condition_sups_condition_sup ON template_tenant.product_condition_sups USING btree (condition_sup);


--
-- Name: idx_product_condition_sups_product_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_product_condition_sups_product_id ON template_tenant.product_condition_sups USING btree (product_id);


--
-- Name: idx_product_materials_material; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_product_materials_material ON template_tenant.product_materials USING btree (material);


--
-- Name: idx_product_materials_product_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_product_materials_product_id ON template_tenant.product_materials USING btree (product_id);


--
-- Name: idx_products_stretch; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_products_stretch ON template_tenant.products USING btree (stretch);


--
-- Name: idx_template_marketplace_jobs_idempotency_key; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE UNIQUE INDEX idx_template_marketplace_jobs_idempotency_key ON template_tenant.marketplace_jobs USING btree (idempotency_key) WHERE (idempotency_key IS NOT NULL);


--
-- Name: idx_template_tenant_vinted_products_catalog_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_template_tenant_vinted_products_catalog_id ON template_tenant.vinted_products USING btree (catalog_id);


--
-- Name: idx_template_tenant_vinted_products_published_at; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_template_tenant_vinted_products_published_at ON template_tenant.vinted_products USING btree (published_at);


--
-- Name: idx_template_tenant_vinted_products_seller_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_template_tenant_vinted_products_seller_id ON template_tenant.vinted_products USING btree (seller_id);


--
-- Name: idx_template_vinted_products_product_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_template_vinted_products_product_id ON template_tenant.vinted_products USING btree (product_id) WHERE (product_id IS NOT NULL);


--
-- Name: idx_vinted_conversations_opposite_user; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_vinted_conversations_opposite_user ON template_tenant.vinted_conversations USING btree (opposite_user_id);


--
-- Name: idx_vinted_conversations_transaction; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_vinted_conversations_transaction ON template_tenant.vinted_conversations USING btree (transaction_id);


--
-- Name: idx_vinted_conversations_unread; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_vinted_conversations_unread ON template_tenant.vinted_conversations USING btree (is_unread);


--
-- Name: idx_vinted_conversations_updated; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_vinted_conversations_updated ON template_tenant.vinted_conversations USING btree (updated_at_vinted);


--
-- Name: idx_vinted_error_logs_created_at; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_vinted_error_logs_created_at ON template_tenant.vinted_error_logs USING btree (created_at);


--
-- Name: idx_vinted_error_logs_error_type; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_vinted_error_logs_error_type ON template_tenant.vinted_error_logs USING btree (error_type);


--
-- Name: idx_vinted_error_logs_product_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_vinted_error_logs_product_id ON template_tenant.vinted_error_logs USING btree (product_id);


--
-- Name: idx_vinted_messages_conversation; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_vinted_messages_conversation ON template_tenant.vinted_messages USING btree (conversation_id);


--
-- Name: idx_vinted_messages_created; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_vinted_messages_created ON template_tenant.vinted_messages USING btree (created_at_vinted);


--
-- Name: idx_vinted_messages_sender; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_vinted_messages_sender ON template_tenant.vinted_messages USING btree (sender_id);


--
-- Name: idx_vinted_messages_type; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_vinted_messages_type ON template_tenant.vinted_messages USING btree (entity_type);


--
-- Name: idx_vinted_products_brand; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_vinted_products_brand ON template_tenant.vinted_products USING btree (brand);


--
-- Name: idx_vinted_products_status; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX idx_vinted_products_status ON template_tenant.vinted_products USING btree (status);


--
-- Name: ix_etsy_credentials_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_etsy_credentials_id ON template_tenant.etsy_credentials USING btree (id);


--
-- Name: ix_etsy_credentials_shop_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_etsy_credentials_shop_id ON template_tenant.etsy_credentials USING btree (shop_id);


--
-- Name: ix_etsy_credentials_user_id_etsy; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_etsy_credentials_user_id_etsy ON template_tenant.etsy_credentials USING btree (user_id_etsy);


--
-- Name: ix_template_tenant_ai_generation_logs_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_ai_generation_logs_id ON template_tenant.ai_generation_logs USING btree (id);


--
-- Name: ix_template_tenant_ai_generation_logs_product_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_ai_generation_logs_product_id ON template_tenant.ai_generation_logs USING btree (product_id);


--
-- Name: ix_template_tenant_ebay_credentials_ebay_user_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_ebay_credentials_ebay_user_id ON template_tenant.ebay_credentials USING btree (ebay_user_id);


--
-- Name: ix_template_tenant_ebay_credentials_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_ebay_credentials_id ON template_tenant.ebay_credentials USING btree (id);


--
-- Name: ix_template_tenant_marketplace_tasks_platform; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_marketplace_tasks_platform ON template_tenant.marketplace_tasks USING btree (platform);


--
-- Name: ix_template_tenant_marketplace_tasks_product_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_marketplace_tasks_product_id ON template_tenant.marketplace_tasks USING btree (product_id);


--
-- Name: ix_template_tenant_marketplace_tasks_status; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_marketplace_tasks_status ON template_tenant.marketplace_tasks USING btree (status);


--
-- Name: ix_template_tenant_product_images_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_product_images_id ON template_tenant.product_images USING btree (id);


--
-- Name: ix_template_tenant_product_images_product_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_product_images_product_id ON template_tenant.product_images USING btree (product_id);


--
-- Name: ix_template_tenant_products_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_products_id ON template_tenant.products USING btree (id);


--
-- Name: ix_template_tenant_products_length; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_products_length ON template_tenant.products USING btree (length);


--
-- Name: ix_template_tenant_products_neckline; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_products_neckline ON template_tenant.products USING btree (neckline);


--
-- Name: ix_template_tenant_products_pattern; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_products_pattern ON template_tenant.products USING btree (pattern);


--
-- Name: ix_template_tenant_products_sport; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_products_sport ON template_tenant.products USING btree (sport);


--
-- Name: ix_template_tenant_publication_history_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_publication_history_id ON template_tenant.publication_history USING btree (id);


--
-- Name: ix_template_tenant_publication_history_product_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_publication_history_product_id ON template_tenant.publication_history USING btree (product_id);


--
-- Name: ix_template_tenant_vinted_connection_login; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_vinted_connection_login ON template_tenant.vinted_connection USING btree (login);


--
-- Name: ix_template_tenant_vinted_connection_user_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_tenant_vinted_connection_user_id ON template_tenant.vinted_connection USING btree (user_id);


--
-- Name: ix_template_vinted_conn_is_connected; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_template_vinted_conn_is_connected ON template_tenant.vinted_connection USING btree (is_connected);


--
-- Name: ix_templatetenant_marketplace_jobs_batch_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_templatetenant_marketplace_jobs_batch_id ON template_tenant.marketplace_jobs USING btree (batch_id);


--
-- Name: ix_templatetenant_marketplace_jobs_created_at; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_templatetenant_marketplace_jobs_created_at ON template_tenant.marketplace_jobs USING btree (created_at);


--
-- Name: ix_templatetenant_marketplace_jobs_priority; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_templatetenant_marketplace_jobs_priority ON template_tenant.marketplace_jobs USING btree (priority);


--
-- Name: ix_templatetenant_marketplace_jobs_status; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_templatetenant_marketplace_jobs_status ON template_tenant.marketplace_jobs USING btree (status);


--
-- Name: ix_templatetenant_marketplace_tasks_job_id; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE INDEX ix_templatetenant_marketplace_tasks_job_id ON template_tenant.marketplace_tasks USING btree (job_id);


--
-- Name: uq_product_colors_primary; Type: INDEX; Schema: template_tenant; Owner: stoflow_user
--

CREATE UNIQUE INDEX uq_product_colors_primary ON template_tenant.product_colors USING btree (product_id) WHERE (is_primary = true);


--
-- Name: idx_batch_jobs_batch_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_batch_jobs_batch_id ON user_1.batch_jobs USING btree (batch_id);


--
-- Name: idx_batch_jobs_created_at; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_batch_jobs_created_at ON user_1.batch_jobs USING btree (created_at);


--
-- Name: idx_batch_jobs_marketplace; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_batch_jobs_marketplace ON user_1.batch_jobs USING btree (marketplace, status);


--
-- Name: idx_batch_jobs_status; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_batch_jobs_status ON user_1.batch_jobs USING btree (status, created_at);


--
-- Name: idx_ebay_op_order_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_op_order_id ON user_1.ebay_orders_products USING btree (order_id);


--
-- Name: idx_ebay_op_sku; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_op_sku ON user_1.ebay_orders_products USING btree (sku);


--
-- Name: idx_ebay_op_sku_original; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_op_sku_original ON user_1.ebay_orders_products USING btree (sku_original);


--
-- Name: idx_ebay_orders_fulfillment_status; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_orders_fulfillment_status ON user_1.ebay_orders USING btree (order_fulfillment_status);


--
-- Name: idx_ebay_orders_marketplace; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_orders_marketplace ON user_1.ebay_orders USING btree (marketplace_id);


--
-- Name: idx_ebay_orders_order_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_orders_order_id ON user_1.ebay_orders USING btree (order_id);


--
-- Name: idx_ebay_pl_campaign; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_pl_campaign ON user_1.ebay_promoted_listings USING btree (campaign_id);


--
-- Name: idx_ebay_pl_marketplace; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_pl_marketplace ON user_1.ebay_promoted_listings USING btree (marketplace_id);


--
-- Name: idx_ebay_pl_product_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_pl_product_id ON user_1.ebay_promoted_listings USING btree (product_id);


--
-- Name: idx_ebay_pl_status; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_pl_status ON user_1.ebay_promoted_listings USING btree (ad_status);


--
-- Name: idx_ebay_pm_listing_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_pm_listing_id ON user_1.ebay_products_marketplace USING btree (ebay_listing_id);


--
-- Name: idx_ebay_pm_marketplace; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_pm_marketplace ON user_1.ebay_products_marketplace USING btree (marketplace_id);


--
-- Name: idx_ebay_pm_product_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_pm_product_id ON user_1.ebay_products_marketplace USING btree (product_id);


--
-- Name: idx_ebay_pm_status; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_pm_status ON user_1.ebay_products_marketplace USING btree (status);


--
-- Name: idx_ebay_products_brand; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_products_brand ON user_1.ebay_products USING btree (brand);


--
-- Name: idx_ebay_products_ebay_listing_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_products_ebay_listing_id ON user_1.ebay_products USING btree (ebay_listing_id);


--
-- Name: idx_ebay_products_ebay_sku; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_products_ebay_sku ON user_1.ebay_products USING btree (ebay_sku);


--
-- Name: idx_ebay_products_marketplace_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_products_marketplace_id ON user_1.ebay_products USING btree (marketplace_id);


--
-- Name: idx_ebay_products_product_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_products_product_id ON user_1.ebay_products USING btree (product_id);


--
-- Name: idx_ebay_products_status; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_ebay_products_status ON user_1.ebay_products USING btree (status);


--
-- Name: idx_marketplace_jobs_batch_job_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_marketplace_jobs_batch_job_id ON user_1.marketplace_jobs USING btree (batch_job_id);


--
-- Name: idx_marketplace_jobs_marketplace; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_marketplace_jobs_marketplace ON user_1.marketplace_jobs USING btree (marketplace);


--
-- Name: idx_pending_instructions_user_status; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_pending_instructions_user_status ON user_1.pending_instructions USING btree (user_id, status);


--
-- Name: idx_product_colors_color; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_product_colors_color ON user_1.product_colors USING btree (color);


--
-- Name: idx_product_colors_product_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_product_colors_product_id ON user_1.product_colors USING btree (product_id);


--
-- Name: idx_product_condition_sups_condition_sup; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_product_condition_sups_condition_sup ON user_1.product_condition_sups USING btree (condition_sup);


--
-- Name: idx_product_condition_sups_product_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_product_condition_sups_product_id ON user_1.product_condition_sups USING btree (product_id);


--
-- Name: idx_product_materials_material; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_product_materials_material ON user_1.product_materials USING btree (material);


--
-- Name: idx_product_materials_product_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_product_materials_product_id ON user_1.product_materials USING btree (product_id);


--
-- Name: idx_products_stretch; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_products_stretch ON user_1.products USING btree (stretch);


--
-- Name: idx_template_marketplace_jobs_idempotency_key; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE UNIQUE INDEX idx_template_marketplace_jobs_idempotency_key ON user_1.marketplace_jobs USING btree (idempotency_key) WHERE (idempotency_key IS NOT NULL);


--
-- Name: idx_template_vinted_products_product_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_template_vinted_products_product_id ON user_1.vinted_products USING btree (product_id) WHERE (product_id IS NOT NULL);


--
-- Name: idx_user_3_vinted_products_catalog_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_user_3_vinted_products_catalog_id ON user_1.vinted_products USING btree (catalog_id);


--
-- Name: idx_user_3_vinted_products_published_at; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_user_3_vinted_products_published_at ON user_1.vinted_products USING btree (published_at);


--
-- Name: idx_user_3_vinted_products_seller_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_user_3_vinted_products_seller_id ON user_1.vinted_products USING btree (seller_id);


--
-- Name: idx_vinted_conversations_opposite_user; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_vinted_conversations_opposite_user ON user_1.vinted_conversations USING btree (opposite_user_id);


--
-- Name: idx_vinted_conversations_transaction; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_vinted_conversations_transaction ON user_1.vinted_conversations USING btree (transaction_id);


--
-- Name: idx_vinted_conversations_unread; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_vinted_conversations_unread ON user_1.vinted_conversations USING btree (is_unread);


--
-- Name: idx_vinted_conversations_updated; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_vinted_conversations_updated ON user_1.vinted_conversations USING btree (updated_at_vinted);


--
-- Name: idx_vinted_error_logs_created_at; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_vinted_error_logs_created_at ON user_1.vinted_error_logs USING btree (created_at);


--
-- Name: idx_vinted_error_logs_error_type; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_vinted_error_logs_error_type ON user_1.vinted_error_logs USING btree (error_type);


--
-- Name: idx_vinted_error_logs_product_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_vinted_error_logs_product_id ON user_1.vinted_error_logs USING btree (product_id);


--
-- Name: idx_vinted_messages_conversation; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_vinted_messages_conversation ON user_1.vinted_messages USING btree (conversation_id);


--
-- Name: idx_vinted_messages_created; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_vinted_messages_created ON user_1.vinted_messages USING btree (created_at_vinted);


--
-- Name: idx_vinted_messages_sender; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_vinted_messages_sender ON user_1.vinted_messages USING btree (sender_id);


--
-- Name: idx_vinted_messages_type; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_vinted_messages_type ON user_1.vinted_messages USING btree (entity_type);


--
-- Name: idx_vinted_products_brand; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_vinted_products_brand ON user_1.vinted_products USING btree (brand);


--
-- Name: idx_vinted_products_status; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX idx_vinted_products_status ON user_1.vinted_products USING btree (status);


--
-- Name: ix_etsy_credentials_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_etsy_credentials_id ON user_1.etsy_credentials USING btree (id);


--
-- Name: ix_etsy_credentials_shop_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_etsy_credentials_shop_id ON user_1.etsy_credentials USING btree (shop_id);


--
-- Name: ix_etsy_credentials_user_id_etsy; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_etsy_credentials_user_id_etsy ON user_1.etsy_credentials USING btree (user_id_etsy);


--
-- Name: ix_template_vinted_conn_is_connected; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_template_vinted_conn_is_connected ON user_1.vinted_connection USING btree (is_connected);


--
-- Name: ix_templatetenant_marketplace_jobs_batch_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_templatetenant_marketplace_jobs_batch_id ON user_1.marketplace_jobs USING btree (batch_id);


--
-- Name: ix_templatetenant_marketplace_jobs_created_at; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_templatetenant_marketplace_jobs_created_at ON user_1.marketplace_jobs USING btree (created_at);


--
-- Name: ix_templatetenant_marketplace_jobs_priority; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_templatetenant_marketplace_jobs_priority ON user_1.marketplace_jobs USING btree (priority);


--
-- Name: ix_templatetenant_marketplace_jobs_status; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_templatetenant_marketplace_jobs_status ON user_1.marketplace_jobs USING btree (status);


--
-- Name: ix_templatetenant_marketplace_tasks_job_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_templatetenant_marketplace_tasks_job_id ON user_1.marketplace_tasks USING btree (job_id);


--
-- Name: ix_user_3_ai_generation_logs_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_ai_generation_logs_id ON user_1.ai_generation_logs USING btree (id);


--
-- Name: ix_user_3_ai_generation_logs_product_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_ai_generation_logs_product_id ON user_1.ai_generation_logs USING btree (product_id);


--
-- Name: ix_user_3_ebay_credentials_ebay_user_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_ebay_credentials_ebay_user_id ON user_1.ebay_credentials USING btree (ebay_user_id);


--
-- Name: ix_user_3_ebay_credentials_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_ebay_credentials_id ON user_1.ebay_credentials USING btree (id);


--
-- Name: ix_user_3_marketplace_tasks_platform; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_marketplace_tasks_platform ON user_1.marketplace_tasks USING btree (platform);


--
-- Name: ix_user_3_marketplace_tasks_product_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_marketplace_tasks_product_id ON user_1.marketplace_tasks USING btree (product_id);


--
-- Name: ix_user_3_marketplace_tasks_status; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_marketplace_tasks_status ON user_1.marketplace_tasks USING btree (status);


--
-- Name: ix_user_3_product_images_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_product_images_id ON user_1.product_images USING btree (id);


--
-- Name: ix_user_3_product_images_product_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_product_images_product_id ON user_1.product_images USING btree (product_id);


--
-- Name: ix_user_3_products_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_products_id ON user_1.products USING btree (id);


--
-- Name: ix_user_3_products_length; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_products_length ON user_1.products USING btree (length);


--
-- Name: ix_user_3_products_neckline; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_products_neckline ON user_1.products USING btree (neckline);


--
-- Name: ix_user_3_products_pattern; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_products_pattern ON user_1.products USING btree (pattern);


--
-- Name: ix_user_3_products_sport; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_products_sport ON user_1.products USING btree (sport);


--
-- Name: ix_user_3_publication_history_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_publication_history_id ON user_1.publication_history USING btree (id);


--
-- Name: ix_user_3_publication_history_product_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_publication_history_product_id ON user_1.publication_history USING btree (product_id);


--
-- Name: ix_user_3_vinted_connection_login; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_vinted_connection_login ON user_1.vinted_connection USING btree (login);


--
-- Name: ix_user_3_vinted_connection_user_id; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE INDEX ix_user_3_vinted_connection_user_id ON user_1.vinted_connection USING btree (user_id);


--
-- Name: uq_product_colors_primary; Type: INDEX; Schema: user_1; Owner: stoflow_user
--

CREATE UNIQUE INDEX uq_product_colors_primary ON user_1.product_colors USING btree (product_id) WHERE (is_primary = true);


--
-- Name: idx_deletions_date_deleted; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_deletions_date_deleted ON vinted.deletions USING btree (date_deleted);


--
-- Name: idx_deletions_days_active; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_deletions_days_active ON vinted.deletions USING btree (days_active);


--
-- Name: idx_deletions_id_site; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_deletions_id_site ON vinted.deletions USING btree (id_site);


--
-- Name: idx_deletions_id_vinted; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_deletions_id_vinted ON vinted.deletions USING btree (id_vinted);


--
-- Name: idx_mapping_default; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_mapping_default ON vinted.mapping USING btree (my_category, my_gender, is_default);


--
-- Name: idx_order_products_product_id; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_order_products_product_id ON vinted.order_products USING btree (product_id);


--
-- Name: idx_order_products_transaction_id; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_order_products_transaction_id ON vinted.order_products USING btree (transaction_id);


--
-- Name: idx_order_products_vinted_item_id; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_order_products_vinted_item_id ON vinted.order_products USING btree (vinted_item_id);


--
-- Name: idx_orders_buyer_id; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_orders_buyer_id ON vinted.orders USING btree (buyer_id);


--
-- Name: idx_orders_created_at_vinted; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_orders_created_at_vinted ON vinted.orders USING btree (created_at_vinted);


--
-- Name: idx_orders_status; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_orders_status ON vinted.orders USING btree (status);


--
-- Name: idx_vinted_categories_gender; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_vinted_categories_gender ON vinted.categories USING btree (gender);


--
-- Name: idx_vinted_categories_is_active; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_vinted_categories_is_active ON vinted.categories USING btree (is_active);


--
-- Name: idx_vinted_categories_is_leaf; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_vinted_categories_is_leaf ON vinted.categories USING btree (is_leaf);


--
-- Name: idx_vinted_categories_parent_id; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_vinted_categories_parent_id ON vinted.categories USING btree (parent_id);


--
-- Name: idx_vinted_mapping_my; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_vinted_mapping_my ON vinted.mapping USING btree (my_category, my_gender);


--
-- Name: idx_vinted_mapping_vinted; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE INDEX idx_vinted_mapping_vinted ON vinted.mapping USING btree (vinted_id);


--
-- Name: unique_default_per_couple; Type: INDEX; Schema: vinted; Owner: stoflow_user
--

CREATE UNIQUE INDEX unique_default_per_couple ON vinted.mapping USING btree (my_category, my_gender) WHERE (is_default = true);


--
-- Name: categories categories_parent_category_fkey; Type: FK CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.categories
    ADD CONSTRAINT categories_parent_category_fkey FOREIGN KEY (parent_category) REFERENCES product_attributes.categories(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: colors fk_colors_parent_color; Type: FK CONSTRAINT; Schema: product_attributes; Owner: stoflow_user
--

ALTER TABLE ONLY product_attributes.colors
    ADD CONSTRAINT fk_colors_parent_color FOREIGN KEY (parent_color) REFERENCES product_attributes.colors(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: admin_audit_logs admin_audit_logs_admin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.admin_audit_logs
    ADD CONSTRAINT admin_audit_logs_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: ai_credits ai_credits_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.ai_credits
    ADD CONSTRAINT ai_credits_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: doc_articles doc_articles_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.doc_articles
    ADD CONSTRAINT doc_articles_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.doc_categories(id) ON DELETE CASCADE;


--
-- Name: users fk_users_subscription_tier_id; Type: FK CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_subscription_tier_id FOREIGN KEY (subscription_tier_id) REFERENCES public.subscription_quotas(id);


--
-- Name: role_permissions role_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(id) ON DELETE CASCADE;


--
-- Name: subscription_features subscription_features_subscription_quota_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: stoflow_user
--

ALTER TABLE ONLY public.subscription_features
    ADD CONSTRAINT subscription_features_subscription_quota_id_fkey FOREIGN KEY (subscription_quota_id) REFERENCES public.subscription_quotas(id) ON DELETE CASCADE;


--
-- Name: ebay_orders_products ebay_orders_products_order_id_fkey; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_orders_products
    ADD CONSTRAINT ebay_orders_products_order_id_fkey FOREIGN KEY (order_id) REFERENCES template_tenant.ebay_orders(order_id) ON DELETE CASCADE;


--
-- Name: ebay_products_marketplace ebay_products_marketplace_product_id_fkey; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_products_marketplace
    ADD CONSTRAINT ebay_products_marketplace_product_id_fkey FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;


--
-- Name: ebay_products ebay_products_product_id_fkey; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_products
    ADD CONSTRAINT ebay_products_product_id_fkey FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: ebay_promoted_listings ebay_promoted_listings_product_id_fkey; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ebay_promoted_listings
    ADD CONSTRAINT ebay_promoted_listings_product_id_fkey FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;


--
-- Name: ai_generation_logs fk_ai_generation_logs_product_id; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.ai_generation_logs
    ADD CONSTRAINT fk_ai_generation_logs_product_id FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;


--
-- Name: batch_jobs fk_batch_jobs_user; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.batch_jobs
    ADD CONSTRAINT fk_batch_jobs_user FOREIGN KEY (created_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: marketplace_jobs fk_marketplace_jobs_batch_job; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.marketplace_jobs
    ADD CONSTRAINT fk_marketplace_jobs_batch_job FOREIGN KEY (batch_job_id) REFERENCES template_tenant.batch_jobs(id) ON DELETE SET NULL;


--
-- Name: marketplace_tasks fk_marketplace_tasks_job; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.marketplace_tasks
    ADD CONSTRAINT fk_marketplace_tasks_job FOREIGN KEY (job_id) REFERENCES template_tenant.marketplace_jobs(id) ON DELETE SET NULL;


--
-- Name: product_colors fk_product_colors_color; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.product_colors
    ADD CONSTRAINT fk_product_colors_color FOREIGN KEY (color) REFERENCES product_attributes.colors(name_en) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: product_colors fk_product_colors_product_id; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.product_colors
    ADD CONSTRAINT fk_product_colors_product_id FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;


--
-- Name: product_condition_sups fk_product_condition_sups_condition_sup; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.product_condition_sups
    ADD CONSTRAINT fk_product_condition_sups_condition_sup FOREIGN KEY (condition_sup) REFERENCES product_attributes.condition_sups(name_en) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: product_condition_sups fk_product_condition_sups_product_id; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.product_condition_sups
    ADD CONSTRAINT fk_product_condition_sups_product_id FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;


--
-- Name: product_images fk_product_images_product_id; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.product_images
    ADD CONSTRAINT fk_product_images_product_id FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;


--
-- Name: product_materials fk_product_materials_material; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.product_materials
    ADD CONSTRAINT fk_product_materials_material FOREIGN KEY (material) REFERENCES product_attributes.materials(name_en) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: product_materials fk_product_materials_product_id; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.product_materials
    ADD CONSTRAINT fk_product_materials_product_id FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;


--
-- Name: products fk_products_size_normalized; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_products_size_normalized FOREIGN KEY (size_normalized) REFERENCES product_attributes.sizes_normalized(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: products fk_products_stretch; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_products_stretch FOREIGN KEY (stretch) REFERENCES product_attributes.stretches(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: publication_history fk_publication_history_product_id; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.publication_history
    ADD CONSTRAINT fk_publication_history_product_id FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;


--
-- Name: products fk_template_tenant_products_brand; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_brand FOREIGN KEY (brand) REFERENCES product_attributes.brands(name) ON DELETE SET NULL;


--
-- Name: products fk_template_tenant_products_category; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_category FOREIGN KEY (category) REFERENCES product_attributes.categories(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: products fk_template_tenant_products_closure; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_closure FOREIGN KEY (closure) REFERENCES product_attributes.closures(name_en) ON DELETE SET NULL;


--
-- Name: products fk_template_tenant_products_condition; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_condition FOREIGN KEY (condition) REFERENCES product_attributes.conditions(note) ON DELETE SET NULL;


--
-- Name: products fk_template_tenant_products_decade; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_decade FOREIGN KEY (decade) REFERENCES product_attributes.decades(name_en) ON DELETE SET NULL;


--
-- Name: products fk_template_tenant_products_fit; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_fit FOREIGN KEY (fit) REFERENCES product_attributes.fits(name_en) ON DELETE SET NULL;


--
-- Name: products fk_template_tenant_products_gender; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_gender FOREIGN KEY (gender) REFERENCES product_attributes.genders(name_en) ON DELETE SET NULL;


--
-- Name: products fk_template_tenant_products_length; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_length FOREIGN KEY (length) REFERENCES product_attributes.lengths(name_en) ON DELETE SET NULL;


--
-- Name: products fk_template_tenant_products_neckline; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_neckline FOREIGN KEY (neckline) REFERENCES product_attributes.necklines(name_en) ON DELETE SET NULL;


--
-- Name: products fk_template_tenant_products_origin; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_origin FOREIGN KEY (origin) REFERENCES product_attributes.origins(name_en) ON DELETE SET NULL;


--
-- Name: products fk_template_tenant_products_pattern; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_pattern FOREIGN KEY (pattern) REFERENCES product_attributes.patterns(name_en) ON DELETE SET NULL;


--
-- Name: products fk_template_tenant_products_rise; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_rise FOREIGN KEY (rise) REFERENCES product_attributes.rises(name_en) ON DELETE SET NULL;


--
-- Name: products fk_template_tenant_products_season; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_season FOREIGN KEY (season) REFERENCES product_attributes.seasons(name_en) ON DELETE SET NULL;


--
-- Name: products fk_template_tenant_products_size; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_size FOREIGN KEY (size_normalized) REFERENCES product_attributes.sizes_normalized(name_en) ON DELETE SET NULL;


--
-- Name: products fk_template_tenant_products_sleeve_length; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_sleeve_length FOREIGN KEY (sleeve_length) REFERENCES product_attributes.sleeve_lengths(name_en) ON DELETE SET NULL;


--
-- Name: products fk_template_tenant_products_sport; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_sport FOREIGN KEY (sport) REFERENCES product_attributes.sports(name_en) ON DELETE SET NULL;


--
-- Name: products fk_template_tenant_products_trend; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.products
    ADD CONSTRAINT fk_template_tenant_products_trend FOREIGN KEY (trend) REFERENCES product_attributes.trends(name_en) ON DELETE SET NULL;


--
-- Name: vinted_products fk_template_vinted_products_product_id; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_products
    ADD CONSTRAINT fk_template_vinted_products_product_id FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: marketplace_jobs marketplace_jobs_action_type_id_fkey; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.marketplace_jobs
    ADD CONSTRAINT marketplace_jobs_action_type_id_fkey FOREIGN KEY (action_type_id) REFERENCES vinted.action_types(id);


--
-- Name: marketplace_jobs marketplace_jobs_product_id_fkey; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.marketplace_jobs
    ADD CONSTRAINT marketplace_jobs_product_id_fkey FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE SET NULL;


--
-- Name: marketplace_tasks marketplace_tasks_job_id_fkey; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.marketplace_tasks
    ADD CONSTRAINT marketplace_tasks_job_id_fkey FOREIGN KEY (job_id) REFERENCES template_tenant.marketplace_jobs(id) ON DELETE SET NULL;


--
-- Name: vinted_connection vinted_connection_user_id_fkey; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_connection
    ADD CONSTRAINT vinted_connection_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: vinted_error_logs vinted_error_logs_product_id_fkey; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_error_logs
    ADD CONSTRAINT vinted_error_logs_product_id_fkey FOREIGN KEY (product_id) REFERENCES template_tenant.products(id) ON DELETE CASCADE;


--
-- Name: vinted_job_stats vinted_job_stats_action_type_id_fkey; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_job_stats
    ADD CONSTRAINT vinted_job_stats_action_type_id_fkey FOREIGN KEY (action_type_id) REFERENCES vinted.action_types(id);


--
-- Name: vinted_messages vinted_messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: template_tenant; Owner: stoflow_user
--

ALTER TABLE ONLY template_tenant.vinted_messages
    ADD CONSTRAINT vinted_messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES template_tenant.vinted_conversations(conversation_id) ON DELETE CASCADE;


--
-- Name: ebay_orders_products ebay_orders_products_order_id_fkey; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_orders_products
    ADD CONSTRAINT ebay_orders_products_order_id_fkey FOREIGN KEY (order_id) REFERENCES user_1.ebay_orders(order_id) ON DELETE CASCADE;


--
-- Name: ebay_products_marketplace ebay_products_marketplace_product_id_fkey; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_products_marketplace
    ADD CONSTRAINT ebay_products_marketplace_product_id_fkey FOREIGN KEY (product_id) REFERENCES user_1.products(id) ON DELETE CASCADE;


--
-- Name: ebay_products ebay_products_product_id_fkey; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_products
    ADD CONSTRAINT ebay_products_product_id_fkey FOREIGN KEY (product_id) REFERENCES user_1.products(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: ebay_promoted_listings ebay_promoted_listings_product_id_fkey; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ebay_promoted_listings
    ADD CONSTRAINT ebay_promoted_listings_product_id_fkey FOREIGN KEY (product_id) REFERENCES user_1.products(id) ON DELETE CASCADE;


--
-- Name: ai_generation_logs fk_ai_generation_logs_product_id; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.ai_generation_logs
    ADD CONSTRAINT fk_ai_generation_logs_product_id FOREIGN KEY (product_id) REFERENCES user_1.products(id) ON DELETE CASCADE;


--
-- Name: batch_jobs fk_batch_jobs_user; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.batch_jobs
    ADD CONSTRAINT fk_batch_jobs_user FOREIGN KEY (created_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: marketplace_jobs fk_marketplace_jobs_batch_job; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.marketplace_jobs
    ADD CONSTRAINT fk_marketplace_jobs_batch_job FOREIGN KEY (batch_job_id) REFERENCES user_1.batch_jobs(id) ON DELETE SET NULL;


--
-- Name: marketplace_tasks fk_marketplace_tasks_job; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.marketplace_tasks
    ADD CONSTRAINT fk_marketplace_tasks_job FOREIGN KEY (job_id) REFERENCES user_1.marketplace_jobs(id) ON DELETE SET NULL;


--
-- Name: product_colors fk_product_colors_color; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.product_colors
    ADD CONSTRAINT fk_product_colors_color FOREIGN KEY (color) REFERENCES product_attributes.colors(name_en) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: product_colors fk_product_colors_product_id; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.product_colors
    ADD CONSTRAINT fk_product_colors_product_id FOREIGN KEY (product_id) REFERENCES user_1.products(id) ON DELETE CASCADE;


--
-- Name: product_condition_sups fk_product_condition_sups_condition_sup; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.product_condition_sups
    ADD CONSTRAINT fk_product_condition_sups_condition_sup FOREIGN KEY (condition_sup) REFERENCES product_attributes.condition_sups(name_en) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: product_condition_sups fk_product_condition_sups_product_id; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.product_condition_sups
    ADD CONSTRAINT fk_product_condition_sups_product_id FOREIGN KEY (product_id) REFERENCES user_1.products(id) ON DELETE CASCADE;


--
-- Name: product_images fk_product_images_product_id; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.product_images
    ADD CONSTRAINT fk_product_images_product_id FOREIGN KEY (product_id) REFERENCES user_1.products(id) ON DELETE CASCADE;


--
-- Name: product_materials fk_product_materials_material; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.product_materials
    ADD CONSTRAINT fk_product_materials_material FOREIGN KEY (material) REFERENCES product_attributes.materials(name_en) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: product_materials fk_product_materials_product_id; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.product_materials
    ADD CONSTRAINT fk_product_materials_product_id FOREIGN KEY (product_id) REFERENCES user_1.products(id) ON DELETE CASCADE;


--
-- Name: products fk_products_size_normalized; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_products_size_normalized FOREIGN KEY (size_normalized) REFERENCES product_attributes.sizes_normalized(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: products fk_products_stretch; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_products_stretch FOREIGN KEY (stretch) REFERENCES product_attributes.stretches(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: publication_history fk_publication_history_product_id; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.publication_history
    ADD CONSTRAINT fk_publication_history_product_id FOREIGN KEY (product_id) REFERENCES user_1.products(id) ON DELETE CASCADE;


--
-- Name: vinted_products fk_template_vinted_products_product_id; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_products
    ADD CONSTRAINT fk_template_vinted_products_product_id FOREIGN KEY (product_id) REFERENCES user_1.products(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_brand; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_brand FOREIGN KEY (brand) REFERENCES product_attributes.brands(name) ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_category; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_category FOREIGN KEY (category) REFERENCES product_attributes.categories(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_closure; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_closure FOREIGN KEY (closure) REFERENCES product_attributes.closures(name_en) ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_condition; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_condition FOREIGN KEY (condition) REFERENCES product_attributes.conditions(note) ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_decade; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_decade FOREIGN KEY (decade) REFERENCES product_attributes.decades(name_en) ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_fit; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_fit FOREIGN KEY (fit) REFERENCES product_attributes.fits(name_en) ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_gender; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_gender FOREIGN KEY (gender) REFERENCES product_attributes.genders(name_en) ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_length; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_length FOREIGN KEY (length) REFERENCES product_attributes.lengths(name_en) ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_neckline; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_neckline FOREIGN KEY (neckline) REFERENCES product_attributes.necklines(name_en) ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_origin; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_origin FOREIGN KEY (origin) REFERENCES product_attributes.origins(name_en) ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_pattern; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_pattern FOREIGN KEY (pattern) REFERENCES product_attributes.patterns(name_en) ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_rise; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_rise FOREIGN KEY (rise) REFERENCES product_attributes.rises(name_en) ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_season; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_season FOREIGN KEY (season) REFERENCES product_attributes.seasons(name_en) ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_size; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_size FOREIGN KEY (size_normalized) REFERENCES product_attributes.sizes_normalized(name_en) ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_sleeve_length; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_sleeve_length FOREIGN KEY (sleeve_length) REFERENCES product_attributes.sleeve_lengths(name_en) ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_sport; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_sport FOREIGN KEY (sport) REFERENCES product_attributes.sports(name_en) ON DELETE SET NULL;


--
-- Name: products fk_user_3_products_trend; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.products
    ADD CONSTRAINT fk_user_3_products_trend FOREIGN KEY (trend) REFERENCES product_attributes.trends(name_en) ON DELETE SET NULL;


--
-- Name: marketplace_jobs marketplace_jobs_action_type_id_fkey; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.marketplace_jobs
    ADD CONSTRAINT marketplace_jobs_action_type_id_fkey FOREIGN KEY (action_type_id) REFERENCES vinted.action_types(id);


--
-- Name: marketplace_jobs marketplace_jobs_product_id_fkey; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.marketplace_jobs
    ADD CONSTRAINT marketplace_jobs_product_id_fkey FOREIGN KEY (product_id) REFERENCES user_1.products(id) ON DELETE SET NULL;


--
-- Name: marketplace_tasks marketplace_tasks_job_id_fkey; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.marketplace_tasks
    ADD CONSTRAINT marketplace_tasks_job_id_fkey FOREIGN KEY (job_id) REFERENCES user_1.marketplace_jobs(id) ON DELETE SET NULL;


--
-- Name: vinted_connection vinted_connection_user_id_fkey; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_connection
    ADD CONSTRAINT vinted_connection_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: vinted_error_logs vinted_error_logs_product_id_fkey; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_error_logs
    ADD CONSTRAINT vinted_error_logs_product_id_fkey FOREIGN KEY (product_id) REFERENCES user_1.products(id) ON DELETE CASCADE;


--
-- Name: vinted_job_stats vinted_job_stats_action_type_id_fkey; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_job_stats
    ADD CONSTRAINT vinted_job_stats_action_type_id_fkey FOREIGN KEY (action_type_id) REFERENCES vinted.action_types(id);


--
-- Name: vinted_messages vinted_messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: user_1; Owner: stoflow_user
--

ALTER TABLE ONLY user_1.vinted_messages
    ADD CONSTRAINT vinted_messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES user_1.vinted_conversations(conversation_id) ON DELETE CASCADE;


--
-- Name: categories fk_vinted_categories_parent; Type: FK CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.categories
    ADD CONSTRAINT fk_vinted_categories_parent FOREIGN KEY (parent_id) REFERENCES vinted.categories(id) ON DELETE CASCADE;


--
-- Name: mapping fk_vinted_mapping_fit; Type: FK CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.mapping
    ADD CONSTRAINT fk_vinted_mapping_fit FOREIGN KEY (my_fit) REFERENCES product_attributes.fits(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: mapping fk_vinted_mapping_gender; Type: FK CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.mapping
    ADD CONSTRAINT fk_vinted_mapping_gender FOREIGN KEY (my_gender) REFERENCES product_attributes.genders(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: mapping fk_vinted_mapping_length; Type: FK CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.mapping
    ADD CONSTRAINT fk_vinted_mapping_length FOREIGN KEY (my_length) REFERENCES product_attributes.lengths(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: mapping fk_vinted_mapping_material; Type: FK CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.mapping
    ADD CONSTRAINT fk_vinted_mapping_material FOREIGN KEY (my_material) REFERENCES product_attributes.materials(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: mapping fk_vinted_mapping_neckline; Type: FK CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.mapping
    ADD CONSTRAINT fk_vinted_mapping_neckline FOREIGN KEY (my_neckline) REFERENCES product_attributes.necklines(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: mapping fk_vinted_mapping_pattern; Type: FK CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.mapping
    ADD CONSTRAINT fk_vinted_mapping_pattern FOREIGN KEY (my_pattern) REFERENCES product_attributes.patterns(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: mapping fk_vinted_mapping_rise; Type: FK CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.mapping
    ADD CONSTRAINT fk_vinted_mapping_rise FOREIGN KEY (my_rise) REFERENCES product_attributes.rises(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: mapping fk_vinted_mapping_sleeve_length; Type: FK CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.mapping
    ADD CONSTRAINT fk_vinted_mapping_sleeve_length FOREIGN KEY (my_sleeve_length) REFERENCES product_attributes.sleeve_lengths(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: mapping mapping_my_category_fkey; Type: FK CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.mapping
    ADD CONSTRAINT mapping_my_category_fkey FOREIGN KEY (my_category) REFERENCES product_attributes.categories(name_en) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: order_products order_products_transaction_id_fkey; Type: FK CONSTRAINT; Schema: vinted; Owner: stoflow_user
--

ALTER TABLE ONLY vinted.order_products
    ADD CONSTRAINT order_products_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES vinted.orders(transaction_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict QAugG7tPgQs6yLU5s12oyGoDWFUKA6ioUk77VYk2EKXsHgYmz9zGxo7CcCOkv0g

--
-- PostgreSQL database cluster dump complete
--

