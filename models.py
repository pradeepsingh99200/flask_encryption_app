import datetime
from unittest import result
import bcrypt

from database import get_db_connection

def create_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
    conn.commit()
    cursor.close()
    conn.close()

def check_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username=%s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()


def store_file_data(filename, user_id, private_key, receiver_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now()  # Import datetime at the top of your file
    cursor.execute(
        "INSERT INTO upload (filename, user_id, privatekey, created_at, receiver_id) VALUES (%s, %s, %s, %s, %s)",
        (filename, user_id, private_key, created_at, receiver_id)
    )
    conn.commit()
    cursor.close()
    conn.close()





    