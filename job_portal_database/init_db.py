#!/usr/bin/env python3
"""Initialize SQLite database for job_portal_database

Sets up tables for IT job portal features: users (as applicants & employers), applicant_profiles, employers, jobs,
job_applications, including foreign keys and indexes for efficient access and relationship integrity.

Tables created:
- app_info (meta)
- users: Common base for all portal users, type-separated
- applicant_profiles: Extended applicant info
- employers: Employer org/company data & dashboard info
- jobs: IT job postings (by employer), attributes for search/filtering
- job_applications: Records of job seekers applying, with status tracking
"""

import sqlite3
import os

DB_NAME = "myapp.db"

print("Starting SQLite setup...")

# Check if database already exists
db_exists = os.path.exists(DB_NAME)
if db_exists:
    print(f"SQLite database already exists at {DB_NAME}")
    # Verify it's accessible
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("SELECT 1")
        conn.close()
        print("Database is accessible and working.")
    except Exception as e:
        print(f"Warning: Database exists but may be corrupted: {e}")
else:
    print("Creating new SQLite database...")

# Create database and tables
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Enable foreign key support
cursor.execute("PRAGMA foreign_keys = ON")

# --------------------- TABLES DEFINITION ---------------------
# Meta/information about the app
cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# All users, both applicants and employers. Type distinguishes.
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        user_type TEXT NOT NULL CHECK(user_type IN ('applicant', 'employer')),
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Applicants' extended profiles
cursor.execute("""
    CREATE TABLE IF NOT EXISTS applicant_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        phone TEXT,
        location TEXT,
        years_of_experience INTEGER,
        education TEXT,
        skills TEXT,
        summary TEXT,
        resume_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_applicant_user_id ON applicant_profiles(user_id)")

# Employers' profile/company/organization info
cursor.execute("""
    CREATE TABLE IF NOT EXISTS employers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        company_name TEXT NOT NULL,
        company_website TEXT,
        company_description TEXT,
        contact_email TEXT,
        contact_phone TEXT,
        verified INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_employer_user_id ON employers(user_id)")

# IT job postings
cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employer_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        location TEXT,
        job_type TEXT, -- e.g. Full-time, Part-time, Contract
        experience_level TEXT, -- e.g. Junior, Mid, Senior
        salary_min INTEGER,
        salary_max INTEGER,
        remote INTEGER DEFAULT 0,
        skills_required TEXT,
        posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (employer_id) REFERENCES employers(id) ON DELETE CASCADE
    )
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_employer_id ON jobs(employer_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_is_active ON jobs(is_active)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_location_type_level ON jobs(location, job_type, experience_level)")

# Applications table: link applicants to jobs + status tracking
cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        applicant_id INTEGER NOT NULL,
        job_id INTEGER NOT NULL,
        employer_id INTEGER NOT NULL,
        application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT NOT NULL DEFAULT 'applied', -- e.g., applied, reviewed, shortlisted, rejected, hired
        resume_snapshot_url TEXT, -- Static snapshot of resume if required
        cover_letter TEXT,
        FOREIGN KEY (applicant_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
        FOREIGN KEY (employer_id) REFERENCES employers(id) ON DELETE CASCADE,
        UNIQUE (applicant_id, job_id) -- Prevent duplicate applications
    )
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_applications_job_id ON job_applications(job_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_applications_applicant_id ON job_applications(applicant_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_applications_employer_id ON job_applications(employer_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_applications_status ON job_applications(status)")

# ------------- Insert/Update App Info -------------
cursor.execute("INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)", 
               ("project_name", "job_portal_database"))
cursor.execute("INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)", 
               ("version", "1.0.0"))
cursor.execute("INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)", 
               ("author", "John Doe"))
cursor.execute("INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)", 
               ("description", "IT job portal supporting applicants, employers, job postings, and applications with search/filtering capabilities."))

conn.commit()

# ------------- DATABASE SUMMARY -------------
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
tables_list = cursor.fetchall()
table_names = [row[0] for row in tables_list]

table_count = len(table_names)
cursor.execute("SELECT COUNT(*) FROM app_info")
record_count = cursor.fetchone()[0]

conn.close()

# Save connection information to a file
current_dir = os.getcwd()
connection_string = f"sqlite:///{current_dir}/{DB_NAME}"

try:
    with open("db_connection.txt", "w") as f:
        f.write(f"# SQLite connection methods:\n")
        f.write(f"# Python: sqlite3.connect('{DB_NAME}')\n")
        f.write(f"# Connection string: {connection_string}\n")
        f.write(f"# File path: {current_dir}/{DB_NAME}\n")
    print("Connection information saved to db_connection.txt")
except Exception as e:
    print(f"Warning: Could not save connection info: {e}")

# Create environment variables file for Node.js viewer
db_path = os.path.abspath(DB_NAME)

# Ensure db_visualizer directory exists
if not os.path.exists("db_visualizer"):
    os.makedirs("db_visualizer", exist_ok=True)
    print("Created db_visualizer directory")

try:
    with open("db_visualizer/sqlite.env", "w") as f:
        f.write(f"export SQLITE_DB=\"{db_path}\"\n")
    print(f"Environment variables saved to db_visualizer/sqlite.env")
except Exception as e:
    print(f"Warning: Could not save environment variables: {e}")

print("\nSQLite setup complete!")
print(f"Database: {DB_NAME}")
print(f"Location: {current_dir}/{DB_NAME}")
print("")
print("Created tables:")
for tname in table_names:
    print(f"  - {tname}")

print(f"\nDatabase statistics:")
print(f"  Tables: {table_count}")
print(f"  App info records: {record_count}")

print("\nTo use with Node.js viewer, run: source db_visualizer/sqlite.env")

print("\nTo connect to the database, use one of the following methods:")
print(f"1. Python: sqlite3.connect('{DB_NAME}')")
print(f"2. Connection string: {connection_string}")
print(f"3. Direct file access: {current_dir}/{DB_NAME}")
print("")

# If sqlite3 CLI is available, show how to use it
try:
    import subprocess
    result = subprocess.run(['which', 'sqlite3'], capture_output=True, text=True)
    if result.returncode == 0:
        print("")
        print("SQLite CLI is available. You can also use:")
        print(f"  sqlite3 {DB_NAME}")
except:
    pass

print("\nScript completed successfully.")
