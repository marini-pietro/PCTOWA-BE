"""
Turn blueprint module.
This module contains the Turn class, which handles the CRUD operations for the Turn resource.
"""

from os.path import basename as os_path_basename
from typing import List, Dict, Union, Any
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity, jwt_required

from config import (
    API_SERVER_HOST,
    API_SERVER_PORT,
    API_SERVER_NAME_IN_LOG,
    STATUS_CODES,
)

from .blueprints_utils import (
    check_authorization,
    fetchone_query,
    execute_query,
    log,
    create_response,
    parse_date_string,
    parse_time_string,
    fetchall_query,
    build_update_query_from_filters,
    get_class_http_verbs,
    validate_json_request,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and API
turn_bp = Blueprint(BP_NAME, __name__)
api = Api(turn_bp)


class Turn(Resource):
    """
    Class representing the Turn resource.
    This class handles the CRUD operations for the Turn resource.
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}", f"/{BP_NAME}/<int:id>"]

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def post(self) -> Response:
        """
        Create a new turn.
        The request body must be a JSON object with application/json content type.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Gather parameters
        settore = data.get("settore")
        materia = data.get("materia")
        data_inizio = parse_date_string(date_string=data.get("data_inizio"))
        data_fine = parse_date_string(date_string=data.get("data_fine"))
        ora_inizio = parse_time_string(time_string=data.get("ora_inizio"))
        ora_fine = parse_time_string(time_string=data.get("ora_fine"))
        giorno_inizio = data.get("giorno_inizio")
        giorno_fine = data.get("giorno_fine")
        ore = data.get("ore")
        posti = data.get("posti")
        id_indirizzo = data.get("id_indirizzo")
        id_tutor = data.get("id_tutor")
        id_azienda = data.get("id_azienda")

        # Validate data
        valid_days: List[str] = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì"]
        if giorno_inizio not in valid_days:
            return create_response(
                message={"error": "invalid giorno_inizio value"},
                status_code=STATUS_CODES["bad_request"],
            )
        if giorno_fine not in valid_days:
            return create_response(
                message={"error": "invalid giorno_fine value"},
                status_code=STATUS_CODES["bad_request"],
            )
        if valid_days.index(giorno_inizio) >= valid_days.index(giorno_fine):
            return create_response(
                message={"error": "giorno_inizio must be before giorno_fine"},
                status_code=STATUS_CODES["bad_request"],
            )
        if giorno_inizio == giorno_fine:
            return create_response(
                message={"error": "giorno_inizio and giorno_fine cannot be the same"},
                status_code=STATUS_CODES["bad_request"],
            )

        values_to_check: Dict[str, int] = {
            "ore": ore,
            "posti": posti,
            "id_indirizzo": id_indirizzo,
            "id_tutor": id_tutor,
            "id_azienda": id_azienda,
        }
        for key, value in values_to_check.items():
            if value is not None:
                try:
                    values_to_check[key] = int(value)
                except (ValueError, TypeError):
                    return create_response(
                        message={"error": f"invalid {key} value"},
                        status_code=STATUS_CODES["bad_request"],
                    )

        # CHECK THAT VALUES PROVIDED ACTUALLY EXIST IN THE DATABASE
        pk_to_check: Dict[str, List[Union[str, Any]]] = {
            "aziende": ["id_azienda", id_azienda],
            "indirizzi": ["id_indirizzo", id_indirizzo],
            "tutor": ["id_tutor", id_tutor],
            "materie": ["materia", materia],
            "settori": ["settore", settore],
        }
        for table, (column, value) in pk_to_check.items():
            if value is not None:
                # Check if the value exists in the database
                result: Dict[str, Any] = fetchone_query(
                    f"SELECT * FROM {table} WHERE {column} = %s", (value,)
                )
                if result is None:
                    return create_response(
                        message={
                            "outcome": f"error, specified row in table {table} does not exist"
                        },
                        status_code=STATUS_CODES["not_found"],
                    )

        # Insert the turn
        lastrowid: int = execute_query(
            "INSERT INTO turni (data_inizio, data_fine, settore, posti, ore, id_azienda, id_indirizzo, id_tutor, ora_inizio, ora_fine) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                data_inizio,
                data_fine,
                settore,
                posti,
                ore,
                id_azienda,
                id_indirizzo,
                id_tutor,
                ora_inizio,
                ora_fine,
            ),
        )

        # Insert row into turnoSettore table
        if settore is not None:
            execute_query(
                "INSERT INTO turnoSettore (idTurno, settore) VALUES (%s, %s)",
                (lastrowid, settore),
            )

        # Insert row into turnoMateria table
        if materia is not None:
            execute_query(
                "INSERT INTO turnoMateria (idTurno, materia) VALUES (%s, %s)",
                (lastrowid, materia),
            )

        # Log the turn creation
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} created turn {lastrowid}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Turn.ENDPOINT_PATHS[0], "verb": "POST"},
        )

        # Return a success message
        return create_response(
            message={
                "outcome": "turn successfully created",
                "location": f"http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/{BP_NAME}/{lastrowid}",
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def delete(self, id_) -> Response:
        """
        Delete a turn.
        The request must include the turn ID as a path variable.
        """

        # Check that the specified turn exists
        turn: Dict[str, Any] = fetchone_query(
            "SELECT posti_occupati FROM turni WHERE idTurno = %s", (id_,)
        )  # Only fetch the province to check existence (could be any field)
        if turn is None:
            return create_response(
                message={"outcome": "specified turn does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Delete the turn
        execute_query("DELETE FROM turni WHERE idTurno = %s", (id_,))

        # Log the deletion
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} deleted turn {id_}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Turn.ENDPOINT_PATHS[1], "verb": "DELETE"},
        )

        # Return a success message
        return create_response(
            message={"outcome": "turn successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def patch(self, id_) -> Response:
        """
        Update a turn.
        The request must include the turn ID as a path variable.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Check that the specified class exists
        turn: Dict[str, Any] = fetchone_query(
            "SELECT * FROM turni WHERE idTurno = %s", (id_,)
        )
        if not turn:
            return create_response(
                message={"outcome": "specified turn does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check that the specified fields actually exist in the database
        modifiable_columns: List[str] = [
            "data_inizio",
            "data_fine",
            "posti",
            "posti_occupati",
            "ore",
            "id_azienda",
            "id_tutor",
            "id_indirizzo",
            "ora_inizio",
            "ora_fine",
            "giorno_inizio",
            "giorno_fine",
        ]
        to_modify: List[str] = list(data.keys())
        error_columns: List[str] = [
            field for field in to_modify if field not in modifiable_columns
        ]
        if error_columns:
            return create_response(
                message={
                    "outcome": f"error, field(s) {error_columns} do not exist or cannot be modified"
                },
                status_code=STATUS_CODES["bad_request"],
            )

        # Build the update query
        query, params = build_update_query_from_filters(
            data=data, table_name="turni", id_column="idTurno", id_value=id_
        )

        # Execute the update query
        execute_query(query, params)

        # Log the update
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} updated turn {id_}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Turn.ENDPOINT_PATHS[1], "verb": "PATCH"},
        )

        # Return a success message
        return create_response(
            message={"outcome": "turn successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, company_id) -> Response:
        """
        Get a turn by ID of its relative company.
        The request must include the turn ID as a path variable.
        """

        # Log the read
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} requested turn list with company id {company_id}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Turn.ENDPOINT_PATHS[0], "verb": "GET"},
        )

        # Check that the specified company exists
        company: Dict[str, Any] = fetchone_query(
            "SELECT * FROM aziende WHERE id_azienda = %s", (company_id,)
        )
        if not company:
            return create_response(
                message={"outcome": "specified company not_found"},
                status_code=STATUS_CODES["not_found"],
            )

        # Get the data
        turns: List[Dict[str, Any]] = fetchall_query(
            "SELECT data_inizio, data_fine, posti, posti_occupati, ore, id_azienda, id_tutor, indirizzo, ora_inizio, ora_fine, giorno_inizio, giorno_fine FROM turni WHERE id_azienda = %s",
            (company_id,),
        )

        # Check if query returned any results
        if not turns:
            return create_response(
                message={"outcome": "no turns found for specified company"},
                status_code=STATUS_CODES["not_found"],
            )

        # Return the turn data
        return create_response(message=turns, status_code=STATUS_CODES["ok"])

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        This method returns the allowed HTTP methods for this endpoint.
        """
        # Define allowed methods
        allowed_methods = get_class_http_verbs(type(self))

        # Create the response
        response = Response(status=STATUS_CODES["ok"])
        response.headers["Allow"] = ", ".join(allowed_methods)
        response.headers["Access-Control-Allow-Origin"] = (
            "*"  # Adjust as needed for CORS
        )
        response.headers["Access-Control-Allow-Methods"] = ", ".join(allowed_methods)
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

        return response


api.add_resource(Turn, *Turn.ENDPOINT_PATHS)
