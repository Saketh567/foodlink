-- =========================================================
-- FoodLink_Final - Full Database Schema
-- CMPT 385 - Group 09 (Trinity Loopers)
-- =========================================================

-- OPTIONAL: uncomment if you need to create the DB
-- CREATE DATABASE IF NOT EXISTS foodlink_db
--   DEFAULT CHARACTER SET utf8mb4
--   DEFAULT COLLATE utf8mb4_unicode_ci;
-- USE foodlink_db;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =========================================================
-- USERS
-- =========================================================

DROP TABLE IF EXISTS qr_sessions;
DROP TABLE IF EXISTS client_pickup_authorizations;
DROP TABLE IF EXISTS no_show_logs;
DROP TABLE IF EXISTS volunteer_signins;
DROP TABLE IF EXISTS activity_logs;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS volunteer_schedules;
DROP TABLE IF EXISTS distributions;
DROP TABLE IF EXISTS donations;
DROP TABLE IF EXISTS client_proxies;
DROP TABLE IF EXISTS clients;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id        INT AUTO_INCREMENT PRIMARY KEY,
    email          VARCHAR(191) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    full_name      VARCHAR(150) NOT NULL,
    phone          VARCHAR(30),
    role           ENUM('admin', 'volunteer', 'client') NOT NULL,
    is_active      TINYINT(1) NOT NULL DEFAULT 0,
    last_login_at  DATETIME NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_users_role (role),
    INDEX idx_users_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- CLIENTS
-- =========================================================

CREATE TABLE clients (
    client_id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id             INT NOT NULL,
    address             VARCHAR(255),
    address_original    TEXT,
    address_standardized TEXT,
    address_validation_source VARCHAR(50),
    address_validated_at DATETIME NULL,
    family_size         INT NOT NULL DEFAULT 1,
    allergies           TEXT,
    food_preferences    TEXT,
    verification_status ENUM('pending', 'verified', 'rejected') NOT NULL DEFAULT 'pending',
    client_number       VARCHAR(30) UNIQUE,
    verified_date       DATETIME NULL,
    verified_by         INT NULL,
    notes               TEXT,
    no_show_count       INT NOT NULL DEFAULT 0,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_clients_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_clients_verified_by
        FOREIGN KEY (verified_by) REFERENCES users(user_id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    INDEX idx_clients_status (verification_status),
    INDEX idx_clients_client_number (client_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- CLIENT PROXIES (PROXY PICKUP)
-- =========================================================

CREATE TABLE client_proxies (
    proxy_id      INT AUTO_INCREMENT PRIMARY KEY,
    client_id     INT NOT NULL,
    proxy_name    VARCHAR(150) NOT NULL,
    proxy_phone   VARCHAR(30),
    proxy_email   VARCHAR(191),
    status        ENUM('pending', 'approved', 'rejected', 'revoked') NOT NULL DEFAULT 'pending',
    approved_by   INT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_client_proxies_client
        FOREIGN KEY (client_id) REFERENCES clients(client_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_client_proxies_approved_by
        FOREIGN KEY (approved_by) REFERENCES users(user_id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    INDEX idx_client_proxies_client (client_id),
    INDEX idx_client_proxies_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- CLIENT PICKUP AUTHORIZATIONS
-- =========================================================

CREATE TABLE client_pickup_authorizations (
    authorization_id INT AUTO_INCREMENT PRIMARY KEY,
    client_id        INT NOT NULL,
    proxy_id         INT NULL,
    authorized_by    INT NULL,
    expires_at       DATETIME NULL,
    status           ENUM('pending', 'active', 'revoked', 'expired') NOT NULL DEFAULT 'pending',
    notes            TEXT,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_cpa_client
        FOREIGN KEY (client_id) REFERENCES clients(client_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_cpa_proxy
        FOREIGN KEY (proxy_id) REFERENCES client_proxies(proxy_id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    CONSTRAINT fk_cpa_authorizer
        FOREIGN KEY (authorized_by) REFERENCES users(user_id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    INDEX idx_cpa_client (client_id),
    INDEX idx_cpa_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- QR SESSIONS (EPHEMERAL QR VALIDATION)
-- =========================================================

CREATE TABLE qr_sessions (
    session_id   CHAR(36) PRIMARY KEY,
    client_id    INT NOT NULL,
    volunteer_id INT NULL,
    proxy_id     INT NULL,
    status       ENUM('pending', 'validated', 'completed', 'expired', 'cancelled') NOT NULL DEFAULT 'pending',
    expires_at   DATETIME NOT NULL,
    consumed_at  DATETIME NULL,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_qr_sessions_client
        FOREIGN KEY (client_id) REFERENCES clients(client_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_qr_sessions_volunteer
        FOREIGN KEY (volunteer_id) REFERENCES users(user_id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    CONSTRAINT fk_qr_sessions_proxy
        FOREIGN KEY (proxy_id) REFERENCES client_proxies(proxy_id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    INDEX idx_qr_sessions_status (status),
    INDEX idx_qr_sessions_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- DONATIONS (FOOD PICKUPS)
-- =========================================================

CREATE TABLE donations (
    donation_id     INT AUTO_INCREMENT PRIMARY KEY,
    volunteer_id    INT NOT NULL,
    donation_date   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    weight_kg       DECIMAL(8,2) NOT NULL,
    food_type       VARCHAR(100),
    source          VARCHAR(150),
    description     TEXT,
    status          ENUM('collected', 'cancelled', 'archived') NOT NULL DEFAULT 'collected',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_donations_volunteer
        FOREIGN KEY (volunteer_id) REFERENCES users(user_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    INDEX idx_donations_volunteer_date (volunteer_id, donation_date),
    INDEX idx_donations_date (donation_date),
    INDEX idx_donations_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- DISTRIBUTIONS (FOOD GIVEN TO CLIENTS)
-- =========================================================

CREATE TABLE distributions (
    distribution_id   INT AUTO_INCREMENT PRIMARY KEY,
    client_id         INT NOT NULL,
    volunteer_id      INT NOT NULL,
    distribution_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    weight_kg         DECIMAL(8,2) NOT NULL,
    items_description TEXT,
    client_signature  TINYINT(1) NOT NULL DEFAULT 0,
    notes             TEXT,
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_distributions_client
        FOREIGN KEY (client_id) REFERENCES clients(client_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_distributions_volunteer
        FOREIGN KEY (volunteer_id) REFERENCES users(user_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    INDEX idx_distributions_client_date (client_id, distribution_date),
    INDEX idx_distributions_volunteer_date (volunteer_id, distribution_date),
    INDEX idx_distributions_date (distribution_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- VOLUNTEER SCHEDULES
-- =========================================================

CREATE TABLE volunteer_schedules (
    schedule_id   INT AUTO_INCREMENT PRIMARY KEY,
    volunteer_id  INT NOT NULL,
    schedule_date DATE NOT NULL,
    start_time    TIME NOT NULL,
    end_time      TIME NOT NULL,
    status        ENUM('scheduled', 'completed', 'cancelled') NOT NULL DEFAULT 'scheduled',
    notes         TEXT,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_volunteer_schedules_volunteer
        FOREIGN KEY (volunteer_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    INDEX idx_volunteer_schedules_volunteer_date (volunteer_id, schedule_date),
    INDEX idx_volunteer_schedules_date (schedule_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- VOLUNTEER SIGN-INS
-- =========================================================

CREATE TABLE volunteer_signins (
    signin_id     INT AUTO_INCREMENT PRIMARY KEY,
    volunteer_id  INT NOT NULL,
    signin_time   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    signout_time  DATETIME NULL,
    status        ENUM('signed_in', 'signed_out', 'no_show') NOT NULL DEFAULT 'signed_in',
    method        ENUM('qr', 'manual', 'admin') NOT NULL DEFAULT 'manual',
    location      VARCHAR(191),
    notes         TEXT,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_volunteer_signins_volunteer
        FOREIGN KEY (volunteer_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    INDEX idx_volunteer_signins_volunteer (volunteer_id),
    INDEX idx_volunteer_signins_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- NOTIFICATIONS (IN-APP MESSAGES)
-- =========================================================

CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    message         TEXT NOT NULL,
    type            ENUM('info', 'success', 'warning', 'error', 'system') NOT NULL DEFAULT 'info',
    is_read         TINYINT(1) NOT NULL DEFAULT 0,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_notifications_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    INDEX idx_notifications_user_read (user_id, is_read),
    INDEX idx_notifications_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- NO-SHOW LOGS
-- =========================================================

CREATE TABLE no_show_logs (
    log_id            INT AUTO_INCREMENT PRIMARY KEY,
    client_id         INT NOT NULL,
    schedule_id       INT NULL,
    distribution_id   INT NULL,
    logged_by         INT NULL,
    reason            VARCHAR(255),
    threshold_reached TINYINT(1) NOT NULL DEFAULT 0,
    action_taken      VARCHAR(255),
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_no_show_client
        FOREIGN KEY (client_id) REFERENCES clients(client_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_no_show_schedule
        FOREIGN KEY (schedule_id) REFERENCES volunteer_schedules(schedule_id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    CONSTRAINT fk_no_show_distribution
        FOREIGN KEY (distribution_id) REFERENCES distributions(distribution_id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    CONSTRAINT fk_no_show_logger
        FOREIGN KEY (logged_by) REFERENCES users(user_id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    INDEX idx_no_show_client (client_id),
    INDEX idx_no_show_threshold (threshold_reached)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- ACTIVITY LOGS (AUDIT TRAIL)
-- =========================================================

CREATE TABLE activity_logs (
    log_id        INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NULL,
    action        VARCHAR(150) NOT NULL,
    description   TEXT,
    ip_address    VARCHAR(45),
    related_type  ENUM('user','client','donation','distribution','schedule','proxy','other') DEFAULT 'other',
    related_id    INT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_activity_logs_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    INDEX idx_activity_logs_user (user_id),
    INDEX idx_activity_logs_created_at (created_at),
    INDEX idx_activity_logs_related (related_type, related_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- =========================================================
-- OPTIONAL: Seed initial admin user (password hash later)
-- =========================================================
-- INSERT INTO users (email, password_hash, full_name, phone, role, is_active)
-- VALUES ('admin@example.com', '<HASH_HERE>', 'Default Admin', '0000000000', 'admin', 1);
