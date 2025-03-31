# This script will be used to validate the filters provided in a JSON by clients by comparing them to table meta data.

import mysql.connector
import json
from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_USER
from typing import List, Dict

TABLE_METADATA: List[Dict[str, List[str]]] = []

def fetch_table_metadata(exclude_primary_keys: bool):
    """
    Fetches table metadata and dumps it in a JSON file, excluding primary keys.
    """
    global TABLE_METADATA
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

        # Fetch column names for each table, excluding primary keys
        for table in tables:
            table_name = table[0]
            
            # Fetch all column names
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s;
            """, (table_name,))
            all_columns = [row[0] for row in cursor.fetchall()]
            
            # Fetch primary key columns
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.key_column_usage 
                WHERE table_name = %s AND constraint_name = 'PRIMARY';
            """, (table_name,))
            primary_keys = [row[0] for row in cursor.fetchall()]
            
            # Exclude primary keys from the column list
            if exclude_primary_keys: valid_columns = [col for col in all_columns if col not in primary_keys]
            else: valid_columns = all_columns
            
            # Append table metadata
            TABLE_METADATA.append({table_name: valid_columns})

        # Print TABLE_METADATA to stdout
        print(json.dumps(TABLE_METADATA, indent=4))

        # Save TABLE_METADATA to a JSON file
        file_name = "valid_update_values.json" if exclude_primary_keys else "valid_search_values.json"
        with open(file_name, "w") as json_file:
            json.dump(TABLE_METADATA, json_file, indent=4)

        print("Table metadata saved to valid_update_values.json")

    except Exception as e:
        print(f"Error fetching table metadata: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

# Fetch metadata when the script is run
if __name__ == "__main__":
    while True:
        what_kind_of_filters_to_generate = input("What kind of filters do you want to generate? (update/search/exit): ").strip().lower()
        if what_kind_of_filters_to_generate in ["update", "search"]:
            exclude_primary_keys = (what_kind_of_filters_to_generate == "update")
            fetch_table_metadata(exclude_primary_keys)
        elif what_kind_of_filters_to_generate == "exit":
            print("Exiting...")
            break
        else:
            print("Invalid input. Please enter 'update', 'search', or 'exit'.")