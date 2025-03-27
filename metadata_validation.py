# This script will be used to validate the filters provided in a JSON by clients by comparing them to table meta data.
# Each time the api_server is ran this script will request table meta data from database in order to provide column names.

import mysql.connector
import json
from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_USER
from typing import List, Dict

TABLE_METADATA: List[Dict[str, List[str]]] = []

def fetch_table_metadata():
    """
    Fetches table metadata and dumps it in json file.
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

        # Fetch column names for each table
        for table in tables:
            table_name = table[0]
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s;
            """, (table_name,))
            columns = [row[0] for row in cursor.fetchall()]
            TABLE_METADATA.append({table_name: columns})

        # Print TABLE_METADATA to stdout
        print(TABLE_METADATA)

        # Save TABLE_METADATA to a JSON file
        with open("table_metadata.json", "w") as json_file:
            json.dump(TABLE_METADATA, json_file, indent=4)

    except Exception as e:
        print(f"Error fetching table metadata: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

# Fetch metadata when the script is run
fetch_table_metadata()

