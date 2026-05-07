import os
import mysql.connector

def run_sql_file():
    print("Connecting to internal Railway database...")
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cursor = connection.cursor()

        print("Reading init.sql...")
        with open('init.sql', 'r') as file:
            sql_script = file.read()

        for result in cursor.execute(sql_script, multi=True):
            pass 

        connection.commit()
        print("✅ Database successfully initialised from inside Railway!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    run_sql_file()