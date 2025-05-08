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
    handle_options_request,
    check_column_existence,
    get_hateos_location_string,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")
VALID_DAYS: List[str] = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì"]

# Create the blueprint and API
turn_bp = Blueprint(BP_NAME, __name__)
api = Api(turn_bp)


class Turn(Resource):
    """
    Class representing the Turn resource.
    This class handles the CRUD operations for the Turn resource.
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}", f"/{BP_NAME}/<int:id_>"]

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def post(self) -> Response:
        """
        Create a new turn.
        The request body must be a JSON object with application/json content type.
        """

        # Gather parameters
        data = request.get_json()
        settori: List[str] = data.get("settori")
        materie: List[str] = data.get("materie")
        data_inizio = parse_date_string(date_string=data.get("data_inizio", type=str))
        data_fine = parse_date_string(date_string=data.get("data_fine", type=str))
        ora_inizio = parse_time_string(time_string=data.get("ora_inizio", type=str))
        ora_fine = parse_time_string(time_string=data.get("ora_fine", type=str))
        giorno_inizio = data.get("giorno_inizio", type=str)
        giorno_fine = data.get("giorno_fine", type=str)
        ore = data.get("ore", type=int)
        posti = data.get("posti", type=int)
        posti_confermati = data.get("posti_confermati", type=bool)
        id_indirizzo = data.get("id_indirizzo", type=int)
        id_tutor = data.get("id_tutor", type=int)
        id_azienda = data.get("id_azienda", type=int)

        # Validate lists
        for field_name, field_value in [("settori", settori), ("materie", materie)]:
            if not isinstance(field_value, List) or not all(isinstance(item, str) for item in field_value):
                return create_response(
                    message={f"error": f"{field_name} must be a list of strings"},
                    status_code=STATUS_CODES["bad_request"],
                )

        if giorno_inizio not in VALID_DAYS:
            return create_response(
                message={"error": "invalid giorno_inizio value"},
                status_code=STATUS_CODES["bad_request"],
            )
        if giorno_fine not in VALID_DAYS:
            return create_response(
                message={"error": "invalid giorno_fine value"},
                status_code=STATUS_CODES["bad_request"],
            )
        if VALID_DAYS.index(giorno_inizio) >= VALID_DAYS.index(giorno_fine):
            return create_response(
                message={"error": "giorno_inizio must be before giorno_fine"},
                status_code=STATUS_CODES["bad_request"],
            )
        if giorno_inizio == giorno_fine:
            return create_response(
                message={"error": "giorno_inizio and giorno_fine cannot be the same"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Validate integers and perform casting if they are numeric strings
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
            "materie": ["materia", materie],
            "settori": ["settore", settori],
        }

        for table, (column, value) in pk_to_check.items():
            if value is not None:
                # Check if the value exists in the database
                result: Dict[str, Any] = fetchone_query(
                    f"SELECT COUNT(*) AS count FROM {table} WHERE {column} = %s", (value,)
                )
                if result["count"] == 0:
                    return create_response(
                        message={
                            "outcome": f"error, specified resource {table} does not exist"
                        },
                        status_code=STATUS_CODES["not_found"],
                    )

        # Insert the turn
        lastrowid, _ = execute_query(
            "INSERT INTO turni (" \
            "data_inizio, data_fine, settore, "
            "posti, ore, id_azienda, "
            "id_indirizzo, id_tutor, ora_inizio, " \
            "ora_fine, posti_confermati) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                data_inizio,
                data_fine,
                settori,
                posti,
                ore,
                id_azienda,
                id_indirizzo,
                id_tutor,
                ora_inizio,
                ora_fine,
                posti_confermati,
            ),
        )

        # Insert row into turnoSettore table
        if settori is not None:
            execute_query(
                "INSERT INTO turno_settore (id_turno, settore) VALUES (%s, %s)",
                (lastrowid, settori),
            )

        # Insert row into turnoMateria table
        if materie is not None:
            execute_query(
                "INSERT INTO turno_materia (id_turno, materia) VALUES (%s, %s)",
                (lastrowid, materie),
            )

        # Log the turn creation
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} created turn {lastrowid}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Turn.ENDPOINT_PATHS[0], "verb": "POST"},
        )

        # Return a success message
        return create_response(
            message={
                "outcome": "turn successfully created",
                "location": get_hateos_location_string(bp_name=BP_NAME, id_=lastrowid),
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def delete(self, id_) -> Response:
        """
        Delete a turn.
        The request must include the turn ID as a path variable.
        """

        # Validate the ID
        if id_ < 0:
            return create_response(
                message={"error": "id must be a positive integer"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Delete the turn
        _, rows_affected = execute_query(
            "DELETE FROM turni WHERE id_turno = %s", (id_,)
        )

        # Check if any rows were affected
        if rows_affected == 0:
            return create_response(
                message={"outcome": "specified turn does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Log the deletion
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} deleted turn {id_}",
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

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def patch(self, id_) -> Response:
        """
        Update a turn.
        The request must include the turn ID as a path variable.
        """

        # Gather parameters
        data = request.get_json()

        # Check that the specified class exists
        turn: Dict[str, Any] = fetchone_query(
            "SELECT ore FROM turni WHERE id_turno = %s",
            (id_,),  # Only fetch the ore to check existence (could be any field)
        )
        if turn is None:
            return create_response(
                message={"outcome": "specified turn does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check that the specified fields actually exist in the database
        temp = check_column_existence(
            modifiable_columns=[
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
            ],
            to_modify=list(data.keys()),
        )
        if isinstance(temp, str):
            return create_response(
                message={"error": temp}, status_code=STATUS_CODES["bad_request"]
            )

        # Build the update query
        query, params = build_update_query_from_filters(
            data=data, table_name="turni", pk_column="id_turno", pk_value=id_
        )

        # Execute the update query
        execute_query(query, params)

        # Log the update
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} updated turn {id_}",
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

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, id_) -> Response:
        """
        Get a turn by ID of its relative company.
        The request must include the turn ID as a path variable.
        """

        # Log the read
        log(
            log_type="info",
            message=(
                f"User {get_jwt_identity()} requested "
                f"turn list with company id {id_}"
            ),
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Turn.ENDPOINT_PATHS[0], "verb": "GET"},
        )

        # Check that the specified company exists
        company: Dict[str, Any] = fetchone_query(
            "SELECT ragione_sociale FROM aziende WHERE id_azienda = %s",
            (id_,),  # Only check existence (SELECT field could be any)
        )
        if company is None:
            return create_response(
                message={"outcome": "specified company not_found"},
                status_code=STATUS_CODES["not_found"],
            )

        # Get the data
        turns: List[Dict[str, Any]] = fetchall_query(
            "SELECT data_inizio, data_fine, posti, "
            "posti_occupati, ore, id_azienda, "
            "ora_inizio, "
            "ora_fine, giorno_inizio, giorno_fine "
            "FROM turni WHERE id_azienda = %s",
            (id_,),
        )

        # Check if query returned any results
        if turns is None:
            return create_response(
                message={"outcome": "no turns found for specified company"},
                status_code=STATUS_CODES["not_found"],
            )

        # Return the turn data
        return create_response(message=turns, status_code=STATUS_CODES["ok"])

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        This method returns the allowed HTTP methods for this endpoint.
        """
        return handle_options_request(resource_class=self)


api.add_resource(Turn, *Turn.ENDPOINT_PATHS)
