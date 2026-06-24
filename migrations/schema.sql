--
-- PostgreSQL database dump
--

\restrict bV7hXatAvjJaAEnsfjxGLZ0oTBvvSkZl3fVI4w6cSFjb99ZhI7u9lPSgNbbXosQ

-- Dumped from database version 17.10
-- Dumped by pg_dump version 17.10

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: casos; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA casos;


ALTER SCHEMA casos OWNER TO postgres;

--
-- Name: entidades; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA entidades;


ALTER SCHEMA entidades OWNER TO postgres;

--
-- Name: personas; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA personas;


ALTER SCHEMA personas OWNER TO postgres;

--
-- Name: redes; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA redes;


ALTER SCHEMA redes OWNER TO postgres;

--
-- Name: sabanas; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA sabanas;


ALTER SCHEMA sabanas OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: caso; Type: TABLE; Schema: casos; Owner: postgres
--

CREATE TABLE casos.caso (
    id_caso bigint NOT NULL,
    nombre character varying(150) NOT NULL,
    descripcion text,
    id_usuario_creador bigint,
    estado character varying(50) DEFAULT 'activo'::character varying NOT NULL,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_modificacion timestamp without time zone
);


ALTER TABLE casos.caso OWNER TO postgres;

--
-- Name: caso_analisis; Type: TABLE; Schema: casos; Owner: postgres
--

CREATE TABLE casos.caso_analisis (
    id_caso_analisis bigint NOT NULL,
    id_caso bigint NOT NULL,
    id_analisis bigint NOT NULL,
    tipo_relacion character varying(100),
    observaciones text,
    fecha_vinculacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_modificacion timestamp without time zone
);


ALTER TABLE casos.caso_analisis OWNER TO postgres;

--
-- Name: caso_analisis_id_caso_analisis_seq; Type: SEQUENCE; Schema: casos; Owner: postgres
--

CREATE SEQUENCE casos.caso_analisis_id_caso_analisis_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE casos.caso_analisis_id_caso_analisis_seq OWNER TO postgres;

--
-- Name: caso_analisis_id_caso_analisis_seq; Type: SEQUENCE OWNED BY; Schema: casos; Owner: postgres
--

ALTER SEQUENCE casos.caso_analisis_id_caso_analisis_seq OWNED BY casos.caso_analisis.id_caso_analisis;


--
-- Name: caso_id_caso_seq; Type: SEQUENCE; Schema: casos; Owner: postgres
--

CREATE SEQUENCE casos.caso_id_caso_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE casos.caso_id_caso_seq OWNER TO postgres;

--
-- Name: caso_id_caso_seq; Type: SEQUENCE OWNED BY; Schema: casos; Owner: postgres
--

ALTER SEQUENCE casos.caso_id_caso_seq OWNED BY casos.caso.id_caso;


--
-- Name: caso_identidad_digital; Type: TABLE; Schema: casos; Owner: postgres
--

CREATE TABLE casos.caso_identidad_digital (
    id_caso_identidad_digital bigint NOT NULL,
    id_caso bigint NOT NULL,
    id_identidad_digital bigint NOT NULL,
    tipo_relacion character varying(100),
    estado character varying(50) DEFAULT 'activa'::character varying NOT NULL,
    observaciones text,
    fecha_vinculacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_modificacion timestamp without time zone
);


ALTER TABLE casos.caso_identidad_digital OWNER TO postgres;

--
-- Name: caso_identidad_digital_id_caso_identidad_digital_seq; Type: SEQUENCE; Schema: casos; Owner: postgres
--

CREATE SEQUENCE casos.caso_identidad_digital_id_caso_identidad_digital_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE casos.caso_identidad_digital_id_caso_identidad_digital_seq OWNER TO postgres;

--
-- Name: caso_identidad_digital_id_caso_identidad_digital_seq; Type: SEQUENCE OWNED BY; Schema: casos; Owner: postgres
--

ALTER SEQUENCE casos.caso_identidad_digital_id_caso_identidad_digital_seq OWNED BY casos.caso_identidad_digital.id_caso_identidad_digital;


--
-- Name: caso_persona; Type: TABLE; Schema: casos; Owner: postgres
--

CREATE TABLE casos.caso_persona (
    id_caso_persona bigint NOT NULL,
    id_caso bigint NOT NULL,
    id_persona bigint NOT NULL,
    tipo_relacion character varying(100),
    estado character varying(50) DEFAULT 'activa'::character varying NOT NULL,
    observaciones text,
    fecha_vinculacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_modificacion timestamp without time zone
);


ALTER TABLE casos.caso_persona OWNER TO postgres;

--
-- Name: caso_persona_id_caso_persona_seq; Type: SEQUENCE; Schema: casos; Owner: postgres
--

CREATE SEQUENCE casos.caso_persona_id_caso_persona_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE casos.caso_persona_id_caso_persona_seq OWNER TO postgres;

--
-- Name: caso_persona_id_caso_persona_seq; Type: SEQUENCE OWNED BY; Schema: casos; Owner: postgres
--

ALTER SEQUENCE casos.caso_persona_id_caso_persona_seq OWNED BY casos.caso_persona.id_caso_persona;


--
-- Name: colaborador_caso; Type: TABLE; Schema: casos; Owner: postgres
--

CREATE TABLE casos.colaborador_caso (
    id_colaborador_caso bigint NOT NULL,
    id_caso bigint NOT NULL,
    id_usuario bigint NOT NULL,
    rol_en_caso character varying(100),
    estado character varying(50) DEFAULT 'activo'::character varying NOT NULL,
    fecha_asignacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_modificacion timestamp without time zone
);


ALTER TABLE casos.colaborador_caso OWNER TO postgres;

--
-- Name: colaborador_caso_id_colaborador_caso_seq; Type: SEQUENCE; Schema: casos; Owner: postgres
--

CREATE SEQUENCE casos.colaborador_caso_id_colaborador_caso_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE casos.colaborador_caso_id_colaborador_caso_seq OWNER TO postgres;

--
-- Name: colaborador_caso_id_colaborador_caso_seq; Type: SEQUENCE OWNED BY; Schema: casos; Owner: postgres
--

ALTER SEQUENCE casos.colaborador_caso_id_colaborador_caso_seq OWNED BY casos.colaborador_caso.id_colaborador_caso;


--
-- Name: area; Type: TABLE; Schema: entidades; Owner: postgres
--

CREATE TABLE entidades.area (
    id_area bigint NOT NULL,
    nombre_area character varying(150) NOT NULL,
    id_organizacion bigint NOT NULL
);


ALTER TABLE entidades.area OWNER TO postgres;

--
-- Name: area_id_area_seq; Type: SEQUENCE; Schema: entidades; Owner: postgres
--

CREATE SEQUENCE entidades.area_id_area_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE entidades.area_id_area_seq OWNER TO postgres;

--
-- Name: area_id_area_seq; Type: SEQUENCE OWNED BY; Schema: entidades; Owner: postgres
--

ALTER SEQUENCE entidades.area_id_area_seq OWNED BY entidades.area.id_area;


--
-- Name: departamento; Type: TABLE; Schema: entidades; Owner: postgres
--

CREATE TABLE entidades.departamento (
    id_departamento bigint NOT NULL,
    nombre_departamento character varying(150) NOT NULL,
    id_area bigint NOT NULL,
    id_organizacion bigint NOT NULL
);


ALTER TABLE entidades.departamento OWNER TO postgres;

--
-- Name: departamento_id_departamento_seq; Type: SEQUENCE; Schema: entidades; Owner: postgres
--

CREATE SEQUENCE entidades.departamento_id_departamento_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE entidades.departamento_id_departamento_seq OWNER TO postgres;

--
-- Name: departamento_id_departamento_seq; Type: SEQUENCE OWNED BY; Schema: entidades; Owner: postgres
--

ALTER SEQUENCE entidades.departamento_id_departamento_seq OWNED BY entidades.departamento.id_departamento;


--
-- Name: organizacion; Type: TABLE; Schema: entidades; Owner: postgres
--

CREATE TABLE entidades.organizacion (
    id_organizacion bigint NOT NULL,
    nombre_organizacion character varying(150) NOT NULL
);


ALTER TABLE entidades.organizacion OWNER TO postgres;

--
-- Name: organizacion_id_organizacion_seq; Type: SEQUENCE; Schema: entidades; Owner: postgres
--

CREATE SEQUENCE entidades.organizacion_id_organizacion_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE entidades.organizacion_id_organizacion_seq OWNER TO postgres;

--
-- Name: organizacion_id_organizacion_seq; Type: SEQUENCE OWNED BY; Schema: entidades; Owner: postgres
--

ALTER SEQUENCE entidades.organizacion_id_organizacion_seq OWNED BY entidades.organizacion.id_organizacion;


--
-- Name: permiso; Type: TABLE; Schema: entidades; Owner: postgres
--

CREATE TABLE entidades.permiso (
    id_permiso bigint NOT NULL,
    codigo character varying(100) NOT NULL,
    descripcion text
);


ALTER TABLE entidades.permiso OWNER TO postgres;

--
-- Name: permiso_id_permiso_seq; Type: SEQUENCE; Schema: entidades; Owner: postgres
--

CREATE SEQUENCE entidades.permiso_id_permiso_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE entidades.permiso_id_permiso_seq OWNER TO postgres;

--
-- Name: permiso_id_permiso_seq; Type: SEQUENCE OWNED BY; Schema: entidades; Owner: postgres
--

ALTER SEQUENCE entidades.permiso_id_permiso_seq OWNED BY entidades.permiso.id_permiso;


--
-- Name: rol; Type: TABLE; Schema: entidades; Owner: postgres
--

CREATE TABLE entidades.rol (
    id_rol bigint NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text
);


ALTER TABLE entidades.rol OWNER TO postgres;

--
-- Name: rol_id_rol_seq; Type: SEQUENCE; Schema: entidades; Owner: postgres
--

CREATE SEQUENCE entidades.rol_id_rol_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE entidades.rol_id_rol_seq OWNER TO postgres;

--
-- Name: rol_id_rol_seq; Type: SEQUENCE OWNED BY; Schema: entidades; Owner: postgres
--

ALTER SEQUENCE entidades.rol_id_rol_seq OWNED BY entidades.rol.id_rol;


--
-- Name: rol_permiso; Type: TABLE; Schema: entidades; Owner: postgres
--

CREATE TABLE entidades.rol_permiso (
    id_rol_permiso bigint NOT NULL,
    id_rol bigint NOT NULL,
    id_permiso bigint NOT NULL
);


ALTER TABLE entidades.rol_permiso OWNER TO postgres;

--
-- Name: rol_permiso_id_rol_permiso_seq; Type: SEQUENCE; Schema: entidades; Owner: postgres
--

CREATE SEQUENCE entidades.rol_permiso_id_rol_permiso_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE entidades.rol_permiso_id_rol_permiso_seq OWNER TO postgres;

--
-- Name: rol_permiso_id_rol_permiso_seq; Type: SEQUENCE OWNED BY; Schema: entidades; Owner: postgres
--

ALTER SEQUENCE entidades.rol_permiso_id_rol_permiso_seq OWNED BY entidades.rol_permiso.id_rol_permiso;


--
-- Name: usuario; Type: TABLE; Schema: entidades; Owner: postgres
--

CREATE TABLE entidades.usuario (
    id_usuario bigint NOT NULL,
    nombre character varying(100) NOT NULL,
    apellido_paterno character varying(100),
    apellido_materno character varying(100),
    email character varying(150) NOT NULL,
    telefono character varying(20),
    password_hash text NOT NULL,
    id_organizacion bigint,
    id_area bigint,
    id_departamento bigint,
    change_password boolean DEFAULT true NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_modificacion timestamp without time zone
);


ALTER TABLE entidades.usuario OWNER TO postgres;

--
-- Name: usuario_id_usuario_seq; Type: SEQUENCE; Schema: entidades; Owner: postgres
--

CREATE SEQUENCE entidades.usuario_id_usuario_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE entidades.usuario_id_usuario_seq OWNER TO postgres;

--
-- Name: usuario_id_usuario_seq; Type: SEQUENCE OWNED BY; Schema: entidades; Owner: postgres
--

ALTER SEQUENCE entidades.usuario_id_usuario_seq OWNED BY entidades.usuario.id_usuario;


--
-- Name: usuario_rol; Type: TABLE; Schema: entidades; Owner: postgres
--

CREATE TABLE entidades.usuario_rol (
    id_usuario_rol bigint NOT NULL,
    id_usuario bigint NOT NULL,
    id_rol bigint NOT NULL
);


ALTER TABLE entidades.usuario_rol OWNER TO postgres;

--
-- Name: usuario_rol_id_usuario_rol_seq; Type: SEQUENCE; Schema: entidades; Owner: postgres
--

CREATE SEQUENCE entidades.usuario_rol_id_usuario_rol_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE entidades.usuario_rol_id_usuario_rol_seq OWNER TO postgres;

--
-- Name: usuario_rol_id_usuario_rol_seq; Type: SEQUENCE OWNED BY; Schema: entidades; Owner: postgres
--

ALTER SEQUENCE entidades.usuario_rol_id_usuario_rol_seq OWNED BY entidades.usuario_rol.id_usuario_rol;


--
-- Name: identidad_digital; Type: TABLE; Schema: personas; Owner: postgres
--

CREATE TABLE personas.identidad_digital (
    id_identidad_digital bigint NOT NULL,
    id_persona bigint,
    id_plataforma bigint NOT NULL,
    username character varying(150),
    usuario_url text,
    nombre_publico character varying(150),
    identificador_externo character varying(255),
    descripcion text,
    verificada boolean DEFAULT false,
    raw_json jsonb DEFAULT '{}'::jsonb,
    estado character varying(50) DEFAULT 'activa'::character varying NOT NULL,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_modificacion timestamp without time zone
);


ALTER TABLE personas.identidad_digital OWNER TO postgres;

--
-- Name: identidad_digital_id_identidad_digital_seq; Type: SEQUENCE; Schema: personas; Owner: postgres
--

CREATE SEQUENCE personas.identidad_digital_id_identidad_digital_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE personas.identidad_digital_id_identidad_digital_seq OWNER TO postgres;

--
-- Name: identidad_digital_id_identidad_digital_seq; Type: SEQUENCE OWNED BY; Schema: personas; Owner: postgres
--

ALTER SEQUENCE personas.identidad_digital_id_identidad_digital_seq OWNED BY personas.identidad_digital.id_identidad_digital;


--
-- Name: persona; Type: TABLE; Schema: personas; Owner: postgres
--

CREATE TABLE personas.persona (
    id_persona bigint NOT NULL,
    nombre character varying(100) NOT NULL,
    apellido_paterno character varying(90),
    apellido_materno character varying(90),
    curp character varying(18),
    rfc character varying(13),
    fecha_nacimiento date,
    tipo_sangre character varying(10),
    dato_adicional jsonb DEFAULT '{}'::jsonb,
    estado character varying(50) DEFAULT 'activa'::character varying NOT NULL,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_modificacion timestamp without time zone
);


ALTER TABLE personas.persona OWNER TO postgres;

--
-- Name: persona_id_persona_seq; Type: SEQUENCE; Schema: personas; Owner: postgres
--

CREATE SEQUENCE personas.persona_id_persona_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE personas.persona_id_persona_seq OWNER TO postgres;

--
-- Name: persona_id_persona_seq; Type: SEQUENCE OWNED BY; Schema: personas; Owner: postgres
--

ALTER SEQUENCE personas.persona_id_persona_seq OWNED BY personas.persona.id_persona;


--
-- Name: analisis; Type: TABLE; Schema: redes; Owner: postgres
--

CREATE TABLE redes.analisis (
    id_analisis bigint NOT NULL,
    id_identidad_digital_objetivo bigint,
    id_usuario_ejecutor bigint,
    tipo_analisis character varying(100) NOT NULL,
    estado character varying(50) DEFAULT 'pendiente'::character varying NOT NULL,
    parametros jsonb DEFAULT '{}'::jsonb,
    resultado jsonb DEFAULT '{}'::jsonb,
    error text,
    fecha_inicio timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_fin timestamp without time zone,
    fecha_modificacion timestamp without time zone
);


ALTER TABLE redes.analisis OWNER TO postgres;

--
-- Name: analisis_id_analisis_seq; Type: SEQUENCE; Schema: redes; Owner: postgres
--

CREATE SEQUENCE redes.analisis_id_analisis_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE redes.analisis_id_analisis_seq OWNER TO postgres;

--
-- Name: analisis_id_analisis_seq; Type: SEQUENCE OWNED BY; Schema: redes; Owner: postgres
--

ALTER SEQUENCE redes.analisis_id_analisis_seq OWNED BY redes.analisis.id_analisis;


--
-- Name: comentario; Type: TABLE; Schema: redes; Owner: postgres
--

CREATE TABLE redes.comentario (
    id_comentario bigint NOT NULL,
    id_analisis bigint,
    id_publicacion bigint NOT NULL,
    id_plataforma bigint NOT NULL,
    id_identidad_autor bigint,
    identificador_externo character varying(255),
    texto text,
    fecha_comentario timestamp without time zone,
    raw_json jsonb DEFAULT '{}'::jsonb,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_modificacion timestamp without time zone
);


ALTER TABLE redes.comentario OWNER TO postgres;

--
-- Name: comentario_id_comentario_seq; Type: SEQUENCE; Schema: redes; Owner: postgres
--

CREATE SEQUENCE redes.comentario_id_comentario_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE redes.comentario_id_comentario_seq OWNER TO postgres;

--
-- Name: comentario_id_comentario_seq; Type: SEQUENCE OWNED BY; Schema: redes; Owner: postgres
--

ALTER SEQUENCE redes.comentario_id_comentario_seq OWNED BY redes.comentario.id_comentario;


--
-- Name: compartido; Type: TABLE; Schema: redes; Owner: postgres
--

CREATE TABLE redes.compartido (
    id_compartido bigint NOT NULL,
    id_analisis bigint,
    id_publicacion_original bigint NOT NULL,
    id_identidad_que_comparte bigint,
    id_publicacion_generada bigint,
    texto text,
    fecha_compartido timestamp without time zone,
    raw_json jsonb DEFAULT '{}'::jsonb,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE redes.compartido OWNER TO postgres;

--
-- Name: compartido_id_compartido_seq; Type: SEQUENCE; Schema: redes; Owner: postgres
--

CREATE SEQUENCE redes.compartido_id_compartido_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE redes.compartido_id_compartido_seq OWNER TO postgres;

--
-- Name: compartido_id_compartido_seq; Type: SEQUENCE OWNED BY; Schema: redes; Owner: postgres
--

ALTER SEQUENCE redes.compartido_id_compartido_seq OWNED BY redes.compartido.id_compartido;


--
-- Name: plataforma; Type: TABLE; Schema: redes; Owner: postgres
--

CREATE TABLE redes.plataforma (
    id_plataforma bigint NOT NULL,
    codigo character varying(50) NOT NULL,
    nombre character varying(100) NOT NULL,
    url_base text,
    activo boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_modificacion timestamp without time zone
);


ALTER TABLE redes.plataforma OWNER TO postgres;

--
-- Name: plataforma_id_plataforma_seq; Type: SEQUENCE; Schema: redes; Owner: postgres
--

CREATE SEQUENCE redes.plataforma_id_plataforma_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE redes.plataforma_id_plataforma_seq OWNER TO postgres;

--
-- Name: plataforma_id_plataforma_seq; Type: SEQUENCE OWNED BY; Schema: redes; Owner: postgres
--

ALTER SEQUENCE redes.plataforma_id_plataforma_seq OWNED BY redes.plataforma.id_plataforma;


--
-- Name: publicacion; Type: TABLE; Schema: redes; Owner: postgres
--

CREATE TABLE redes.publicacion (
    id_publicacion bigint NOT NULL,
    id_analisis bigint,
    id_plataforma bigint NOT NULL,
    id_identidad_autor bigint,
    identificador_externo character varying(255),
    url text,
    tipo_publicacion character varying(50),
    texto text,
    fecha_publicacion timestamp without time zone,
    raw_json jsonb DEFAULT '{}'::jsonb,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_modificacion timestamp without time zone
);


ALTER TABLE redes.publicacion OWNER TO postgres;

--
-- Name: publicacion_id_publicacion_seq; Type: SEQUENCE; Schema: redes; Owner: postgres
--

CREATE SEQUENCE redes.publicacion_id_publicacion_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE redes.publicacion_id_publicacion_seq OWNER TO postgres;

--
-- Name: publicacion_id_publicacion_seq; Type: SEQUENCE OWNED BY; Schema: redes; Owner: postgres
--

ALTER SEQUENCE redes.publicacion_id_publicacion_seq OWNED BY redes.publicacion.id_publicacion;


--
-- Name: publicacion_multimedia; Type: TABLE; Schema: redes; Owner: postgres
--

CREATE TABLE redes.publicacion_multimedia (
    id_publicacion_multimedia bigint NOT NULL,
    id_publicacion bigint NOT NULL,
    tipo_multimedia character varying(50),
    url_original text,
    ruta_local text,
    hash_archivo character varying(255),
    metadata jsonb DEFAULT '{}'::jsonb,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE redes.publicacion_multimedia OWNER TO postgres;

--
-- Name: publicacion_multimedia_id_publicacion_multimedia_seq; Type: SEQUENCE; Schema: redes; Owner: postgres
--

CREATE SEQUENCE redes.publicacion_multimedia_id_publicacion_multimedia_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE redes.publicacion_multimedia_id_publicacion_multimedia_seq OWNER TO postgres;

--
-- Name: publicacion_multimedia_id_publicacion_multimedia_seq; Type: SEQUENCE OWNED BY; Schema: redes; Owner: postgres
--

ALTER SEQUENCE redes.publicacion_multimedia_id_publicacion_multimedia_seq OWNED BY redes.publicacion_multimedia.id_publicacion_multimedia;


--
-- Name: reaccion; Type: TABLE; Schema: redes; Owner: postgres
--

CREATE TABLE redes.reaccion (
    id_reaccion bigint NOT NULL,
    id_analisis bigint,
    id_plataforma bigint NOT NULL,
    id_publicacion bigint,
    id_comentario bigint,
    id_identidad_autor bigint,
    tipo_reaccion character varying(50) NOT NULL,
    fecha_reaccion timestamp without time zone,
    raw_json jsonb DEFAULT '{}'::jsonb,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_reaccion_objetivo CHECK ((((id_publicacion IS NOT NULL) AND (id_comentario IS NULL)) OR ((id_publicacion IS NULL) AND (id_comentario IS NOT NULL))))
);


ALTER TABLE redes.reaccion OWNER TO postgres;

--
-- Name: reaccion_id_reaccion_seq; Type: SEQUENCE; Schema: redes; Owner: postgres
--

CREATE SEQUENCE redes.reaccion_id_reaccion_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE redes.reaccion_id_reaccion_seq OWNER TO postgres;

--
-- Name: reaccion_id_reaccion_seq; Type: SEQUENCE OWNED BY; Schema: redes; Owner: postgres
--

ALTER SEQUENCE redes.reaccion_id_reaccion_seq OWNED BY redes.reaccion.id_reaccion;


--
-- Name: tipo_vinculo_social; Type: TABLE; Schema: redes; Owner: postgres
--

CREATE TABLE redes.tipo_vinculo_social (
    id_tipo_vinculo bigint NOT NULL,
    codigo character varying(50) NOT NULL,
    descripcion text,
    direccional boolean DEFAULT true NOT NULL
);


ALTER TABLE redes.tipo_vinculo_social OWNER TO postgres;

--
-- Name: tipo_vinculo_social_id_tipo_vinculo_seq; Type: SEQUENCE; Schema: redes; Owner: postgres
--

CREATE SEQUENCE redes.tipo_vinculo_social_id_tipo_vinculo_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE redes.tipo_vinculo_social_id_tipo_vinculo_seq OWNER TO postgres;

--
-- Name: tipo_vinculo_social_id_tipo_vinculo_seq; Type: SEQUENCE OWNED BY; Schema: redes; Owner: postgres
--

ALTER SEQUENCE redes.tipo_vinculo_social_id_tipo_vinculo_seq OWNED BY redes.tipo_vinculo_social.id_tipo_vinculo;


--
-- Name: vinculo_social; Type: TABLE; Schema: redes; Owner: postgres
--

CREATE TABLE redes.vinculo_social (
    id_vinculo_social bigint NOT NULL,
    id_analisis bigint NOT NULL,
    id_identidad_origen bigint NOT NULL,
    id_identidad_destino bigint NOT NULL,
    id_tipo_vinculo bigint NOT NULL,
    fecha_observacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    vigente boolean DEFAULT true,
    raw_json jsonb DEFAULT '{}'::jsonb,
    CONSTRAINT chk_vinculo_no_mismo_perfil CHECK ((id_identidad_origen <> id_identidad_destino))
);


ALTER TABLE redes.vinculo_social OWNER TO postgres;

--
-- Name: vinculo_social_id_vinculo_social_seq; Type: SEQUENCE; Schema: redes; Owner: postgres
--

CREATE SEQUENCE redes.vinculo_social_id_vinculo_social_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE redes.vinculo_social_id_vinculo_social_seq OWNER TO postgres;

--
-- Name: vinculo_social_id_vinculo_social_seq; Type: SEQUENCE OWNED BY; Schema: redes; Owner: postgres
--

ALTER SEQUENCE redes.vinculo_social_id_vinculo_social_seq OWNED BY redes.vinculo_social.id_vinculo_social;


--
-- Name: compania_telefonica; Type: TABLE; Schema: sabanas; Owner: postgres
--

CREATE TABLE sabanas.compania_telefonica (
    id_compania_tel bigint NOT NULL,
    nombre_compania_tel character varying(30) NOT NULL
);


ALTER TABLE sabanas.compania_telefonica OWNER TO postgres;

--
-- Name: compania_telefonica_id_compania_tel_seq; Type: SEQUENCE; Schema: sabanas; Owner: postgres
--

CREATE SEQUENCE sabanas.compania_telefonica_id_compania_tel_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE sabanas.compania_telefonica_id_compania_tel_seq OWNER TO postgres;

--
-- Name: compania_telefonica_id_compania_tel_seq; Type: SEQUENCE OWNED BY; Schema: sabanas; Owner: postgres
--

ALTER SEQUENCE sabanas.compania_telefonica_id_compania_tel_seq OWNED BY sabanas.compania_telefonica.id_compania_tel;


--
-- Name: imeis; Type: TABLE; Schema: sabanas; Owner: postgres
--

CREATE TABLE sabanas.imeis (
    id_imei bigint NOT NULL,
    imei character varying(22) NOT NULL,
    serie character varying(30),
    modelo_equipo text
);


ALTER TABLE sabanas.imeis OWNER TO postgres;

--
-- Name: imeis_id_imei_seq; Type: SEQUENCE; Schema: sabanas; Owner: postgres
--

CREATE SEQUENCE sabanas.imeis_id_imei_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE sabanas.imeis_id_imei_seq OWNER TO postgres;

--
-- Name: imeis_id_imei_seq; Type: SEQUENCE OWNED BY; Schema: sabanas; Owner: postgres
--

ALTER SEQUENCE sabanas.imeis_id_imei_seq OWNED BY sabanas.imeis.id_imei;


--
-- Name: imsis; Type: TABLE; Schema: sabanas; Owner: postgres
--

CREATE TABLE sabanas.imsis (
    id_imsi bigint NOT NULL,
    imsi character varying(20) NOT NULL
);


ALTER TABLE sabanas.imsis OWNER TO postgres;

--
-- Name: imsis_id_imsi_seq; Type: SEQUENCE; Schema: sabanas; Owner: postgres
--

CREATE SEQUENCE sabanas.imsis_id_imsi_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE sabanas.imsis_id_imsi_seq OWNER TO postgres;

--
-- Name: imsis_id_imsi_seq; Type: SEQUENCE OWNED BY; Schema: sabanas; Owner: postgres
--

ALTER SEQUENCE sabanas.imsis_id_imsi_seq OWNED BY sabanas.imsis.id_imsi;


--
-- Name: numero_telefonico; Type: TABLE; Schema: sabanas; Owner: postgres
--

CREATE TABLE sabanas.numero_telefonico (
    id_numero_telefonico bigint NOT NULL,
    numero character varying(20) NOT NULL,
    id_compania_tel bigint,
    codigo_area character varying(10)
);


ALTER TABLE sabanas.numero_telefonico OWNER TO postgres;

--
-- Name: numero_telefonico_id_numero_telefonico_seq; Type: SEQUENCE; Schema: sabanas; Owner: postgres
--

CREATE SEQUENCE sabanas.numero_telefonico_id_numero_telefonico_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE sabanas.numero_telefonico_id_numero_telefonico_seq OWNER TO postgres;

--
-- Name: numero_telefonico_id_numero_telefonico_seq; Type: SEQUENCE OWNED BY; Schema: sabanas; Owner: postgres
--

ALTER SEQUENCE sabanas.numero_telefonico_id_numero_telefonico_seq OWNED BY sabanas.numero_telefonico.id_numero_telefonico;


--
-- Name: sabana; Type: TABLE; Schema: sabanas; Owner: postgres
--

CREATE TABLE sabanas.sabana (
    id_sabana bigint NOT NULL,
    id_numero_telefonico bigint NOT NULL,
    id_caso bigint NOT NULL,
    estado character varying(50) DEFAULT 'activa'::character varying NOT NULL,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_modificacion timestamp without time zone
);


ALTER TABLE sabanas.sabana OWNER TO postgres;

--
-- Name: sabana_analizada; Type: TABLE; Schema: sabanas; Owner: postgres
--

CREATE TABLE sabanas.sabana_analizada (
    id_sabana_analizada bigint NOT NULL,
    id_sabana bigint NOT NULL,
    id_sabana_cargada bigint,
    numero_a character varying(20),
    numero_b character varying(20),
    id_tipo_registro bigint,
    id_imei bigint,
    id_imsi bigint,
    duracion integer,
    latitud numeric(10,7),
    longitud numeric(10,7),
    azimuth numeric(6,2),
    altitud numeric(10,2),
    fecha_analisis timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE sabanas.sabana_analizada OWNER TO postgres;

--
-- Name: sabana_analizada_id_sabana_analizada_seq; Type: SEQUENCE; Schema: sabanas; Owner: postgres
--

CREATE SEQUENCE sabanas.sabana_analizada_id_sabana_analizada_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE sabanas.sabana_analizada_id_sabana_analizada_seq OWNER TO postgres;

--
-- Name: sabana_analizada_id_sabana_analizada_seq; Type: SEQUENCE OWNED BY; Schema: sabanas; Owner: postgres
--

ALTER SEQUENCE sabanas.sabana_analizada_id_sabana_analizada_seq OWNED BY sabanas.sabana_analizada.id_sabana_analizada;


--
-- Name: sabana_cargada; Type: TABLE; Schema: sabanas; Owner: postgres
--

CREATE TABLE sabanas.sabana_cargada (
    id_sabana_cargada bigint NOT NULL,
    id_sabana bigint NOT NULL,
    ruta text NOT NULL,
    estado character varying(50) DEFAULT 'cargada'::character varying NOT NULL,
    fecha_carga timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_modificacion timestamp without time zone
);


ALTER TABLE sabanas.sabana_cargada OWNER TO postgres;

--
-- Name: sabana_cargada_id_sabana_cargada_seq; Type: SEQUENCE; Schema: sabanas; Owner: postgres
--

CREATE SEQUENCE sabanas.sabana_cargada_id_sabana_cargada_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE sabanas.sabana_cargada_id_sabana_cargada_seq OWNER TO postgres;

--
-- Name: sabana_cargada_id_sabana_cargada_seq; Type: SEQUENCE OWNED BY; Schema: sabanas; Owner: postgres
--

ALTER SEQUENCE sabanas.sabana_cargada_id_sabana_cargada_seq OWNED BY sabanas.sabana_cargada.id_sabana_cargada;


--
-- Name: sabana_id_sabana_seq; Type: SEQUENCE; Schema: sabanas; Owner: postgres
--

CREATE SEQUENCE sabanas.sabana_id_sabana_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE sabanas.sabana_id_sabana_seq OWNER TO postgres;

--
-- Name: sabana_id_sabana_seq; Type: SEQUENCE OWNED BY; Schema: sabanas; Owner: postgres
--

ALTER SEQUENCE sabanas.sabana_id_sabana_seq OWNED BY sabanas.sabana.id_sabana;


--
-- Name: tipo_registro; Type: TABLE; Schema: sabanas; Owner: postgres
--

CREATE TABLE sabanas.tipo_registro (
    id_tipo_registro bigint NOT NULL,
    tipo character varying(100) NOT NULL,
    descripcion text
);


ALTER TABLE sabanas.tipo_registro OWNER TO postgres;

--
-- Name: tipo_registro_id_tipo_registro_seq; Type: SEQUENCE; Schema: sabanas; Owner: postgres
--

CREATE SEQUENCE sabanas.tipo_registro_id_tipo_registro_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE sabanas.tipo_registro_id_tipo_registro_seq OWNER TO postgres;

--
-- Name: tipo_registro_id_tipo_registro_seq; Type: SEQUENCE OWNED BY; Schema: sabanas; Owner: postgres
--

ALTER SEQUENCE sabanas.tipo_registro_id_tipo_registro_seq OWNED BY sabanas.tipo_registro.id_tipo_registro;


--
-- Name: caso id_caso; Type: DEFAULT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso ALTER COLUMN id_caso SET DEFAULT nextval('casos.caso_id_caso_seq'::regclass);


--
-- Name: caso_analisis id_caso_analisis; Type: DEFAULT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso_analisis ALTER COLUMN id_caso_analisis SET DEFAULT nextval('casos.caso_analisis_id_caso_analisis_seq'::regclass);


--
-- Name: caso_identidad_digital id_caso_identidad_digital; Type: DEFAULT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso_identidad_digital ALTER COLUMN id_caso_identidad_digital SET DEFAULT nextval('casos.caso_identidad_digital_id_caso_identidad_digital_seq'::regclass);


--
-- Name: caso_persona id_caso_persona; Type: DEFAULT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso_persona ALTER COLUMN id_caso_persona SET DEFAULT nextval('casos.caso_persona_id_caso_persona_seq'::regclass);


--
-- Name: colaborador_caso id_colaborador_caso; Type: DEFAULT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.colaborador_caso ALTER COLUMN id_colaborador_caso SET DEFAULT nextval('casos.colaborador_caso_id_colaborador_caso_seq'::regclass);


--
-- Name: area id_area; Type: DEFAULT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.area ALTER COLUMN id_area SET DEFAULT nextval('entidades.area_id_area_seq'::regclass);


--
-- Name: departamento id_departamento; Type: DEFAULT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.departamento ALTER COLUMN id_departamento SET DEFAULT nextval('entidades.departamento_id_departamento_seq'::regclass);


--
-- Name: organizacion id_organizacion; Type: DEFAULT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.organizacion ALTER COLUMN id_organizacion SET DEFAULT nextval('entidades.organizacion_id_organizacion_seq'::regclass);


--
-- Name: permiso id_permiso; Type: DEFAULT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.permiso ALTER COLUMN id_permiso SET DEFAULT nextval('entidades.permiso_id_permiso_seq'::regclass);


--
-- Name: rol id_rol; Type: DEFAULT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.rol ALTER COLUMN id_rol SET DEFAULT nextval('entidades.rol_id_rol_seq'::regclass);


--
-- Name: rol_permiso id_rol_permiso; Type: DEFAULT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.rol_permiso ALTER COLUMN id_rol_permiso SET DEFAULT nextval('entidades.rol_permiso_id_rol_permiso_seq'::regclass);


--
-- Name: usuario id_usuario; Type: DEFAULT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.usuario ALTER COLUMN id_usuario SET DEFAULT nextval('entidades.usuario_id_usuario_seq'::regclass);


--
-- Name: usuario_rol id_usuario_rol; Type: DEFAULT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.usuario_rol ALTER COLUMN id_usuario_rol SET DEFAULT nextval('entidades.usuario_rol_id_usuario_rol_seq'::regclass);


--
-- Name: identidad_digital id_identidad_digital; Type: DEFAULT; Schema: personas; Owner: postgres
--

ALTER TABLE ONLY personas.identidad_digital ALTER COLUMN id_identidad_digital SET DEFAULT nextval('personas.identidad_digital_id_identidad_digital_seq'::regclass);


--
-- Name: persona id_persona; Type: DEFAULT; Schema: personas; Owner: postgres
--

ALTER TABLE ONLY personas.persona ALTER COLUMN id_persona SET DEFAULT nextval('personas.persona_id_persona_seq'::regclass);


--
-- Name: analisis id_analisis; Type: DEFAULT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.analisis ALTER COLUMN id_analisis SET DEFAULT nextval('redes.analisis_id_analisis_seq'::regclass);


--
-- Name: comentario id_comentario; Type: DEFAULT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.comentario ALTER COLUMN id_comentario SET DEFAULT nextval('redes.comentario_id_comentario_seq'::regclass);


--
-- Name: compartido id_compartido; Type: DEFAULT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.compartido ALTER COLUMN id_compartido SET DEFAULT nextval('redes.compartido_id_compartido_seq'::regclass);


--
-- Name: plataforma id_plataforma; Type: DEFAULT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.plataforma ALTER COLUMN id_plataforma SET DEFAULT nextval('redes.plataforma_id_plataforma_seq'::regclass);


--
-- Name: publicacion id_publicacion; Type: DEFAULT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.publicacion ALTER COLUMN id_publicacion SET DEFAULT nextval('redes.publicacion_id_publicacion_seq'::regclass);


--
-- Name: publicacion_multimedia id_publicacion_multimedia; Type: DEFAULT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.publicacion_multimedia ALTER COLUMN id_publicacion_multimedia SET DEFAULT nextval('redes.publicacion_multimedia_id_publicacion_multimedia_seq'::regclass);


--
-- Name: reaccion id_reaccion; Type: DEFAULT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.reaccion ALTER COLUMN id_reaccion SET DEFAULT nextval('redes.reaccion_id_reaccion_seq'::regclass);


--
-- Name: tipo_vinculo_social id_tipo_vinculo; Type: DEFAULT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.tipo_vinculo_social ALTER COLUMN id_tipo_vinculo SET DEFAULT nextval('redes.tipo_vinculo_social_id_tipo_vinculo_seq'::regclass);


--
-- Name: vinculo_social id_vinculo_social; Type: DEFAULT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.vinculo_social ALTER COLUMN id_vinculo_social SET DEFAULT nextval('redes.vinculo_social_id_vinculo_social_seq'::regclass);


--
-- Name: compania_telefonica id_compania_tel; Type: DEFAULT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.compania_telefonica ALTER COLUMN id_compania_tel SET DEFAULT nextval('sabanas.compania_telefonica_id_compania_tel_seq'::regclass);


--
-- Name: imeis id_imei; Type: DEFAULT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.imeis ALTER COLUMN id_imei SET DEFAULT nextval('sabanas.imeis_id_imei_seq'::regclass);


--
-- Name: imsis id_imsi; Type: DEFAULT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.imsis ALTER COLUMN id_imsi SET DEFAULT nextval('sabanas.imsis_id_imsi_seq'::regclass);


--
-- Name: numero_telefonico id_numero_telefonico; Type: DEFAULT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.numero_telefonico ALTER COLUMN id_numero_telefonico SET DEFAULT nextval('sabanas.numero_telefonico_id_numero_telefonico_seq'::regclass);


--
-- Name: sabana id_sabana; Type: DEFAULT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.sabana ALTER COLUMN id_sabana SET DEFAULT nextval('sabanas.sabana_id_sabana_seq'::regclass);


--
-- Name: sabana_analizada id_sabana_analizada; Type: DEFAULT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.sabana_analizada ALTER COLUMN id_sabana_analizada SET DEFAULT nextval('sabanas.sabana_analizada_id_sabana_analizada_seq'::regclass);


--
-- Name: sabana_cargada id_sabana_cargada; Type: DEFAULT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.sabana_cargada ALTER COLUMN id_sabana_cargada SET DEFAULT nextval('sabanas.sabana_cargada_id_sabana_cargada_seq'::regclass);


--
-- Name: tipo_registro id_tipo_registro; Type: DEFAULT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.tipo_registro ALTER COLUMN id_tipo_registro SET DEFAULT nextval('sabanas.tipo_registro_id_tipo_registro_seq'::regclass);


--
-- Data for Name: caso; Type: TABLE DATA; Schema: casos; Owner: postgres
--

COPY casos.caso (id_caso, nombre, descripcion, id_usuario_creador, estado, fecha_creacion, fecha_modificacion) FROM stdin;
\.


--
-- Data for Name: caso_analisis; Type: TABLE DATA; Schema: casos; Owner: postgres
--

COPY casos.caso_analisis (id_caso_analisis, id_caso, id_analisis, tipo_relacion, observaciones, fecha_vinculacion, fecha_modificacion) FROM stdin;
\.


--
-- Data for Name: caso_identidad_digital; Type: TABLE DATA; Schema: casos; Owner: postgres
--

COPY casos.caso_identidad_digital (id_caso_identidad_digital, id_caso, id_identidad_digital, tipo_relacion, estado, observaciones, fecha_vinculacion, fecha_modificacion) FROM stdin;
\.


--
-- Data for Name: caso_persona; Type: TABLE DATA; Schema: casos; Owner: postgres
--

COPY casos.caso_persona (id_caso_persona, id_caso, id_persona, tipo_relacion, estado, observaciones, fecha_vinculacion, fecha_modificacion) FROM stdin;
\.


--
-- Data for Name: colaborador_caso; Type: TABLE DATA; Schema: casos; Owner: postgres
--

COPY casos.colaborador_caso (id_colaborador_caso, id_caso, id_usuario, rol_en_caso, estado, fecha_asignacion, fecha_modificacion) FROM stdin;
\.


--
-- Data for Name: area; Type: TABLE DATA; Schema: entidades; Owner: postgres
--

COPY entidades.area (id_area, nombre_area, id_organizacion) FROM stdin;
1	IT	1
2	Recursos Humanos	1
\.


--
-- Data for Name: departamento; Type: TABLE DATA; Schema: entidades; Owner: postgres
--

COPY entidades.departamento (id_departamento, nombre_departamento, id_area, id_organizacion) FROM stdin;
1	Desarrollo	1	1
\.


--
-- Data for Name: organizacion; Type: TABLE DATA; Schema: entidades; Owner: postgres
--

COPY entidades.organizacion (id_organizacion, nombre_organizacion) FROM stdin;
1	RyR
2	Datelis
\.


--
-- Data for Name: permiso; Type: TABLE DATA; Schema: entidades; Owner: postgres
--

COPY entidades.permiso (id_permiso, codigo, descripcion) FROM stdin;
\.


--
-- Data for Name: rol; Type: TABLE DATA; Schema: entidades; Owner: postgres
--

COPY entidades.rol (id_rol, nombre, descripcion) FROM stdin;
\.


--
-- Data for Name: rol_permiso; Type: TABLE DATA; Schema: entidades; Owner: postgres
--

COPY entidades.rol_permiso (id_rol_permiso, id_rol, id_permiso) FROM stdin;
\.


--
-- Data for Name: usuario; Type: TABLE DATA; Schema: entidades; Owner: postgres
--

COPY entidades.usuario (id_usuario, nombre, apellido_paterno, apellido_materno, email, telefono, password_hash, id_organizacion, id_area, id_departamento, change_password, activo, fecha_creacion, fecha_modificacion) FROM stdin;
1	Eduardo	Martinez	Guerrero	eduardo.mg2309@gmail.com	1234567890	$2a$11$Edk8FY7FHgZLfezr.elnNefAJD4OkIkgMlNP0Zpeet0U79m3OR.c6	1	1	1	t	t	2026-06-18 15:46:28.836529	\N
\.


--
-- Data for Name: usuario_rol; Type: TABLE DATA; Schema: entidades; Owner: postgres
--

COPY entidades.usuario_rol (id_usuario_rol, id_usuario, id_rol) FROM stdin;
\.


--
-- Data for Name: identidad_digital; Type: TABLE DATA; Schema: personas; Owner: postgres
--

COPY personas.identidad_digital (id_identidad_digital, id_persona, id_plataforma, username, usuario_url, nombre_publico, identificador_externo, descripcion, verificada, raw_json, estado, fecha_creacion, fecha_modificacion) FROM stdin;
\.


--
-- Data for Name: persona; Type: TABLE DATA; Schema: personas; Owner: postgres
--

COPY personas.persona (id_persona, nombre, apellido_paterno, apellido_materno, curp, rfc, fecha_nacimiento, tipo_sangre, dato_adicional, estado, fecha_creacion, fecha_modificacion) FROM stdin;
\.


--
-- Data for Name: analisis; Type: TABLE DATA; Schema: redes; Owner: postgres
--

COPY redes.analisis (id_analisis, id_identidad_digital_objetivo, id_usuario_ejecutor, tipo_analisis, estado, parametros, resultado, error, fecha_inicio, fecha_fin, fecha_modificacion) FROM stdin;
\.


--
-- Data for Name: comentario; Type: TABLE DATA; Schema: redes; Owner: postgres
--

COPY redes.comentario (id_comentario, id_analisis, id_publicacion, id_plataforma, id_identidad_autor, identificador_externo, texto, fecha_comentario, raw_json, fecha_creacion, fecha_modificacion) FROM stdin;
\.


--
-- Data for Name: compartido; Type: TABLE DATA; Schema: redes; Owner: postgres
--

COPY redes.compartido (id_compartido, id_analisis, id_publicacion_original, id_identidad_que_comparte, id_publicacion_generada, texto, fecha_compartido, raw_json, fecha_creacion) FROM stdin;
\.


--
-- Data for Name: plataforma; Type: TABLE DATA; Schema: redes; Owner: postgres
--

COPY redes.plataforma (id_plataforma, codigo, nombre, url_base, activo, fecha_creacion, fecha_modificacion) FROM stdin;
\.


--
-- Data for Name: publicacion; Type: TABLE DATA; Schema: redes; Owner: postgres
--

COPY redes.publicacion (id_publicacion, id_analisis, id_plataforma, id_identidad_autor, identificador_externo, url, tipo_publicacion, texto, fecha_publicacion, raw_json, fecha_creacion, fecha_modificacion) FROM stdin;
\.


--
-- Data for Name: publicacion_multimedia; Type: TABLE DATA; Schema: redes; Owner: postgres
--

COPY redes.publicacion_multimedia (id_publicacion_multimedia, id_publicacion, tipo_multimedia, url_original, ruta_local, hash_archivo, metadata, fecha_creacion) FROM stdin;
\.


--
-- Data for Name: reaccion; Type: TABLE DATA; Schema: redes; Owner: postgres
--

COPY redes.reaccion (id_reaccion, id_analisis, id_plataforma, id_publicacion, id_comentario, id_identidad_autor, tipo_reaccion, fecha_reaccion, raw_json, fecha_creacion) FROM stdin;
\.


--
-- Data for Name: tipo_vinculo_social; Type: TABLE DATA; Schema: redes; Owner: postgres
--

COPY redes.tipo_vinculo_social (id_tipo_vinculo, codigo, descripcion, direccional) FROM stdin;
\.


--
-- Data for Name: vinculo_social; Type: TABLE DATA; Schema: redes; Owner: postgres
--

COPY redes.vinculo_social (id_vinculo_social, id_analisis, id_identidad_origen, id_identidad_destino, id_tipo_vinculo, fecha_observacion, vigente, raw_json) FROM stdin;
\.


--
-- Data for Name: compania_telefonica; Type: TABLE DATA; Schema: sabanas; Owner: postgres
--

COPY sabanas.compania_telefonica (id_compania_tel, nombre_compania_tel) FROM stdin;
\.


--
-- Data for Name: imeis; Type: TABLE DATA; Schema: sabanas; Owner: postgres
--

COPY sabanas.imeis (id_imei, imei, serie, modelo_equipo) FROM stdin;
\.


--
-- Data for Name: imsis; Type: TABLE DATA; Schema: sabanas; Owner: postgres
--

COPY sabanas.imsis (id_imsi, imsi) FROM stdin;
\.


--
-- Data for Name: numero_telefonico; Type: TABLE DATA; Schema: sabanas; Owner: postgres
--

COPY sabanas.numero_telefonico (id_numero_telefonico, numero, id_compania_tel, codigo_area) FROM stdin;
\.


--
-- Data for Name: sabana; Type: TABLE DATA; Schema: sabanas; Owner: postgres
--

COPY sabanas.sabana (id_sabana, id_numero_telefonico, id_caso, estado, fecha_creacion, fecha_modificacion) FROM stdin;
\.


--
-- Data for Name: sabana_analizada; Type: TABLE DATA; Schema: sabanas; Owner: postgres
--

COPY sabanas.sabana_analizada (id_sabana_analizada, id_sabana, id_sabana_cargada, numero_a, numero_b, id_tipo_registro, id_imei, id_imsi, duracion, latitud, longitud, azimuth, altitud, fecha_analisis) FROM stdin;
\.


--
-- Data for Name: sabana_cargada; Type: TABLE DATA; Schema: sabanas; Owner: postgres
--

COPY sabanas.sabana_cargada (id_sabana_cargada, id_sabana, ruta, estado, fecha_carga, fecha_modificacion) FROM stdin;
\.


--
-- Data for Name: tipo_registro; Type: TABLE DATA; Schema: sabanas; Owner: postgres
--

COPY sabanas.tipo_registro (id_tipo_registro, tipo, descripcion) FROM stdin;
\.


--
-- Name: caso_analisis_id_caso_analisis_seq; Type: SEQUENCE SET; Schema: casos; Owner: postgres
--

SELECT pg_catalog.setval('casos.caso_analisis_id_caso_analisis_seq', 1, false);


--
-- Name: caso_id_caso_seq; Type: SEQUENCE SET; Schema: casos; Owner: postgres
--

SELECT pg_catalog.setval('casos.caso_id_caso_seq', 1, false);


--
-- Name: caso_identidad_digital_id_caso_identidad_digital_seq; Type: SEQUENCE SET; Schema: casos; Owner: postgres
--

SELECT pg_catalog.setval('casos.caso_identidad_digital_id_caso_identidad_digital_seq', 1, false);


--
-- Name: caso_persona_id_caso_persona_seq; Type: SEQUENCE SET; Schema: casos; Owner: postgres
--

SELECT pg_catalog.setval('casos.caso_persona_id_caso_persona_seq', 1, false);


--
-- Name: colaborador_caso_id_colaborador_caso_seq; Type: SEQUENCE SET; Schema: casos; Owner: postgres
--

SELECT pg_catalog.setval('casos.colaborador_caso_id_colaborador_caso_seq', 1, false);


--
-- Name: area_id_area_seq; Type: SEQUENCE SET; Schema: entidades; Owner: postgres
--

SELECT pg_catalog.setval('entidades.area_id_area_seq', 2, true);


--
-- Name: departamento_id_departamento_seq; Type: SEQUENCE SET; Schema: entidades; Owner: postgres
--

SELECT pg_catalog.setval('entidades.departamento_id_departamento_seq', 1, true);


--
-- Name: organizacion_id_organizacion_seq; Type: SEQUENCE SET; Schema: entidades; Owner: postgres
--

SELECT pg_catalog.setval('entidades.organizacion_id_organizacion_seq', 2, true);


--
-- Name: permiso_id_permiso_seq; Type: SEQUENCE SET; Schema: entidades; Owner: postgres
--

SELECT pg_catalog.setval('entidades.permiso_id_permiso_seq', 1, false);


--
-- Name: rol_id_rol_seq; Type: SEQUENCE SET; Schema: entidades; Owner: postgres
--

SELECT pg_catalog.setval('entidades.rol_id_rol_seq', 1, false);


--
-- Name: rol_permiso_id_rol_permiso_seq; Type: SEQUENCE SET; Schema: entidades; Owner: postgres
--

SELECT pg_catalog.setval('entidades.rol_permiso_id_rol_permiso_seq', 1, false);


--
-- Name: usuario_id_usuario_seq; Type: SEQUENCE SET; Schema: entidades; Owner: postgres
--

SELECT pg_catalog.setval('entidades.usuario_id_usuario_seq', 1, true);


--
-- Name: usuario_rol_id_usuario_rol_seq; Type: SEQUENCE SET; Schema: entidades; Owner: postgres
--

SELECT pg_catalog.setval('entidades.usuario_rol_id_usuario_rol_seq', 1, false);


--
-- Name: identidad_digital_id_identidad_digital_seq; Type: SEQUENCE SET; Schema: personas; Owner: postgres
--

SELECT pg_catalog.setval('personas.identidad_digital_id_identidad_digital_seq', 1, false);


--
-- Name: persona_id_persona_seq; Type: SEQUENCE SET; Schema: personas; Owner: postgres
--

SELECT pg_catalog.setval('personas.persona_id_persona_seq', 1, false);


--
-- Name: analisis_id_analisis_seq; Type: SEQUENCE SET; Schema: redes; Owner: postgres
--

SELECT pg_catalog.setval('redes.analisis_id_analisis_seq', 1, false);


--
-- Name: comentario_id_comentario_seq; Type: SEQUENCE SET; Schema: redes; Owner: postgres
--

SELECT pg_catalog.setval('redes.comentario_id_comentario_seq', 1, false);


--
-- Name: compartido_id_compartido_seq; Type: SEQUENCE SET; Schema: redes; Owner: postgres
--

SELECT pg_catalog.setval('redes.compartido_id_compartido_seq', 1, false);


--
-- Name: plataforma_id_plataforma_seq; Type: SEQUENCE SET; Schema: redes; Owner: postgres
--

SELECT pg_catalog.setval('redes.plataforma_id_plataforma_seq', 1, false);


--
-- Name: publicacion_id_publicacion_seq; Type: SEQUENCE SET; Schema: redes; Owner: postgres
--

SELECT pg_catalog.setval('redes.publicacion_id_publicacion_seq', 1, false);


--
-- Name: publicacion_multimedia_id_publicacion_multimedia_seq; Type: SEQUENCE SET; Schema: redes; Owner: postgres
--

SELECT pg_catalog.setval('redes.publicacion_multimedia_id_publicacion_multimedia_seq', 1, false);


--
-- Name: reaccion_id_reaccion_seq; Type: SEQUENCE SET; Schema: redes; Owner: postgres
--

SELECT pg_catalog.setval('redes.reaccion_id_reaccion_seq', 1, false);


--
-- Name: tipo_vinculo_social_id_tipo_vinculo_seq; Type: SEQUENCE SET; Schema: redes; Owner: postgres
--

SELECT pg_catalog.setval('redes.tipo_vinculo_social_id_tipo_vinculo_seq', 1, false);


--
-- Name: vinculo_social_id_vinculo_social_seq; Type: SEQUENCE SET; Schema: redes; Owner: postgres
--

SELECT pg_catalog.setval('redes.vinculo_social_id_vinculo_social_seq', 1, false);


--
-- Name: compania_telefonica_id_compania_tel_seq; Type: SEQUENCE SET; Schema: sabanas; Owner: postgres
--

SELECT pg_catalog.setval('sabanas.compania_telefonica_id_compania_tel_seq', 1, false);


--
-- Name: imeis_id_imei_seq; Type: SEQUENCE SET; Schema: sabanas; Owner: postgres
--

SELECT pg_catalog.setval('sabanas.imeis_id_imei_seq', 1, false);


--
-- Name: imsis_id_imsi_seq; Type: SEQUENCE SET; Schema: sabanas; Owner: postgres
--

SELECT pg_catalog.setval('sabanas.imsis_id_imsi_seq', 1, false);


--
-- Name: numero_telefonico_id_numero_telefonico_seq; Type: SEQUENCE SET; Schema: sabanas; Owner: postgres
--

SELECT pg_catalog.setval('sabanas.numero_telefonico_id_numero_telefonico_seq', 1, false);


--
-- Name: sabana_analizada_id_sabana_analizada_seq; Type: SEQUENCE SET; Schema: sabanas; Owner: postgres
--

SELECT pg_catalog.setval('sabanas.sabana_analizada_id_sabana_analizada_seq', 1, false);


--
-- Name: sabana_cargada_id_sabana_cargada_seq; Type: SEQUENCE SET; Schema: sabanas; Owner: postgres
--

SELECT pg_catalog.setval('sabanas.sabana_cargada_id_sabana_cargada_seq', 1, false);


--
-- Name: sabana_id_sabana_seq; Type: SEQUENCE SET; Schema: sabanas; Owner: postgres
--

SELECT pg_catalog.setval('sabanas.sabana_id_sabana_seq', 1, false);


--
-- Name: tipo_registro_id_tipo_registro_seq; Type: SEQUENCE SET; Schema: sabanas; Owner: postgres
--

SELECT pg_catalog.setval('sabanas.tipo_registro_id_tipo_registro_seq', 1, false);


--
-- Name: caso_analisis caso_analisis_pkey; Type: CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso_analisis
    ADD CONSTRAINT caso_analisis_pkey PRIMARY KEY (id_caso_analisis);


--
-- Name: caso_identidad_digital caso_identidad_digital_pkey; Type: CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso_identidad_digital
    ADD CONSTRAINT caso_identidad_digital_pkey PRIMARY KEY (id_caso_identidad_digital);


--
-- Name: caso_persona caso_persona_pkey; Type: CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso_persona
    ADD CONSTRAINT caso_persona_pkey PRIMARY KEY (id_caso_persona);


--
-- Name: caso caso_pkey; Type: CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso
    ADD CONSTRAINT caso_pkey PRIMARY KEY (id_caso);


--
-- Name: colaborador_caso colaborador_caso_pkey; Type: CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.colaborador_caso
    ADD CONSTRAINT colaborador_caso_pkey PRIMARY KEY (id_colaborador_caso);


--
-- Name: caso_analisis uq_caso_analisis; Type: CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso_analisis
    ADD CONSTRAINT uq_caso_analisis UNIQUE (id_caso, id_analisis);


--
-- Name: caso_identidad_digital uq_caso_identidad_digital; Type: CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso_identidad_digital
    ADD CONSTRAINT uq_caso_identidad_digital UNIQUE (id_caso, id_identidad_digital);


--
-- Name: caso_persona uq_caso_persona; Type: CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso_persona
    ADD CONSTRAINT uq_caso_persona UNIQUE (id_caso, id_persona);


--
-- Name: colaborador_caso uq_colaborador_caso; Type: CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.colaborador_caso
    ADD CONSTRAINT uq_colaborador_caso UNIQUE (id_caso, id_usuario);


--
-- Name: area area_pkey; Type: CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.area
    ADD CONSTRAINT area_pkey PRIMARY KEY (id_area);


--
-- Name: departamento departamento_pkey; Type: CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.departamento
    ADD CONSTRAINT departamento_pkey PRIMARY KEY (id_departamento);


--
-- Name: organizacion organizacion_nombre_organizacion_key; Type: CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.organizacion
    ADD CONSTRAINT organizacion_nombre_organizacion_key UNIQUE (nombre_organizacion);


--
-- Name: organizacion organizacion_pkey; Type: CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.organizacion
    ADD CONSTRAINT organizacion_pkey PRIMARY KEY (id_organizacion);


--
-- Name: permiso permiso_codigo_key; Type: CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.permiso
    ADD CONSTRAINT permiso_codigo_key UNIQUE (codigo);


--
-- Name: permiso permiso_pkey; Type: CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.permiso
    ADD CONSTRAINT permiso_pkey PRIMARY KEY (id_permiso);


--
-- Name: rol rol_nombre_key; Type: CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.rol
    ADD CONSTRAINT rol_nombre_key UNIQUE (nombre);


--
-- Name: rol_permiso rol_permiso_pkey; Type: CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.rol_permiso
    ADD CONSTRAINT rol_permiso_pkey PRIMARY KEY (id_rol_permiso);


--
-- Name: rol rol_pkey; Type: CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.rol
    ADD CONSTRAINT rol_pkey PRIMARY KEY (id_rol);


--
-- Name: rol_permiso uq_rol_permiso; Type: CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.rol_permiso
    ADD CONSTRAINT uq_rol_permiso UNIQUE (id_rol, id_permiso);


--
-- Name: usuario_rol uq_usuario_rol; Type: CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.usuario_rol
    ADD CONSTRAINT uq_usuario_rol UNIQUE (id_usuario, id_rol);


--
-- Name: usuario usuario_email_key; Type: CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.usuario
    ADD CONSTRAINT usuario_email_key UNIQUE (email);


--
-- Name: usuario usuario_pkey; Type: CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.usuario
    ADD CONSTRAINT usuario_pkey PRIMARY KEY (id_usuario);


--
-- Name: usuario_rol usuario_rol_pkey; Type: CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.usuario_rol
    ADD CONSTRAINT usuario_rol_pkey PRIMARY KEY (id_usuario_rol);


--
-- Name: identidad_digital identidad_digital_pkey; Type: CONSTRAINT; Schema: personas; Owner: postgres
--

ALTER TABLE ONLY personas.identidad_digital
    ADD CONSTRAINT identidad_digital_pkey PRIMARY KEY (id_identidad_digital);


--
-- Name: persona persona_pkey; Type: CONSTRAINT; Schema: personas; Owner: postgres
--

ALTER TABLE ONLY personas.persona
    ADD CONSTRAINT persona_pkey PRIMARY KEY (id_persona);


--
-- Name: identidad_digital uq_identidad_digital_plataforma_externo; Type: CONSTRAINT; Schema: personas; Owner: postgres
--

ALTER TABLE ONLY personas.identidad_digital
    ADD CONSTRAINT uq_identidad_digital_plataforma_externo UNIQUE (id_plataforma, identificador_externo);


--
-- Name: identidad_digital uq_identidad_digital_plataforma_username; Type: CONSTRAINT; Schema: personas; Owner: postgres
--

ALTER TABLE ONLY personas.identidad_digital
    ADD CONSTRAINT uq_identidad_digital_plataforma_username UNIQUE (id_plataforma, username);


--
-- Name: persona uq_persona_curp; Type: CONSTRAINT; Schema: personas; Owner: postgres
--

ALTER TABLE ONLY personas.persona
    ADD CONSTRAINT uq_persona_curp UNIQUE (curp);


--
-- Name: persona uq_persona_rfc; Type: CONSTRAINT; Schema: personas; Owner: postgres
--

ALTER TABLE ONLY personas.persona
    ADD CONSTRAINT uq_persona_rfc UNIQUE (rfc);


--
-- Name: analisis analisis_pkey; Type: CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.analisis
    ADD CONSTRAINT analisis_pkey PRIMARY KEY (id_analisis);


--
-- Name: comentario comentario_pkey; Type: CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.comentario
    ADD CONSTRAINT comentario_pkey PRIMARY KEY (id_comentario);


--
-- Name: compartido compartido_pkey; Type: CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.compartido
    ADD CONSTRAINT compartido_pkey PRIMARY KEY (id_compartido);


--
-- Name: plataforma plataforma_codigo_key; Type: CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.plataforma
    ADD CONSTRAINT plataforma_codigo_key UNIQUE (codigo);


--
-- Name: plataforma plataforma_pkey; Type: CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.plataforma
    ADD CONSTRAINT plataforma_pkey PRIMARY KEY (id_plataforma);


--
-- Name: publicacion_multimedia publicacion_multimedia_pkey; Type: CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.publicacion_multimedia
    ADD CONSTRAINT publicacion_multimedia_pkey PRIMARY KEY (id_publicacion_multimedia);


--
-- Name: publicacion publicacion_pkey; Type: CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.publicacion
    ADD CONSTRAINT publicacion_pkey PRIMARY KEY (id_publicacion);


--
-- Name: reaccion reaccion_pkey; Type: CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.reaccion
    ADD CONSTRAINT reaccion_pkey PRIMARY KEY (id_reaccion);


--
-- Name: tipo_vinculo_social tipo_vinculo_social_codigo_key; Type: CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.tipo_vinculo_social
    ADD CONSTRAINT tipo_vinculo_social_codigo_key UNIQUE (codigo);


--
-- Name: tipo_vinculo_social tipo_vinculo_social_pkey; Type: CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.tipo_vinculo_social
    ADD CONSTRAINT tipo_vinculo_social_pkey PRIMARY KEY (id_tipo_vinculo);


--
-- Name: comentario uq_comentario_plataforma_externo; Type: CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.comentario
    ADD CONSTRAINT uq_comentario_plataforma_externo UNIQUE (id_plataforma, identificador_externo);


--
-- Name: publicacion uq_publicacion_plataforma_externo; Type: CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.publicacion
    ADD CONSTRAINT uq_publicacion_plataforma_externo UNIQUE (id_plataforma, identificador_externo);


--
-- Name: vinculo_social uq_vinculo_por_analisis; Type: CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.vinculo_social
    ADD CONSTRAINT uq_vinculo_por_analisis UNIQUE (id_analisis, id_identidad_origen, id_identidad_destino, id_tipo_vinculo);


--
-- Name: vinculo_social vinculo_social_pkey; Type: CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.vinculo_social
    ADD CONSTRAINT vinculo_social_pkey PRIMARY KEY (id_vinculo_social);


--
-- Name: compania_telefonica compania_telefonica_nombre_compania_tel_key; Type: CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.compania_telefonica
    ADD CONSTRAINT compania_telefonica_nombre_compania_tel_key UNIQUE (nombre_compania_tel);


--
-- Name: compania_telefonica compania_telefonica_pkey; Type: CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.compania_telefonica
    ADD CONSTRAINT compania_telefonica_pkey PRIMARY KEY (id_compania_tel);


--
-- Name: imeis imeis_imei_key; Type: CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.imeis
    ADD CONSTRAINT imeis_imei_key UNIQUE (imei);


--
-- Name: imeis imeis_pkey; Type: CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.imeis
    ADD CONSTRAINT imeis_pkey PRIMARY KEY (id_imei);


--
-- Name: imsis imsis_imsi_key; Type: CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.imsis
    ADD CONSTRAINT imsis_imsi_key UNIQUE (imsi);


--
-- Name: imsis imsis_pkey; Type: CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.imsis
    ADD CONSTRAINT imsis_pkey PRIMARY KEY (id_imsi);


--
-- Name: numero_telefonico numero_telefonico_numero_key; Type: CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.numero_telefonico
    ADD CONSTRAINT numero_telefonico_numero_key UNIQUE (numero);


--
-- Name: numero_telefonico numero_telefonico_pkey; Type: CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.numero_telefonico
    ADD CONSTRAINT numero_telefonico_pkey PRIMARY KEY (id_numero_telefonico);


--
-- Name: sabana_analizada sabana_analizada_pkey; Type: CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.sabana_analizada
    ADD CONSTRAINT sabana_analizada_pkey PRIMARY KEY (id_sabana_analizada);


--
-- Name: sabana_cargada sabana_cargada_pkey; Type: CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.sabana_cargada
    ADD CONSTRAINT sabana_cargada_pkey PRIMARY KEY (id_sabana_cargada);


--
-- Name: sabana sabana_pkey; Type: CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.sabana
    ADD CONSTRAINT sabana_pkey PRIMARY KEY (id_sabana);


--
-- Name: tipo_registro tipo_registro_pkey; Type: CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.tipo_registro
    ADD CONSTRAINT tipo_registro_pkey PRIMARY KEY (id_tipo_registro);


--
-- Name: tipo_registro tipo_registro_tipo_key; Type: CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.tipo_registro
    ADD CONSTRAINT tipo_registro_tipo_key UNIQUE (tipo);


--
-- Name: idx_caso_analisis_analisis; Type: INDEX; Schema: casos; Owner: postgres
--

CREATE INDEX idx_caso_analisis_analisis ON casos.caso_analisis USING btree (id_analisis);


--
-- Name: idx_caso_analisis_caso; Type: INDEX; Schema: casos; Owner: postgres
--

CREATE INDEX idx_caso_analisis_caso ON casos.caso_analisis USING btree (id_caso);


--
-- Name: idx_caso_identidad_caso; Type: INDEX; Schema: casos; Owner: postgres
--

CREATE INDEX idx_caso_identidad_caso ON casos.caso_identidad_digital USING btree (id_caso);


--
-- Name: idx_caso_identidad_identidad; Type: INDEX; Schema: casos; Owner: postgres
--

CREATE INDEX idx_caso_identidad_identidad ON casos.caso_identidad_digital USING btree (id_identidad_digital);


--
-- Name: idx_caso_persona_caso; Type: INDEX; Schema: casos; Owner: postgres
--

CREATE INDEX idx_caso_persona_caso ON casos.caso_persona USING btree (id_caso);


--
-- Name: idx_caso_persona_persona; Type: INDEX; Schema: casos; Owner: postgres
--

CREATE INDEX idx_caso_persona_persona ON casos.caso_persona USING btree (id_persona);


--
-- Name: idx_identidad_persona; Type: INDEX; Schema: personas; Owner: postgres
--

CREATE INDEX idx_identidad_persona ON personas.identidad_digital USING btree (id_persona);


--
-- Name: idx_identidad_plataforma; Type: INDEX; Schema: personas; Owner: postgres
--

CREATE INDEX idx_identidad_plataforma ON personas.identidad_digital USING btree (id_plataforma);


--
-- Name: idx_identidad_username; Type: INDEX; Schema: personas; Owner: postgres
--

CREATE INDEX idx_identidad_username ON personas.identidad_digital USING btree (username);


--
-- Name: idx_persona_curp; Type: INDEX; Schema: personas; Owner: postgres
--

CREATE INDEX idx_persona_curp ON personas.persona USING btree (curp);


--
-- Name: idx_persona_rfc; Type: INDEX; Schema: personas; Owner: postgres
--

CREATE INDEX idx_persona_rfc ON personas.persona USING btree (rfc);


--
-- Name: idx_analisis_identidad_objetivo; Type: INDEX; Schema: redes; Owner: postgres
--

CREATE INDEX idx_analisis_identidad_objetivo ON redes.analisis USING btree (id_identidad_digital_objetivo);


--
-- Name: idx_analisis_usuario_ejecutor; Type: INDEX; Schema: redes; Owner: postgres
--

CREATE INDEX idx_analisis_usuario_ejecutor ON redes.analisis USING btree (id_usuario_ejecutor);


--
-- Name: idx_comentario_analisis; Type: INDEX; Schema: redes; Owner: postgres
--

CREATE INDEX idx_comentario_analisis ON redes.comentario USING btree (id_analisis);


--
-- Name: idx_comentario_publicacion; Type: INDEX; Schema: redes; Owner: postgres
--

CREATE INDEX idx_comentario_publicacion ON redes.comentario USING btree (id_publicacion);


--
-- Name: idx_compartido_analisis; Type: INDEX; Schema: redes; Owner: postgres
--

CREATE INDEX idx_compartido_analisis ON redes.compartido USING btree (id_analisis);


--
-- Name: idx_publicacion_analisis; Type: INDEX; Schema: redes; Owner: postgres
--

CREATE INDEX idx_publicacion_analisis ON redes.publicacion USING btree (id_analisis);


--
-- Name: idx_publicacion_autor; Type: INDEX; Schema: redes; Owner: postgres
--

CREATE INDEX idx_publicacion_autor ON redes.publicacion USING btree (id_identidad_autor);


--
-- Name: idx_reaccion_analisis; Type: INDEX; Schema: redes; Owner: postgres
--

CREATE INDEX idx_reaccion_analisis ON redes.reaccion USING btree (id_analisis);


--
-- Name: idx_reaccion_comentario; Type: INDEX; Schema: redes; Owner: postgres
--

CREATE INDEX idx_reaccion_comentario ON redes.reaccion USING btree (id_comentario);


--
-- Name: idx_reaccion_publicacion; Type: INDEX; Schema: redes; Owner: postgres
--

CREATE INDEX idx_reaccion_publicacion ON redes.reaccion USING btree (id_publicacion);


--
-- Name: idx_vinculo_analisis; Type: INDEX; Schema: redes; Owner: postgres
--

CREATE INDEX idx_vinculo_analisis ON redes.vinculo_social USING btree (id_analisis);


--
-- Name: idx_vinculo_destino; Type: INDEX; Schema: redes; Owner: postgres
--

CREATE INDEX idx_vinculo_destino ON redes.vinculo_social USING btree (id_identidad_destino);


--
-- Name: idx_vinculo_origen; Type: INDEX; Schema: redes; Owner: postgres
--

CREATE INDEX idx_vinculo_origen ON redes.vinculo_social USING btree (id_identidad_origen);


--
-- Name: caso_analisis fk_caso_analisis_analisis; Type: FK CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso_analisis
    ADD CONSTRAINT fk_caso_analisis_analisis FOREIGN KEY (id_analisis) REFERENCES redes.analisis(id_analisis) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: caso_analisis fk_caso_analisis_caso; Type: FK CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso_analisis
    ADD CONSTRAINT fk_caso_analisis_caso FOREIGN KEY (id_caso) REFERENCES casos.caso(id_caso) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: caso_identidad_digital fk_caso_identidad_caso; Type: FK CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso_identidad_digital
    ADD CONSTRAINT fk_caso_identidad_caso FOREIGN KEY (id_caso) REFERENCES casos.caso(id_caso) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: caso_identidad_digital fk_caso_identidad_identidad; Type: FK CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso_identidad_digital
    ADD CONSTRAINT fk_caso_identidad_identidad FOREIGN KEY (id_identidad_digital) REFERENCES personas.identidad_digital(id_identidad_digital) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: caso_persona fk_caso_persona_caso; Type: FK CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso_persona
    ADD CONSTRAINT fk_caso_persona_caso FOREIGN KEY (id_caso) REFERENCES casos.caso(id_caso) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: caso_persona fk_caso_persona_persona; Type: FK CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso_persona
    ADD CONSTRAINT fk_caso_persona_persona FOREIGN KEY (id_persona) REFERENCES personas.persona(id_persona) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: caso fk_caso_usuario_creador; Type: FK CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.caso
    ADD CONSTRAINT fk_caso_usuario_creador FOREIGN KEY (id_usuario_creador) REFERENCES entidades.usuario(id_usuario) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: colaborador_caso fk_colaborador_caso_caso; Type: FK CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.colaborador_caso
    ADD CONSTRAINT fk_colaborador_caso_caso FOREIGN KEY (id_caso) REFERENCES casos.caso(id_caso) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: colaborador_caso fk_colaborador_caso_usuario; Type: FK CONSTRAINT; Schema: casos; Owner: postgres
--

ALTER TABLE ONLY casos.colaborador_caso
    ADD CONSTRAINT fk_colaborador_caso_usuario FOREIGN KEY (id_usuario) REFERENCES entidades.usuario(id_usuario) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: area fk_area_organizacion; Type: FK CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.area
    ADD CONSTRAINT fk_area_organizacion FOREIGN KEY (id_organizacion) REFERENCES entidades.organizacion(id_organizacion) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: departamento fk_departamento_area; Type: FK CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.departamento
    ADD CONSTRAINT fk_departamento_area FOREIGN KEY (id_area) REFERENCES entidades.area(id_area) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: departamento fk_departamento_organizacion; Type: FK CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.departamento
    ADD CONSTRAINT fk_departamento_organizacion FOREIGN KEY (id_organizacion) REFERENCES entidades.organizacion(id_organizacion) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: rol_permiso fk_rol_permiso_permiso; Type: FK CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.rol_permiso
    ADD CONSTRAINT fk_rol_permiso_permiso FOREIGN KEY (id_permiso) REFERENCES entidades.permiso(id_permiso) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: rol_permiso fk_rol_permiso_rol; Type: FK CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.rol_permiso
    ADD CONSTRAINT fk_rol_permiso_rol FOREIGN KEY (id_rol) REFERENCES entidades.rol(id_rol) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: usuario fk_usuario_area; Type: FK CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.usuario
    ADD CONSTRAINT fk_usuario_area FOREIGN KEY (id_area) REFERENCES entidades.area(id_area) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: usuario fk_usuario_departamento; Type: FK CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.usuario
    ADD CONSTRAINT fk_usuario_departamento FOREIGN KEY (id_departamento) REFERENCES entidades.departamento(id_departamento) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: usuario fk_usuario_organizacion; Type: FK CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.usuario
    ADD CONSTRAINT fk_usuario_organizacion FOREIGN KEY (id_organizacion) REFERENCES entidades.organizacion(id_organizacion) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: usuario_rol fk_usuario_rol_rol; Type: FK CONSTRAINT; Schema: entidades; Owner: postgres
--

ALTER TABLE ONLY entidades.usuario_rol
    ADD CONSTRAINT fk_usuario_rol_rol FOREIGN KEY (id_rol) REFERENCES entidades.rol(id_rol) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: identidad_digital fk_identidad_digital_persona; Type: FK CONSTRAINT; Schema: personas; Owner: postgres
--

ALTER TABLE ONLY personas.identidad_digital
    ADD CONSTRAINT fk_identidad_digital_persona FOREIGN KEY (id_persona) REFERENCES personas.persona(id_persona) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: identidad_digital fk_identidad_digital_plataforma; Type: FK CONSTRAINT; Schema: personas; Owner: postgres
--

ALTER TABLE ONLY personas.identidad_digital
    ADD CONSTRAINT fk_identidad_digital_plataforma FOREIGN KEY (id_plataforma) REFERENCES redes.plataforma(id_plataforma) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: analisis fk_analisis_identidad_objetivo; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.analisis
    ADD CONSTRAINT fk_analisis_identidad_objetivo FOREIGN KEY (id_identidad_digital_objetivo) REFERENCES personas.identidad_digital(id_identidad_digital) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: analisis fk_analisis_usuario_ejecutor; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.analisis
    ADD CONSTRAINT fk_analisis_usuario_ejecutor FOREIGN KEY (id_usuario_ejecutor) REFERENCES entidades.usuario(id_usuario) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: comentario fk_comentario_analisis; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.comentario
    ADD CONSTRAINT fk_comentario_analisis FOREIGN KEY (id_analisis) REFERENCES redes.analisis(id_analisis) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: comentario fk_comentario_autor; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.comentario
    ADD CONSTRAINT fk_comentario_autor FOREIGN KEY (id_identidad_autor) REFERENCES personas.identidad_digital(id_identidad_digital) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: comentario fk_comentario_plataforma; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.comentario
    ADD CONSTRAINT fk_comentario_plataforma FOREIGN KEY (id_plataforma) REFERENCES redes.plataforma(id_plataforma) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: comentario fk_comentario_publicacion; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.comentario
    ADD CONSTRAINT fk_comentario_publicacion FOREIGN KEY (id_publicacion) REFERENCES redes.publicacion(id_publicacion) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: compartido fk_compartido_analisis; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.compartido
    ADD CONSTRAINT fk_compartido_analisis FOREIGN KEY (id_analisis) REFERENCES redes.analisis(id_analisis) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: compartido fk_compartido_identidad; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.compartido
    ADD CONSTRAINT fk_compartido_identidad FOREIGN KEY (id_identidad_que_comparte) REFERENCES personas.identidad_digital(id_identidad_digital) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: compartido fk_compartido_publicacion_generada; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.compartido
    ADD CONSTRAINT fk_compartido_publicacion_generada FOREIGN KEY (id_publicacion_generada) REFERENCES redes.publicacion(id_publicacion) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: compartido fk_compartido_publicacion_original; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.compartido
    ADD CONSTRAINT fk_compartido_publicacion_original FOREIGN KEY (id_publicacion_original) REFERENCES redes.publicacion(id_publicacion) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: publicacion_multimedia fk_multimedia_publicacion; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.publicacion_multimedia
    ADD CONSTRAINT fk_multimedia_publicacion FOREIGN KEY (id_publicacion) REFERENCES redes.publicacion(id_publicacion) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: publicacion fk_publicacion_analisis; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.publicacion
    ADD CONSTRAINT fk_publicacion_analisis FOREIGN KEY (id_analisis) REFERENCES redes.analisis(id_analisis) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: publicacion fk_publicacion_autor; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.publicacion
    ADD CONSTRAINT fk_publicacion_autor FOREIGN KEY (id_identidad_autor) REFERENCES personas.identidad_digital(id_identidad_digital) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: publicacion fk_publicacion_plataforma; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.publicacion
    ADD CONSTRAINT fk_publicacion_plataforma FOREIGN KEY (id_plataforma) REFERENCES redes.plataforma(id_plataforma) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: reaccion fk_reaccion_analisis; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.reaccion
    ADD CONSTRAINT fk_reaccion_analisis FOREIGN KEY (id_analisis) REFERENCES redes.analisis(id_analisis) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: reaccion fk_reaccion_autor; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.reaccion
    ADD CONSTRAINT fk_reaccion_autor FOREIGN KEY (id_identidad_autor) REFERENCES personas.identidad_digital(id_identidad_digital) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: reaccion fk_reaccion_comentario; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.reaccion
    ADD CONSTRAINT fk_reaccion_comentario FOREIGN KEY (id_comentario) REFERENCES redes.comentario(id_comentario) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: reaccion fk_reaccion_plataforma; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.reaccion
    ADD CONSTRAINT fk_reaccion_plataforma FOREIGN KEY (id_plataforma) REFERENCES redes.plataforma(id_plataforma) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: reaccion fk_reaccion_publicacion; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.reaccion
    ADD CONSTRAINT fk_reaccion_publicacion FOREIGN KEY (id_publicacion) REFERENCES redes.publicacion(id_publicacion) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: vinculo_social fk_vinculo_analisis; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.vinculo_social
    ADD CONSTRAINT fk_vinculo_analisis FOREIGN KEY (id_analisis) REFERENCES redes.analisis(id_analisis) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: vinculo_social fk_vinculo_destino; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.vinculo_social
    ADD CONSTRAINT fk_vinculo_destino FOREIGN KEY (id_identidad_destino) REFERENCES personas.identidad_digital(id_identidad_digital) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: vinculo_social fk_vinculo_origen; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.vinculo_social
    ADD CONSTRAINT fk_vinculo_origen FOREIGN KEY (id_identidad_origen) REFERENCES personas.identidad_digital(id_identidad_digital) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: vinculo_social fk_vinculo_tipo; Type: FK CONSTRAINT; Schema: redes; Owner: postgres
--

ALTER TABLE ONLY redes.vinculo_social
    ADD CONSTRAINT fk_vinculo_tipo FOREIGN KEY (id_tipo_vinculo) REFERENCES redes.tipo_vinculo_social(id_tipo_vinculo) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: numero_telefonico fk_numero_compania; Type: FK CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.numero_telefonico
    ADD CONSTRAINT fk_numero_compania FOREIGN KEY (id_compania_tel) REFERENCES sabanas.compania_telefonica(id_compania_tel) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: sabana_analizada fk_sabana_analizada_cargada; Type: FK CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.sabana_analizada
    ADD CONSTRAINT fk_sabana_analizada_cargada FOREIGN KEY (id_sabana_cargada) REFERENCES sabanas.sabana_cargada(id_sabana_cargada) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: sabana_analizada fk_sabana_analizada_imei; Type: FK CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.sabana_analizada
    ADD CONSTRAINT fk_sabana_analizada_imei FOREIGN KEY (id_imei) REFERENCES sabanas.imeis(id_imei) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: sabana_analizada fk_sabana_analizada_imsi; Type: FK CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.sabana_analizada
    ADD CONSTRAINT fk_sabana_analizada_imsi FOREIGN KEY (id_imsi) REFERENCES sabanas.imsis(id_imsi) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: sabana_analizada fk_sabana_analizada_sabana; Type: FK CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.sabana_analizada
    ADD CONSTRAINT fk_sabana_analizada_sabana FOREIGN KEY (id_sabana) REFERENCES sabanas.sabana(id_sabana) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sabana_analizada fk_sabana_analizada_tipo_registro; Type: FK CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.sabana_analizada
    ADD CONSTRAINT fk_sabana_analizada_tipo_registro FOREIGN KEY (id_tipo_registro) REFERENCES sabanas.tipo_registro(id_tipo_registro) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: sabana_cargada fk_sabana_cargada_sabana; Type: FK CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.sabana_cargada
    ADD CONSTRAINT fk_sabana_cargada_sabana FOREIGN KEY (id_sabana) REFERENCES sabanas.sabana(id_sabana) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sabana fk_sabana_caso; Type: FK CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.sabana
    ADD CONSTRAINT fk_sabana_caso FOREIGN KEY (id_caso) REFERENCES casos.caso(id_caso) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sabana fk_sabana_numero_telefonico; Type: FK CONSTRAINT; Schema: sabanas; Owner: postgres
--

ALTER TABLE ONLY sabanas.sabana
    ADD CONSTRAINT fk_sabana_numero_telefonico FOREIGN KEY (id_numero_telefonico) REFERENCES sabanas.numero_telefonico(id_numero_telefonico) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- PostgreSQL database dump complete
--

\unrestrict bV7hXatAvjJaAEnsfjxGLZ0oTBvvSkZl3fVI4w6cSFjb99ZhI7u9lPSgNbbXosQ

