-- Apply missing tables

CREATE TABLE IF NOT EXISTS client_proxies (
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

CREATE TABLE IF NOT EXISTS client_pickup_authorizations (
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

CREATE TABLE IF NOT EXISTS qr_sessions (
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

CREATE TABLE IF NOT EXISTS volunteer_signins (
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

CREATE TABLE IF NOT EXISTS notifications (
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

CREATE TABLE IF NOT EXISTS no_show_logs (
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
