import json
from flask import jsonify

def validate_filters(data, table_name):

    # Validate filters
        with open('../table_metadata.json') as metadata_file:
            try:
                metadata = json.load(metadata_file)
                indirizzi_available_filters = metadata.get(f'{table_name}', [])
                if not isinstance(indirizzi_available_filters, list) or not all(isinstance(item, str) for item in indirizzi_available_filters):
                    return jsonify({'error': f'invalid {table_name} column values in metadata'}), 400
                
                # Get list of keys in data json
                filters_key = list(data.keys()) if isinstance(data, dict) else []

                # Check if any filter key is not in indirizzi_filters
                invalid_filters = [key for key in filters_key if key not in indirizzi_available_filters]
                if invalid_filters:
                    return jsonify({'error': f'Invalid filter(s): {", ".join(invalid_filters)}'}), 400

            except json.JSONDecodeError:
                return jsonify({'error': 'failed to parse metadata file'}), 500