import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def run_sql_file():
    print("Connecting to Railway database across the internet...")
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cursor = connection.cursor()

        print("Reading init.sql...")
        with open('init.sql', 'r', encoding='utf-8') as file:
            sql_script = file.read()

        print("Parsing SQL commands intelligently...")
        
        delimiter = ';'
        statements = []
        current_statement = []

        # Read the file line by line
        for line in sql_script.split('\n'):
            line = line.strip()
            
            # Skip empty lines and single-line comments
            if not line or line.startswith('--'):
                continue
            
            # If the line is a DELIMITER command, change our cut-off rule and skip the line
            if line.upper().startswith('DELIMITER'):
                delimiter = line.split()[1]
                continue
            
            current_statement.append(line)
            
            # If the line ends with our current delimiter, the block is finished!
            if line.endswith(delimiter):
                stmt = '\n'.join(current_statement)
                # Remove the delimiter from the string before executing
                stmt = stmt[:-len(delimiter)].strip()
                if stmt:
                    statements.append(stmt)
                current_statement = []

        print(f"Found {len(statements)} commands. Executing...")
        for i, stmt in enumerate(statements):
            cursor.execute(stmt)

        connection.commit()
        print("✅ All tables and stored procedures successfully created!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    run_sql_file()