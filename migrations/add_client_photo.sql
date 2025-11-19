-- Migration: Add photo_path column to clients table
-- Date: 2024

USE foodlink_db;

-- Add photo_path column to clients table
ALTER TABLE clients 
ADD COLUMN photo_path VARCHAR(500) NULL AFTER income_proof_path;

-- Add index for faster lookups
CREATE INDEX idx_photo_path ON clients(photo_path);

