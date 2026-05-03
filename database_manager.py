import sqlite3
import bcrypt

# This is the file that will be created on the admin's computer next to server.py
DB_NAME = "royal_td_users.db"


def init_db():
    """Creates the database and the users table if it doesn't exist yet."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized.")


def register_user(username, password):
    """Hashes the password and saves the new user. Returns True if successful."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt)

    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                       (username, hashed_pw))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        # This triggers if the username already exists because of the UNIQUE constraint
        success = False

    conn.close()
    return success


def verify_login(username, password):
    """Checks if the password matches the stored hash. Returns True if valid."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        # result[0] is the hashed password from the database
        stored_hash = result[0]
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

    return False


# You can add a quick test here that only runs if you execute this file directly
if __name__ == "__main__":
    init_db()
    # Test registration
    if register_user("Player1", "mysecretpassword"):
        print("User registered!")
    else:
        print("Username already exists.")

    # Test login
    if verify_login("Player1", "mysecretpassword"):
        print("Login successful!")
    else:
        print("Login failed.")