-- SQL to add title column to UserProfile table
-- Run this using: python manage.py dbshell < fix_title_column.sql

-- Add title column if it doesn't exist
ALTER TABLE travels_userprofile ADD COLUMN title VARCHAR(10) DEFAULT 'Mr' NOT NULL;

-- Add gst_number column if it doesn't exist  
ALTER TABLE travels_userprofile ADD COLUMN gst_number VARCHAR(15) NULL;

