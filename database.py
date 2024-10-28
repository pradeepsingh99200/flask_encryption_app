import mysql.connector
import os

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'DocEncrypt')
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
