-- SQL script to create test accounts for barcode scanning testing

-- Create volunteer account (password: password123)
INSERT IGNORE INTO users (email, password_hash, full_name, role, is_active)
VALUES ('volunteer@test.com', 'scrypt:32768:8:1$r3r6LGzujm5MbqYQ$5a9bbef854d1fa307c656c076e4244b4076c5e712833a89714b577511709a3190', 'Test Volunteer', 'volunteer', 1);

-- Create client account (password: password123)
INSERT IGNORE INTO users (email, password_hash, full_name, role, is_active)
VALUES ('client@test.com', 'scrypt:32768:8:1$r3r6LGzujm5MbqYQ$5a9bbef854d1fa307c656c076e4244b4076c5e712833a89714b577511709a3190', 'Test Client', 'client', 1);

-- Get the client user_id and create client profile
SET @client_user_id = (SELECT user_id FROM users WHERE email='client@test.com');

INSERT IGNORE INTO clients (user_id, address, family_size, verification_status, client_number, verified_date)
VALUES (@client_user_id, '123 Test St, Vancouver, BC', 3, 'verified', CONCAT('CL', LPAD(@client_user_id, 5, '0')), NOW());

-- Update client to ensure verified status
UPDATE clients SET verification_status='verified', client_number=CONCAT('CL', LPAD(user_id, 5, '0'))
WHERE user_id = @client_user_id;

SELECT 'Test accounts created successfully!' AS message;
SELECT 'Volunteer: volunteer@test.com / password123' AS credentials;
SELECT 'Client: client@test.com / password123' AS credentials;
