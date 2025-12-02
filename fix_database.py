#!/usr/bin/env python
"""Script to add missing columns to UserProfile table"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Travel_agency.settings')
django.setup()

from django.db import connection

def fix_database():
    """Add title and gst_number columns if they don't exist"""
    with connection.cursor() as cursor:
        try:
            # Get current columns
            cursor.execute("PRAGMA table_info(travels_userprofile)")
            columns = {row[1]: row for row in cursor.fetchall()}
            
            print("Current columns in travels_userprofile:")
            for col_name in columns.keys():
                print(f"  - {col_name}")
            
            # Add title column if missing
            if 'title' not in columns:
                print("\nAdding 'title' column...")
                cursor.execute("""
                    ALTER TABLE travels_userprofile 
                    ADD COLUMN title VARCHAR(10) DEFAULT 'Mr' NOT NULL
                """)
                print("✓ Title column added successfully!")
            else:
                print("\n✓ Title column already exists")
            
            # Add gst_number column if missing
            if 'gst_number' not in columns:
                print("\nAdding 'gst_number' column...")
                cursor.execute("""
                    ALTER TABLE travels_userprofile 
                    ADD COLUMN gst_number VARCHAR(15) NULL
                """)
                print("✓ GST number column added successfully!")
            else:
                print("\n✓ GST number column already exists")
            
            # Verify columns were added
            cursor.execute("PRAGMA table_info(travels_userprofile)")
            new_columns = {row[1]: row for row in cursor.fetchall()}
            
            print("\n\nUpdated columns in travels_userprofile:")
            for col_name in new_columns.keys():
                print(f"  - {col_name}")
            
            print("\n✓ Database fix completed successfully!")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    import sys
    print("Starting database fix...", file=sys.stderr)
    sys.stderr.flush()
    fix_database()
    print("\nDone!", file=sys.stderr)
    sys.stderr.flush()

