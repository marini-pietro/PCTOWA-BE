"""
Student API Blueprint
"""

from os.path import basename as os_path_basename
from typing import List, Dict, Union, Any
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity, jwt_required
from mysql.connector import IntegrityError

from config import (
    API_SERVER_HOST,
    API_SERVER_NAME_IN_LOG,
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
    validate_json_request,
    check_column_existence,
    get_hateos_location_string,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and API
student_bp = Blueprint(BP_NAME, __name__)
api = Api(student_bp)


class Student(Resource):
    """
    Endpoint to manage students.
    """

    ENDPOINT_PATHS = [
        f"/{BP_NAME}/<int:matricola>",  # For endpoints like DELETE or PATCH
        f"/{BP_NAME}/class/<int:class_id>",  # For endpoints like GET
    ]

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def post(self) -> Response:
        """
        Create a new student.
        The request body must be a JSON object with application/json content type.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Gather parameters
        matricola: str = data.get("matricola")
        nome: str = data.get("nome")
        cognome: str = data.get("cognome")
        id_classe: int = data.get("id_classe")

        # Validate parameters
        if matricola is None or nome is None or cognome is None or id_classe is None:
            return create_response(
                message={
                    "error": "matricola, nome, cognome and id_classe parameters are required"
                },
                status_code=STATUS_CODES["bad_request"],
            )
        if (
            not isinstance(matricola, str)
            or not isinstance(nome, str)
            or not isinstance(cognome, str)
        ):
            return create_response(
                message={"error": "matricola, nome and cognome must be strings"},
                status_code=STATUS_CODES["bad_request"],
            )
        try:
            id_classe = int(id_classe)
        except (ValueError, TypeError):
            return create_response(
                message={"error": "id_classe must be an integer"},
                status_code=STATUS_CODES["bad_request"],
            )

        try:
            # Insert the student
            lastrowid: int = execute_query(
                "INSERT INTO studenti VALUES (%s, %s, %s, %s)",
                (matricola, nome, cognome, id_classe),
            )
        except IntegrityError as ex:
            log(
                log_type="error",
                message=(
                    f"User {get_jwt_identity()} tried to create student {matricola} "
                    f"but it already generated {ex}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={"endpoint": Student.ENDPOINT_PATHS[0], "verb": "POST"},
            )
            return create_response(
                message={"error": "conflict error"},
                status_code=STATUS_CODES["conflict"],
            )
        except (ValueError, TypeError) as ex:
            log(
                log_type="error",
                message=(
                    f"User {get_jwt_identity()} failed to create student {matricola} "
                    f"with error: {str(ex)}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={"endpoint": Student.ENDPOINT_PATHS[0], "verb": "POST"},
            )
            return create_response(
                message={"error": "internal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

        # Log the student creation
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} created student {matricola}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Student.ENDPOINT_PATHS[0], "verb": "POST"},
        )

        return create_response(
            message={
                "outcome": "student successfully created",
                "location": get_hateos_location_string(bp_name=BP_NAME, id_=lastrowid),
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def delete(self, matricola) -> Response:
        """
        Delete a student.
        The request must include the student matricola as a path variable.
        """

        # Check that the specified student exists
        student: Dict[str, Any] = fetchone_query(
            "SELECT nome FROM studenti WHERE matricola = %s", (matricola,)
        )  # Only fetch the province to check existence (could be any field)
        if student is None:
            return create_response(
                message={"error": "specified student does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Delete the student
        execute_query("DELETE FROM studenti WHERE matricola = %s", (matricola,))

        # Log the deletion
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} deleted student {matricola}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Student.ENDPOINT_PATHS[1], "verb": "DELETE"},
        )

        # Return a success message
        return create_response(
            message={"outcome": "student successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def patch(self, matricola) -> Response:
        """
        Update a student.
        The request must include the student matricola as a path variable.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Check that the specified student exists
        student: Dict[str, Any] = fetchone_query(
            "SELECT nome FROM studenti WHERE matricola = %s",
            (
                matricola,
            ),  # Only fetch the province to check existence (could be any field)
        )
        if student is None:
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

        # Log the update
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} updated student {matricola}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Student.ENDPOINT_PATHS[1], "verb": "PATCH"},
        )

        # Return a success message
        return create_response(
            message={"outcome": "student successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, class_id) -> Response:
        """
        Get students list of a given class,
        including turn and address data if they are bound to a turn.
        """
        # Log the request
        log(
            log_type="info",
            message=(
                f"User {get_jwt_identity()} requested student list "
                f"for class {class_id}"
            ),
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Student.ENDPOINT_PATHS[1], "verb": "GET"},
        )

        # Check if the class exists
        class_: Dict[str, Any] = fetchone_query(
            "SELECT sigla FROM classi WHERE id_classe = %s",
            (class_id,),  # Only check for existence (select column could be any field)
        )
        if not class_:
            return create_response(
                message={"outcome": "no class found with the provided id_"},
                status_code=STATUS_CODES["not_found"],
            )

        # Get student data
        student_data: List[Dict[str, Any]] = fetchall_query(
            """
            SELECT S.matricola, S.nome, S.cognome, 
                  S.comune, T.id_turno, T.data_inizio, 
                  T.data_fine, T.giorno_inizio, T.giorno_fine, 
                  T.ora_inizio, T.ora_fine, T.ore,
                  A.ragione_sociale, A.indirizzo, A.cap, 
                  A.comune AS comuneAzienda, A.provincia, A.stato
            FROM studenti AS S
            LEFT JOIN studente_turno AS ST ON S.matricola = ST.matricola
            LEFT JOIN turni AS T ON ST.id_turno = T.id_turno
            LEFT JOIN aziende AS A ON T.id_azienda = A.id_azienda
            WHERE S.id_classe = %s
            """,
            (class_id,),
        )

        # Build the output JSON TODO check if the minimum necessary data is insterted in the JSON
        out_json = {}
        for row in student_data:
            matricola = row.get("matricola")
            out_json[matricola] = {
                "nome": row.get("nome"),
                "cognome": row.get("cognome"),
                "comune": row.get("comune"),
                "turno": (
                    {
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
                            "indirizzo": row.get("indirizzo"),
                        },
                    }
                    if row.get("id_turno")
                    else None
                ),
            }

        # Return the response
        return create_response(message=out_json, status_code=STATUS_CODES["ok"])

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS request for the Student resource.
        """

        return handle_options_request(resource_class=self)


class BindStudentToTurn(Resource):
    """
    Endpoint to bind a student to a turn.
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}/bind/<int:matricola>"]

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def post(self, matricola) -> Response:
        """
        Bind a student to a turn.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Gather parameters
        id_turno: Union[str, int] = data.get("id_turno")

        # Validate parameters
        if id_turno is None:
            return create_response(
                message={"error": "id_turno parameter is required"},
                status_code=STATUS_CODES["bad_request"],
            )
        try:
            id_turno = int(id_turno)
        except (ValueError, TypeError):
            return create_response(
                message={"error": "invalid id_turno parameter"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check that the student exists
        student: Dict[str, Any] = fetchone_query(
            "SELECT nome FROM studenti WHERE matricola = %s",
            (matricola,),  # Only check for existence (select column could be any field)
        )
        if student is None:
            return create_response(
                message={"error": "student not_found"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check that the turn exists
        turn: Dict[str, Any] = fetchone_query(
            "SELECT ore FROM turni WHERE id_turno = %s",
            (id_turno,),  # Only check for existence (select column could be any field)
        )
        if turn is None:
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
                    f"User {get_jwt_identity()} bound student {matricola} "
                    f"to turn {id_turno}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={
                    "endpoint": BindStudentToTurn.ENDPOINT_PATHS[0],
                    "verb": "POST",
                },
            )
            return create_response(
                message={"outcome": "student successfully bound to turn"},
                status_code=STATUS_CODES["created"],
            )
        except IntegrityError as ex:
            log(
                log_type="error",
                message=(
                    f"User {get_jwt_identity()} tried to bind student {matricola} "
                    f"to turn {id_turno} but it already generated {ex}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={
                    "endpoint": BindStudentToTurn.ENDPOINT_PATHS[0],
                    "verb": "POST",
                },
            )
            return create_response(
                message={"error": "conflict error"},
                status_code=STATUS_CODES["conflict"],
            )
        except (ValueError, TypeError) as ex:
            log(
                log_type="error",
                message=(
                    f"User {get_jwt_identity()} failed to bind student {matricola} "
                    f"to turn {id_turno} with error: {str(ex)}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={
                    "endpoint": BindStudentToTurn.ENDPOINT_PATHS[0],
                    "verb": "POST",
                },
            )
            return create_response(
                message={"error": "internal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS request for the BindStudentToTurn resource.
        """
        return handle_options_request(resource_class=self)


class StudentList(Resource):
    """
    Endpoint to get a list of all students associated with a specific turn.
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}/list/<int:turn_id>"]

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, turn_id) -> Response:
        """
        Get a list of all students that are associated
        to a turn passed by its id_ as a path variable.
        """
        # Log the request
        log(
            log_type="info",
            message=(
                f"User {get_jwt_identity()} requested student list "
                f"that are associated to turn {turn_id}"
            ),
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": StudentList.ENDPOINT_PATHS[0], "verb": "GET"},
        )

        # Check if the turn exists
        turn: Dict[str, Any] = fetchone_query(
            "SELECT ore FROM turni WHERE id_turno = %s",
            (turn_id,),  # Only check for existence (select column could be any field)
        )
        if not turn:
            return create_response(
                message={"outcome": "no turn found with the provided id_"},
                status_code=STATUS_CODES["not_found"],
            )

        # Get all students
        students: List[Dict[str, Any]] = fetchall_query(
            query="SELECT S.matricola, S.nome, S.cognome, S.comune"
            "FROM studenti AS S "
            "JOIN studenteTurno AS ST ON S.matricola = ST.matricola "
            "JOIN turni AS T ON ST.id_turno = T.id_turno "
            "WHERE T.id_turno = %s",
            params=(turn_id,),
        )

        # Return the response
        return create_response(message=students, status_code=STATUS_CODES["ok"])

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS request for the StudentList resource.
        """
        return handle_options_request(resource_class=self)


api.add_resource(Student, *Student.ENDPOINT_PATHS)
api.add_resource(BindStudentToTurn, *BindStudentToTurn.ENDPOINT_PATHS)
api.add_resource(StudentList, *StudentList.ENDPOINT_PATHS)
