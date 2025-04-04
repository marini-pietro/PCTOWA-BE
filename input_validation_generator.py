# This script generates a JSON file containing table names, column names, their data types, and nullability.

import mysql.connector
import json
from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_USER
from typing import List, Dict

def fetch_column_metadata():
    """
    Fetches column metadata (data type and nullability) for each table in the database and saves it in a JSON file.
    """
    column_metadata: Dict[str, List[Dict[str, str]]] = {}
    try:
        # Connect to the database
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("Connection successful.\n")
        cursor = connection.cursor()
        
        # Fetch all table names
        cursor.execute(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{DB_NAME}';
        """)
        tables = cursor.fetchall()

        # Fetch column metadata for each table
        for table in tables:
            table_name = table[0]
            
            # Fetch column names, data types, and nullability
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = %s;
            """, (table_name,))
            columns = cursor.fetchall()
            
            # Append table metadata
            column_metadata[table_name] = [
                {
                    "column_name": column[0],
                    "data_type": column[1],
                    "is_nullable": column[2] == "YES"
                }
                for column in columns
            ]

        # Print column_metadata to stdout
        print(json.dumps(column_metadata, indent=4))

        # Save column_metadata to a JSON file
        file_name = "input_validation.json"
        with open(file_name, "w") as json_file:
            json.dump(column_metadata, json_file, indent=4)

        print(f"Column metadata saved to {file_name}")

    except Exception as e:
        print(f"Error fetching column metadata: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

# Fetch column metadata when the script is run
if __name__ == "__main__":
    fetch_column_metadata()