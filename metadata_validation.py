# This script will be used to validate the filters provided in a JSON by clients by comparing them to table meta data.

import mysql.connector
import json
from config import DB_HOST, DB_NAME, REDACTED_PASSWORD, REDACTED_USER
from typing import List, Dict

TABLE_METADATA: List[Dict[str, List[str]]] = []

def fetch_table_metadata():
    """
    Fetches table metadata and dumps it in a JSON file, excluding primary keys.
    """
    global TABLE_METADATA
    try:
        # Connect to the database
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=REDACTED_USER,
            password=REDACTED_PASSWORD
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
            non_primary_columns = [col for col in all_columns if col not in primary_keys]
            
            # Append table metadata
            TABLE_METADATA.append({table_name: non_primary_columns})

        # Print TABLE_METADATA to stdout
        print(json.dumps(TABLE_METADATA, indent=4))

        # Save TABLE_METADATA to a JSON file
        with open("table_metadata.json", "w") as json_file:
            json.dump(TABLE_METADATA, json_file, indent=4)

        print("Table metadata saved to table_metadata.json")

    except Exception as e:
        print(f"Error fetching table metadata: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

# Fetch metadata when the script is run
fetch_table_metadata()