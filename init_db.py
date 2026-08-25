import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def initialize_db():
    conn = sqlite3.connect("app_data.db")
    cursor = conn.cursor()
    
    # Add a password_hash column to the users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    
    # Insert default users if the table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        admin_pw = hash_password("admin123")
        employee_pw = hash_password("emp123")
        
        cursor.execute("INSERT INTO users (name, role, password_hash) VALUES (?, ?, ?)", 
                       ("Admin", "manager", admin_pw))
        cursor.execute("INSERT INTO users (name, role, password_hash) VALUES (?, ?, ?)", 
                       ("Alex", "employee", employee_pw))
        
    conn.commit()
    conn.close()
