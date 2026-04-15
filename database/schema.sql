-- ============================================================
--  Focus IA — Schema MySQL
--  Versión: 1.0.0
--  Descripción: Schema completo para la base de datos de Focus IA.
--               Compatible con MySQL 8.0+ y MariaDB 10.5+.
-- ============================================================

-- Crear la base de datos (ejecutar solo si no existe aún)
CREATE DATABASE IF NOT EXISTS focusia
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE focusia;

-- ============================================================
--  Tabla: users
--  Descripción: Almacena usuarios registrados en la plataforma.
--               Incluye los campos requeridos por fastapi-users
--               (is_active, is_superuser, is_verified) más campos
--               propios de la aplicación (name, profile_data).
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    -- Identificador único autoincremental
    id               INT            NOT NULL AUTO_INCREMENT,

    -- Credenciales de autenticación
    email            VARCHAR(255)   NOT NULL,
    hashed_password  VARCHAR(255)   NOT NULL,

    -- Datos del perfil
    name             VARCHAR(100)   NOT NULL,
    profile_data     JSON               NULL,

    -- Marcas de tiempo
    created_at       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Flags de control (requeridos por fastapi-users)
    is_active        TINYINT(1)     NOT NULL DEFAULT 1,
    is_superuser     TINYINT(1)     NOT NULL DEFAULT 0,
    is_verified      TINYINT(1)     NOT NULL DEFAULT 0,

    -- Restricciones
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Usuarios registrados en Focus IA';

-- Índice adicional para búsquedas frecuentes por email
CREATE INDEX idx_users_email ON users (email);

-- ============================================================
--  Datos de prueba (opcional — comentar en producción)
-- ============================================================
-- INSERT INTO users (email, hashed_password, name, is_active, is_superuser, is_verified)
-- VALUES (
--     'admin@focusia.com',
--     '$2b$12$placeholder_hash_aqui',
--     'Administrador',
--     1, 1, 1
-- );
