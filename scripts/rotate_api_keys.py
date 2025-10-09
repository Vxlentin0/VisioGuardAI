import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

def generate_new_api_key():
    return secrets.token_urlsafe(32)

def create_api_keys_table(db_path):
    """Create the API keys table if it doesn't exist"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS ApiKeys
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      api_key TEXT NOT NULL UNIQUE,
                      created_at TIMESTAMP NOT NULL,
                      expires_at TIMESTAMP NOT NULL,
                      is_active INTEGER DEFAULT 1,
                      revoked_at TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def store_api_key(db_path, api_key, expiration):
    """Store the new API key in the database (encrypted)"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE ApiKeys SET is_active = 0 WHERE is_active = 1")
        
        # Encrypt the key before storing
        encrypted_key = encrypt_api_key(api_key)
        
        cursor.execute('''INSERT INTO ApiKeys 
                         (api_key, created_at, expires_at, is_active)
                         VALUES (?, ?, ?, 1)''',
                      (encrypted_key, datetime.now(), expiration))
        
        conn.commit()
        print(f"Encrypted API Key stored successfully")
        
    except sqlite3.IntegrityError:
        print("Error: API key already exists")
    finally:
        conn.close()

def get_active_api_key(db_path):
    """Retrieve the currently active API key"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''SELECT api_key, expires_at 
                     FROM ApiKeys 
                     WHERE is_active = 1 
                     AND expires_at > ?
                     ORDER BY created_at DESC 
                     LIMIT 1''', (datetime.now(),))
    
    result = cursor.fetchone()
    conn.close()
    
    return result

def rotate_api_key(db_path='api_keys.db'):
    """Generate and store a new API key"""
    # Create table if it doesn't exist
    create_api_keys_table(db_path)
    
    # Generate new key
    new_key = generate_new_api_key()
    expiration = datetime.now() + timedelta(days=30)
    
    # Store in database
    store_api_key(db_path, new_key, expiration)
    
    # Update the environment variable
    os.environ["API_KEY"] = new_key
    
    return new_key

def get_or_create_encryption_key():
    """Get or create an encryption key for the database"""
    key_file = 'encryption.key'
    
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
        return key

def encrypt_api_key(api_key):
    """Encrypt the API key before storing"""
    key = get_or_create_encryption_key()
    f = Fernet(key)
    return f.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key):
    """Decrypt the API key when retrieving"""
    key = get_or_create_encryption_key()
    f = Fernet(key)
    return f.decrypt(encrypted_key.encode()).decode()

if __name__ == "__main__":
    # Specify the database path (adjust as needed)
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'api_keys.db')
    
    # Rotate the API key
    new_key = rotate_api_key(db_path)
    
    # Optionally, verify the key was stored
    active_key = get_active_api_key(db_path)
    if active_key:
        print(f"Active API Key verified in database")
        print(f"Expires at: {active_key[1]}")