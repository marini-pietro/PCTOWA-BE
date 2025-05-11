"""
Student API Blueprint
"""

from os.path import basename as os_path_basename
from typing import List, Dict, Any
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from marshmallow import fields, ValidationError
from marshmallow.validate import Regexp
from mysql.connector import IntegrityError
from api_server import ma

from config import (
    STATUS_CODES,
)

from .blueprints_utils import (
    check_authorization,
    fetchone_query,
    fetchall_query,
    execute_query,
    log,
    create_response,
    build_update_query_from_filters,
    handle_options_request,
    check_column_existence,
    get_hateos_location_string,
    jwt_validation_required,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and API
student_bp = Blueprint(BP_NAME, __name__)
api = Api(student_bp)


# Marshmallow schema for Student resource
class StudentSchema(ma.Schema):
    """
    Schema for validating and deserializing student data.
    """
    matricola = fields.String(
        required=True,
        validate=Regexp(
            r"^\d{5}$", error="matricola must be a string of exactly 5 digits"
        ),
        error_messages={
            "required": "matricola is required.",
            "invalid": "matricola must be a string of exactly 5 digits.",
        },
    )
    nome = fields.String(
        required=True, error_messages={"required": "nome is required."}
    )
    cognome = fields.String(
        required=True, error_messages={"required": "cognome is required."}
    )
    id_classe = fields.Integer(
        required=True,
        error_messages={
            "required": "id_classe is required.",
            "invalid": "id_classe must be an integer.",
        },
    )


student_schema = StudentSchema()
student_schema_partial = StudentSchema(partial=True)


class Student(Resource):
    """
    Endpoint to manage students.
    """

    ENDPOINT_PATHS = [
        f"/{BP_NAME}/<int:matricola>",  # For endpoints like DELETE or PATCH
    ]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def post(self, identity) -> Response:
        """
        Create a new student.
        The request body must be a JSON object with application/json content type.
        """

        # Validate and deserialize input using Marshmallow
        try:
            data = student_schema.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        matricola: str = data["matricola"]
        nome: str = data["nome"]
        cognome: str = data["cognome"]
        id_classe: int = data["id_classe"]

        # Log the student creation
        log(
            log_type="info",
            message=f"User {identity} created student {matricola}",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        try:
            # Insert the student
            lastrowid, _ = execute_query(
                "INSERT INTO studenti VALUES (%s, %s, %s, %s)",
                (matricola, nome, cognome, id_classe),
            )
        except IntegrityError as ex:
            log(
                log_type="error",
                message=(
                    f"User {identity} tried to create student {matricola} "
                    f"but it already generated {ex}"
                ),
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )
            return create_response(
                message={"error": "conflict error"},
                status_code=STATUS_CODES["conflict"],
            )
        except (ValueError, TypeError) as ex:
            log(
                log_type="error",
                message=(
                    f"User {identity} failed to create student {matricola} "
                    f"with error: {str(ex)}"
                ),
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )
            return create_response(
                message={"error": "internal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

        return create_response(
            message={
                "outcome": "student successfully created",
                "location": get_hateos_location_string(bp_name=BP_NAME, id_=lastrowid),
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def delete(self, matricola, identity) -> Response:
        """
        Delete a student.
        The request must include the student matricola as a path variable.
        """

        # Delete the student
        _, rows_affected = execute_query(
            "DELETE FROM studenti WHERE matricola = %s", (matricola,)
        )

        # Check if any rows were affected
        if rows_affected == 0:
            return create_response(
                message={"error": "no student found with the provided matricola"},
                status_code=STATUS_CODES["not_found"],
            )

        # Log the deletion
        log(
            log_type="info",
            message=f"User {identity} deleted student {matricola}",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={"outcome": "student successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def patch(self, matricola, identity) -> Response:
        """
        Update a student.
        The request must include the student matricola as a path variable.
        """

        # Validate and deserialize input using Marshmallow (partial update)
        try:
            data = student_schema_partial.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        # Log the update
        log(
            log_type="info",
            message=f"User {identity} updated student {matricola}",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Check that the specified student exists using EXISTS keyword
        student_exists: bool = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM studenti WHERE matricola = %s) AS ex",
            (matricola,),
        )["ex"]
        if not student_exists:
            return create_response(
                message={"outcome": "error, specified student does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check that the specified fields actually exist in the database
        temp = check_column_existence(
            modifiable_columns=["nome", "cognome", "id_classe", "comune"],
            to_modify=list(data.keys()),
        )
        if isinstance(temp, str):
            return create_response(
                message={"outcome": temp},
                status_code=STATUS_CODES["bad_request"],
            )

        # Build the update query
        query, params = build_update_query_from_filters(
            data=data, table_name="studenti", pk_column="matricola", pk_value=matricola
        )

        # Update the student
        execute_query(query, params)

        # Return a success message
        return create_response(
            message={"outcome": "student successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, matricola, identity) -> Response:
        """
        Get students data by matricola.
        The request must include the student matricola as a path variable.
        """

        # Log the request
        log(
            log_type="info",
            message=(f"User {identity} requested student {matricola}"),
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Get student data
        student: List[Dict[str, Any]] = fetchall_query(
            """
            SELECT matricola, nome, cognome, comune, id_classe
            FROM studenti
            WHERE matricola = %s
            """,
            (matricola,),
        )

        # Check if the student exists
        if student is None:
            return create_response(
                message={"outcome": "no student found with the provided matricola"},
                status_code=STATUS_CODES["not_found"],
            )

        # Return the response
        return create_response(message=student, status_code=STATUS_CODES["ok"])

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS request for the Student resource.
        """

        return handle_options_request(resource_class=self)


class BindStudentToTurnSchema(ma.Schema):
    """
    Schema for validating and deserializing data for binding a student to a turn.
    """
    id_turno = fields.Integer(required=True)


bind_student_to_turn_schema = BindStudentToTurnSchema()


class BindStudentToTurn(Resource):
    """
    Endpoint to bind a student to a turn.
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}/bind/<int:matricola>"]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def post(self, matricola, identity) -> Response:
        """
        Bind a student to a turn.
        The request must include the student matricola as a path variable.
        """

        # Validate and deserialize input using Marshmallow
        try:
            data = bind_student_to_turn_schema.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        id_turno: int = data["id_turno"]

        # Check that the student exists using EXISTS keyword
        student_exists: bool = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM studenti WHERE matricola = %s) AS ex",
            (matricola,),
        )["ex"]
        if not student_exists:
            return create_response(
                message={"error": "student not_found"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check that the turn exists using EXISTS keyword
        turn_exists: bool = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM turni WHERE id_turno = %s) AS ex",
            (id_turno,),
        )["ex"]
        if not turn_exists:
            return create_response(
                message={"error": "turn not_found"},
                status_code=STATUS_CODES["not_found"],
            )

        # Bind the student to the turn
        try:
            execute_query(
                query="INSERT INTO studenteTurno (matricola, id_turno) VALUES (%s, %s)",
                params=(matricola, id_turno),
            )

            # Log the binding
            log(
                log_type="info",
                message=(
                    f"User {identity} bound student {matricola} " f"to turn {id_turno}"
                ),
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )
            return create_response(
                message={"outcome": "student successfully bound to turn"},
                status_code=STATUS_CODES["created"],
            )
        except IntegrityError as ex:
            log(
                log_type="error",
                message=(
                    f"User {identity} tried to bind student {matricola} "
                    f"to turn {id_turno} but it already generated {ex}"
                ),
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )
            return create_response(
                message={"error": "conflict error"},
                status_code=STATUS_CODES["conflict"],
            )
        except (ValueError, TypeError) as ex:
            log(
                log_type="error",
                message=(
                    f"User {identity} failed to bind student {matricola} "
                    f"to turn {id_turno} with error: {str(ex)}"
                ),
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )
            return create_response(
                message={"error": "internal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS request for the BindStudentToTurn resource.
        """
        return handle_options_request(resource_class=self)


class StudentListFromClass(Resource):
    """
    Endpoint to get a list of all students associated with a specific class.
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}/class_list/<int:class_id>"]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, class_id, identity) -> Response:
        """
        Get a list of all students that are associated
        to a class passed by its id_ as a path variable.
        """

        # Log the request
        log(
            log_type="info",
            message=(
                f"User {identity} requested student list "
                f"that are associated to class {class_id}"
            ),
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Check if the class exists using EXISTS keyword
        class_exists: bool = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM classi WHERE id_classe = %s) AS ex",
            (class_id,),
        )["ex"]
        if not class_exists:
            return create_response(
                message={"outcome": "no class found with the provided id"},
                status_code=STATUS_CODES["not_found"],
            )

        # Get student data
        student_data: List[Dict[str, Any]] = fetchall_query(
            """
            SELECT S.matricola, S.nome, S.cognome, 
                S.comune, T.id_turno, T.data_inizio, 
                T.data_fine, T.giorno_inizio, T.giorno_fine, 
                T.ora_inizio, T.ora_fine, T.ore,
                A.ragione_sociale, I.stato, I.provincia, I.comune AS comuneAzienda,
                I.cap, I.indirizzo AS indirizzoAzienda
            FROM studenti AS S
            LEFT JOIN studente_turno AS ST ON S.matricola = ST.matricola
            LEFT JOIN turni AS T ON ST.id_turno = T.id_turno
            LEFT JOIN aziende AS A ON T.id_azienda = A.id_azienda
            LEFT JOIN indirizzi AS I ON T.id_indirizzo = I.id_indirizzo
            WHERE S.id_classe = %s
            """,
            (class_id,),
        )

        # Check if student_data is empty
        if not student_data:
            return create_response(
                message={"outcome": "no students found for the provided class_id"},
                status_code=STATUS_CODES["not_found"],
            )

        # Build the output JSON
        students = []
        student_map = {}
        for row in student_data:
            matricola = row.get("matricola")
            if matricola not in student_map:
                student = {
                    "matricola": matricola,
                    "nome": row.get("nome"),
                    "cognome": row.get("cognome"),
                    "comune": row.get("comune"),
                    "turn": None,
                }
                students.append(student)
                student_map[matricola] = student

            if row.get("id_turno"):
                student_map[matricola]["turn"] = {
                    "ragione_sociale": row.get("ragione_sociale"),
                    "data_inizio": row.get("data_inizio"),
                    "data_fine": row.get("data_fine"),
                    "giorno_inizio": row.get("giorno_inizio"),
                    "giorno_fine": row.get("giorno_fine"),
                    "ora_inizio": row.get("ora_inizio"),
                    "ora_fine": row.get("ora_fine"),
                    "ore": row.get("ore"),
                    "turnoPK": row.get("id_turno"),
                    "indirizzo": {
                        "stato": row.get("stato"),
                        "provincia": row.get("provincia"),
                        "comune": row.get("comuneAzienda"),
                        "cap": row.get("cap"),
                        "indirizzo": row.get("indirizzoAzienda"),
                    },
                }

        # Return the response
        return create_response(message=students, status_code=STATUS_CODES["ok"])

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS request for the StudentListFromClass resource.
        """

        return handle_options_request(resource_class=self)


class StudentListFromTurn(Resource):
    """
    Endpoint to get a list of all students associated with a specific turn.
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}/list/<int:turn_id>"]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, turn_id, identity) -> Response:
        """
        Get a list of all students that are associated
        to a turn passed by its id_ as a path variable.
        """
        # Log the request
        log(
            log_type="info",
            message=(
                f"User {identity} requested student list "
                f"that are associated to turn {turn_id}"
            ),
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Check if the turn exists using EXISTS keyword
        turn_exists: bool = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM turni WHERE id_turno = %s) AS ex",
            (turn_id,),
        )["ex"]
        if not turn_exists:
            return create_response(
                message={"outcome": "no turn found with the provided id_"},
                status_code=STATUS_CODES["not_found"],
            )

        # Get all students
        students: List[Dict[str, Any]] = fetchall_query(
            query="SELECT S.matricola, S.nome, S.cognome, S.comune "
            "FROM studenti AS S "
            "JOIN studenteTurno AS ST ON S.matricola = ST.matricola "
            "JOIN turni AS T ON ST.id_turno = T.id_turno "
            "WHERE T.id_turno = %s",
            params=(turn_id,),
        )

        # Return the response
        return create_response(message=students, status_code=STATUS_CODES["ok"])

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS request for the StudentListFromTurn resource.
        """
        return handle_options_request(resource_class=self)


api.add_resource(Student, *Student.ENDPOINT_PATHS)
api.add_resource(BindStudentToTurn, *BindStudentToTurn.ENDPOINT_PATHS)
api.add_resource(StudentListFromTurn, *StudentListFromTurn.ENDPOINT_PATHS)
api.add_resource(StudentListFromClass, *StudentListFromClass.ENDPOINT_PATHS)
