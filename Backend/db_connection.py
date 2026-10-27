
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        port=int(os.getenv("DB_PORT", "3306")),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

if __name__ == "__main__":
    try:
        connection = get_db_connection()

        print("Database connected successfully!")

        connection.close()
        print("Connection closed.")

    except mysql.connector.Error as error:
        print("Database connection failed:", error)
