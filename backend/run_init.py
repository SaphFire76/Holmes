import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def run_sql_file():
    print("Connecting to Railway database across the internet...")
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"), # <-- This is the magic key for the public door!
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cursor = connection.cursor()

        print("Reading init.sql...")
        with open('init.sql', 'r') as file:
            sql_script = file.read()

        print("Executing SQL commands...")
        for result in cursor.execute(sql_script, multi=True):
            pass 

        connection.commit()
        print("✅ Database successfully initialized from your local machine!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    run_sql_file()