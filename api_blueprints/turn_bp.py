"""
Turn blueprint module.
This module contains the Turn class, which handles the CRUD operations for the Turn resource.
"""

from os.path import basename as os_path_basename
from typing import List, Dict, Union, Any
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import fields, ValidationError
from marshmallow import validates_schema
from marshmallow.validate import Regexp, Range
from api_server import ma

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
    fetchall_query,
    build_update_query_from_filters,
    handle_options_request,
    check_column_existence,
    get_hateos_location_string,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py")
VALID_DAYS: List[str] = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì"]

# Create the blueprint and API
turn_bp = Blueprint(BP_NAME, __name__)
api = Api(turn_bp)


# Marshmallow schema for Turn resource
class TurnSchema(ma.Schema):
    settori = fields.List(fields.String(), required=True)
    materie = fields.List(fields.String(), required=True)
    data_inizio = fields.Date(
        required=True,
        error_messages={
            "required": "data_inizio is required.",
            "invalid": "data_inizio must be a valid date in YYYY-MM-DD format.",
        },
    )
    data_fine = fields.Date(
        required=True,
        error_messages={
            "required": "data_fine is required.",
            "invalid": "data_fine must be a valid date in YYYY-MM-DD format.",
        },
    )
    ora_inizio = fields.Time(
        required=True,
        format="%H:%M",
        error_messages={
            "required": "ora_inizio is required.",
            "invalid": "ora_inizio must be in the format HH:MM (e.g. 18:30).",
        },
    )
    ora_fine = fields.Time(
        required=True,
        format="%H:%M",
        error_messages={
            "required": "ora_fine is required.",
            "invalid": "ora_fine must be in the format HH:MM (e.g. 18:30).",
        },
    )
    giorno_inizio = fields.String(
        required=True,
        validate=Regexp(
            r"^(lunedì|martedì|mercoledì|giovedì|venerdì)$",
            error="giorno_inizio must be a valid weekday (lunedì, martedì, mercoledì, giovedì, venerdì)",
        ),
        error_messages={"required": "giorno_inizio is required."},
    )
    giorno_fine = fields.String(
        required=True,
        validate=Regexp(
            r"^(lunedì|martedì|mercoledì|giovedì|venerdì)$",
            error="giorno_fine must be a valid weekday (lunedì, martedì, mercoledì, giovedì, venerdì)",
        ),
        error_messages={"required": "giorno_fine is required."},
    )
    ore = fields.Integer(
        required=True,
        validate=Range(min=1, error="ore must be a positive integer"),
        error_messages={"required": "ore is required."},
    )
    posti = fields.Integer(
        required=True,
        validate=Range(min=1, error="posti must be a positive integer"),
        error_messages={"required": "posti is required."},
    )
    posti_confermati = fields.Boolean(required=True)
    id_indirizzo = fields.Integer(
        required=True,
        validate=Range(min=1, error="id_indirizzo must be a positive integer"),
        error_messages={"required": "id_indirizzo is required."},
    )
    id_tutor = fields.Integer(
        required=True,
        validate=Range(min=1, error="id_tutor must be a positive integer"),
        error_messages={"required": "id_tutor is required."},
    )
    id_azienda = fields.Integer(
        required=True,
        validate=Range(min=1, error="id_azienda must be a positive integer"),
        error_messages={"required": "id_azienda is required."},
    )

    @validates_schema
    def validate_giorni(self, data, **kwargs):
        giorno_inizio = data.get("giorno_inizio")
        giorno_fine = data.get("giorno_fine")
        if giorno_inizio and giorno_fine:
            try:
                idx_inizio = VALID_DAYS.index(giorno_inizio)
                idx_fine = VALID_DAYS.index(giorno_fine)
            except ValueError:
                raise ValidationError(
                    "giorno_inizio and giorno_fine must be valid weekdays.",
                    field_name="giorno_inizio",
                )
            if idx_fine <= idx_inizio:
                raise ValidationError(
                    "giorno_fine must be work day after giorno_inizio.",
                    field_name="giorno_fine",
                )


turn_schema = TurnSchema()


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

        # Validate and deserialize input using Marshmallow
        try:
            data = turn_schema.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        settori: List[str] = data["settori"]
        materie: List[str] = data["materie"]
        data_inizio = data["data_inizio"]
        data_fine = data["data_fine"]
        ora_inizio = data["ora_inizio"]
        ora_fine = data["ora_fine"]
        giorno_inizio = data["giorno_inizio"]
        giorno_fine = data["giorno_fine"]
        ore = data["ore"]
        posti = data["posti"]
        posti_confermati = data["posti_confermati"]
        id_indirizzo = data["id_indirizzo"]
        id_tutor = data["id_tutor"]
        id_azienda = data["id_azienda"]

        # Validate days
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

        # CHECK THAT VALUES PROVIDED ACTUALLY EXIST IN THE DATABASE
        pk_to_check: Dict[str, List[Union[str, Any]]] = {
            "aziende": ["id_azienda", id_azienda],
            "indirizzi": ["id_indirizzo", id_indirizzo],
            "tutor": ["id_tutor", id_tutor],
        }
        for table, (column, value) in pk_to_check.items():
            if value is not None:
                result: Dict[str, Any] = fetchone_query(
                    f"SELECT COUNT(*) AS count FROM {table} WHERE {column} = %s",
                    (value,),
                )
                if result["count"] == 0:
                    return create_response(
                        message={
                            "outcome": f"error, specified resource {table} does not exist"
                        },
                        status_code=STATUS_CODES["not_found"],
                    )

        # Check materie and settori existence
        for materia in materie:
            result = fetchone_query(
                "SELECT COUNT(*) AS count FROM materie WHERE materia = %s", (materia,)
            )
            if result["count"] == 0:
                return create_response(
                    message={
                        "outcome": f"error, specified materia '{materia}' does not exist"
                    },
                    status_code=STATUS_CODES["not_found"],
                )
        for settore in settori:
            result = fetchone_query(
                "SELECT COUNT(*) AS count FROM settori WHERE settore = %s", (settore,)
            )
            if result["count"] == 0:
                return create_response(
                    message={
                        "outcome": f"error, specified settore '{settore}' does not exist"
                    },
                    status_code=STATUS_CODES["not_found"],
                )

        # Insert the turn
        lastrowid, _ = execute_query(
            "INSERT INTO turni ("
            "data_inizio, data_fine, settore, "
            "posti, ore, id_azienda, "
            "id_indirizzo, id_tutor, ora_inizio, "
            "ora_fine, posti_confermati, giorno_inizio, giorno_fine) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                data_inizio,
                data_fine,
                ",".join(settori),
                posti,
                ore,
                id_azienda,
                id_indirizzo,
                id_tutor,
                ora_inizio,
                ora_fine,
                posti_confermati,
                giorno_inizio,
                giorno_fine,
            ),
        )

        # Insert rows into turno_settore table
        for settore in settori:
            execute_query(
                "INSERT INTO turno_settore (id_turno, settore) VALUES (%s, %s)",
                (lastrowid, settore),
            )

        # Insert rows into turno_materia table
        for materia in materie:
            execute_query(
                "INSERT INTO turno_materia (id_turno, materia) VALUES (%s, %s)",
                (lastrowid, materia),
            )

        # Log the turn creation
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} created turn {lastrowid}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
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
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
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

        # Validate and deserialize input using Marshmallow (partial update)
        try:
            data = turn_schema.load(request.get_json(), partial=True)
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

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
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
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
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
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
