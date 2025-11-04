#!/usr/bin/env python
"""
Quick diagnostic script to check if everything is set up correctly
"""
import os
import sys
from pathlib import Path

print("=" * 60)
print("Safar Zone Travels - Setup Diagnostic")
print("=" * 60)

BASE_DIR = Path(__file__).resolve().parent

# Check 1: CSS Output File
css_file = BASE_DIR / 'static' / 'css' / 'output.css'
print("\n[*] Checking CSS file...")
if css_file.exists():
    size = css_file.stat().st_size
    print(f"  [OK] CSS file exists: {css_file}")
    print(f"  [OK] File size: {size:,} bytes ({size/1024:.1f} KB)")
    if size < 5000:
        print("  [!]  WARNING: CSS file is small. May need rebuild.")
else:
    print(f"  [X] CSS file NOT found: {css_file}")
    print("  -> Run: npm run build:css")

# Check 2: Static directories
print("\n[*] Checking static directories...")
static_dir = BASE_DIR / 'static'
if static_dir.exists():
    print(f"  [OK] Static directory exists: {static_dir}")
    subdirs = ['css', 'js', 'src']
    for subdir in subdirs:
        path = static_dir / subdir
        if path.exists():
            print(f"  [OK] {subdir}/ directory exists")
        else:
            print(f"  [X] {subdir}/ directory missing")
else:
    print(f"  [X] Static directory NOT found: {static_dir}")

# Check 3: Templates
print("\n[*] Checking templates...")
templates_dir = BASE_DIR / 'templates'
if templates_dir.exists():
    print(f"  [OK] Templates directory exists: {templates_dir}")
    templates = ['base.html', 'index.html', 'search.html', 'booking.html', 
                 'dashboard.html', 'login.html', 'signup.html']
    for tmpl in templates:
        path = templates_dir / tmpl
        if path.exists():
            print(f"  [OK] {tmpl}")
        else:
            print(f"  [X] {tmpl} missing")
else:
    print(f"  [X] Templates directory NOT found: {templates_dir}")

# Check 4: Node modules
print("\n[*] Checking Node.js setup...")
node_modules = BASE_DIR / 'node_modules'
if node_modules.exists():
    print(f"  [OK] node_modules exists")
    tailwind = node_modules / 'tailwindcss'
    if tailwind.exists():
        print(f"  [OK] Tailwind CSS installed")
    else:
        print(f"  [X] Tailwind CSS NOT installed")
        print("  -> Run: npm install")
else:
    print(f"  [X] node_modules NOT found")
    print("  -> Run: npm install")

# Check 5: Database
print("\n[*] Checking database...")
db_file = BASE_DIR / 'db.sqlite3'
if db_file.exists():
    size = db_file.stat().st_size
    print(f"  [OK] Database exists: {db_file}")
    print(f"  [OK] File size: {size:,} bytes ({size/1024:.1f} KB)")
    if size < 50000:
        print("  [!]  WARNING: Database is small. May need migrations/data.")
else:
    print(f"  [X] Database NOT found: {db_file}")
    print("  -> Run: python manage.py migrate")

# Check 6: Configuration files
print("\n[*] Checking configuration files...")
config_files = [
    'tailwind.config.js',
    'package.json',
    'requirements.txt',
    'manage.py'
]
for config in config_files:
    path = BASE_DIR / config
    if path.exists():
        print(f"  [OK] {config}")
    else:
        print(f"  [X] {config} missing")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

issues = []
if not css_file.exists() or css_file.stat().st_size < 5000:
    issues.append("Rebuild Tailwind CSS: npm run build:css")
if not node_modules.exists():
    issues.append("Install NPM packages: npm install")
if not db_file.exists():
    issues.append("Setup database: python manage.py migrate")

if issues:
    print("\n[!] ISSUES FOUND:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
    print("\n[>] Run these commands to fix:")
    for issue in issues:
        cmd = issue.split(': ')[1]
        print(f"  -> {cmd}")
else:
    print("\n[OK] ALL CHECKS PASSED!")
    print("\n[+] Your setup looks good!")
    print("\n[>] Start server: python manage.py runserver")
    print("[>] Visit: http://localhost:8000")

print("\n" + "=" * 60)
print("Test colors at: http://localhost:8000/test-colors/")
print("=" * 60)
