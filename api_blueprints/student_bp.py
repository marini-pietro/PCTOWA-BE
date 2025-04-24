from os.path import basename as os_path_basename
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from typing import List, Dict, Union, Any
from mysql.connector import IntegrityError
from .blueprints_utils import (check_authorization, fetchone_query, 
                               fetchall_query, execute_query, 
                               log, jwt_required_endpoint, 
                               create_response, build_update_query_from_filters, 
                               has_valid_json, is_input_safe,
                               get_class_http_verbs)
from config import (API_SERVER_HOST, API_SERVER_PORT, 
                    API_SERVER_NAME_IN_LOG, STATUS_CODES)

# Define constants
BP_NAME = os_path_basename(__file__).replace('_bp.py', '')

# Create the blueprint and API
student_bp = Blueprint(BP_NAME, __name__)
api = Api(student_bp)

class Student(Resource):

    ENDPOINT_PATHS = [f'/{BP_NAME}/<int:matricola>', f'/{BP_NAME}/<int:matricola>', f'/{BP_NAME}/<int:class_id>']

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def post(self) -> Response:
        """
        Create a new student.
        The request body must be a JSON object with application/json content type.
        """

        # Validate request
        data: Union[str, Dict[str, Any]] = has_valid_json(request)
        if isinstance(data, str): 
            return create_response(message={'error': data}, status_code=STATUS_CODES["bad_request"])

        # Check for sql injection
        if not is_input_safe(data):
            return create_response(message={'error': 'invalid input, suspected sql injection'}, status_code=STATUS_CODES["bad_request"])

        # Gather parameters
        matricola: str = data.get('matricola')
        nome: str = data.get('nome')
        cognome: str = data.get('cognome')
        idClasse: int = data.get('idClasse')

        # Validate parameters
        if matricola is None or nome is None or cognome is None or idClasse is None:
            return create_response(message={'error': 'matricola, nome, cognome and idClasse parameters are required'}, status_code=STATUS_CODES["bad_request"])
        if not isinstance(matricola, str) or not isinstance(nome, str) or not isinstance(cognome, str):
            return create_response(message={'error': 'matricola, nome and cognome must be strings'}, status_code=STATUS_CODES["bad_request"])
        try:
            idClasse = int(idClasse)
        except (ValueError, TypeError):
            return create_response(message={'error': 'idClasse must be an integer'}, status_code=STATUS_CODES["bad_request"])

        try:
            # Insert the student
            lastrowid: int = execute_query('INSERT INTO studenti VALUES (%s, %s, %s, %s)', (matricola, nome, cognome, idClasse))
        except IntegrityError as ex:
            log(type='error',
                message=f'User {get_jwt_identity().get("email")} tried to create student {matricola} but it already generated {ex}',
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)
            return create_response(message={'error': 'conflict error'}, status_code=STATUS_CODES["conflict"])
        except Exception as ex:
            log(type='error',
                message=f'User {get_jwt_identity().get("email")} failed to create student {matricola} with error: {str(ex)}',
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)
            return create_response(message={'error': "internal server error"}, status_code=STATUS_CODES["internal_error"])

        # Log the student creation
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} created student {matricola}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{Student.ENDPOINT_PATHS[0]} Verb POST]")

        return create_response(message={"outcome": "student successfully created",
                                        'location': f'http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/{BP_NAME}/{lastrowid}'}, status_code=STATUS_CODES["created"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def delete(self, matricola) -> Response:
        """
        Delete a student.
        The request must include the student matricola as a path variable.
        """

        # Check that the specified student exists
        student: Dict[str, Any] = fetchone_query('SELECT nome FROM studenti WHERE matricola = %s', (matricola,)) # Only fetch the province to check existence (could be any field)
        if student is None:
            return create_response(message={'error': 'specified student does not exist'}, status_code=STATUS_CODES["not_found"])

        # Delete the student
        execute_query('DELETE FROM studenti WHERE matricola = %s', (matricola,))

        # Log the deletion
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} deleted student {matricola}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{Student.ENDPOINT_PATHS[1]} Verb DELETE]")

        # Return a success message
        return create_response(message={'outcome': 'student successfully deleted'}, status_code=STATUS_CODES["no_content"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def patch(self, matricola) -> Response:
        """
        Update a student.
        The request must include the student matricola as a path variable.
        """

        # Validate request
        data: Union[str, Dict[str, Any]] = has_valid_json(request)
        if isinstance(data, str): 
            return create_response(message={'error': data}, status_code=STATUS_CODES["bad_request"])

        # Check for sql injection
        if not is_input_safe(data):
            return create_response(message={'error': 'invalid input, suspected sql injection'}, status_code=STATUS_CODES["bad_request"])

        # Check that the specified student exists
        student: Dict[str, Any] = fetchone_query('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
        if student is None:
            return create_response(message={'outcome': 'error, specified student does not exist'}, status_code=STATUS_CODES["not_found"])

        # Check that the specified fields actually exist in the database
        modifiable_columns: List[str] = ['nome', 'cognome', 'idClasse', 'comune']
        toModify: List[str]  = list(data.keys())
        error_columns: List[str] = [field for field in toModify if field not in modifiable_columns]
        if error_columns:
            return create_response(message={'outcome': f'error, field(s) {error_columns} do not exist or cannot be modified'}, status_code=STATUS_CODES["bad_request"])

        # Build the update query
        query, params = build_update_query_from_filters(data=data, table_name='studenti', 
                                                        id_column='matricola', id_value=matricola)

        # Update the student
        execute_query(query, params)

        # Log the update
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} updated student {matricola}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{Student.ENDPOINT_PATHS[1]} Verb PATCH]")

        # Return a success message
        return create_response(message={'outcome': 'student successfully updated'}, status_code=STATUS_CODES["ok"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self, class_id) -> Response:
        """
        Get students list of a given class, including turn and address data if they are bound to a turn.
        """
        # Log the request
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} requested student list for class {class_id}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{Student.ENDPOINT_PATHS[2]} Verb GET]")

        # Check if the class exists
        class_: Dict[str, Any] = fetchone_query("SELECT * FROM classi WHERE idClasse = %s", (class_id,))
        if not class_:
            return create_response(
                message={"outcome": "no class found with the provided id"},
                status_code=STATUS_CODES["not_found"]
            )

        # Get student data
        student_data: List[Dict[str, Any]] = fetchall_query(
            """
            SELECT S.matricola, S.nome, S.cognome, S.comune, T.idTurno, T.dataInizio, T.dataFine,
                   T.giornoInizio, T.giornoFine, T.oraInizio, T.oraFine, T.ore,
                   A.ragioneSociale, A.indirizzo, A.cap, A.comune AS comuneAzienda, A.provincia, A.stato
            FROM studenti AS S
            LEFT JOIN studenteTurno AS ST ON S.matricola = ST.matricola
            LEFT JOIN turni AS T ON ST.idTurno = T.idTurno
            LEFT JOIN aziende AS A ON T.idAzienda = A.idAzienda
            WHERE S.idClasse = %s
            """,
            (class_id,)
        )

        # Build the output JSON TODO check if the minimum necessary data is insterted in the JSON
        out_json = {}
        for row in student_data:
            matricola = row.get('matricola')
            out_json[matricola] = {
                'nome': row.get('nome'),
                'cognome': row.get('cognome'),
                'comune': row.get('comune'),
                'turno': {
                    'ragioneSociale': row.get('ragioneSociale'),
                    'dataInizio': row.get('dataInizio'),
                    'dataFine': row.get('dataFine'),
                    'giornoInizio': row.get('giornoInizio'),
                    'giornoFine': row.get('giornoFine'),
                    'oraInizio': row.get('oraInizio'),
                    'oraFine': row.get('oraFine'),
                    'ore': row.get('ore'),
                    'turnoPK': row.get('idTurno'),
                    'indirizzo': {
                        'stato': row.get('stato'),
                        'provincia': row.get('provincia'),
                        'comune': row.get('comuneAzienda'),
                        'cap': row.get('cap'),
                        'indirizzo': row.get('indirizzo')
                    },
                } if row.get('idTurno') else None
            }

        # Return the response
        return create_response(message=out_json, status_code=STATUS_CODES["ok"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def options(self) -> Response:
        # Define allowed methods
        allowed_methods = get_class_http_verbs(type(self))
        
        # Create the response
        response = Response(status=STATUS_CODES["ok"])
        response.headers['Allow'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Origin'] = '*'  # Adjust as needed for CORS
        response.headers['Access-Control-Allow-Methods'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response

class BindStudentToTurn(Resource):

    ENDPOINT_PATHS = [f'/{BP_NAME}/bind/<int:matricola>']

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def post(self, matricola) -> Response:
        """
        Bind a student to a turn.
        """

        # Validate request
        data: Union[str, Dict[str, Any]] = has_valid_json(request)
        if isinstance(data, str): 
            return create_response(message={'error': data}, status_code=STATUS_CODES["bad_request"])
        
        # Check for sql injection
        if not is_input_safe(data):
            return create_response(message={'error': 'invalid input, suspected sql injection'}, status_code=STATUS_CODES["bad_request"])

        # Gather parameters
        idTurno: Union[str, int] = data.get('idTurno')

        # Validate parameters
        if idTurno is None:
            return create_response(message={'error': 'idTurno parameter is required'}, status_code=STATUS_CODES["bad_request"])
        try:
            idTurno = int(idTurno)
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idTurno parameter'}, status_code=STATUS_CODES["bad_request"])
        
        # Check that the student exists
        student: Dict[str, Any] = fetchone_query('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
        if student is None:
            return create_response(message={'error': 'student not_found'}, status_code=STATUS_CODES["not_found"])
        
        # Check that the turn exists
        turn: Dict[str, Any] = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
        if turn is None:
            return create_response(message={'error': 'turn not_found'}, status_code=STATUS_CODES["not_found"])
        
        # Bind the student to the turn
        try:
            execute_query('INSERT INTO studenteTurno (matricola, idTurno) VALUES (%s, %s)', (matricola, idTurno))

            # Log the binding
            log(type='info',
                message=f'User {get_jwt_identity().get("email")} bound student {matricola} to turn {idTurno}',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                origin_port=API_SERVER_PORT,
                structured_data=f"[{BindStudentToTurn.ENDPOINT_PATHS[0]} Verb POST]")
            return create_response(message={'outcome': 'student successfully bound to turn'}, status_code=STATUS_CODES["created"])
        except IntegrityError as ex:
            log(type='error',
                message=f'User {get_jwt_identity().get("email")} tried to bind student {matricola} to turn {idTurno} but it already generated {ex}',
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT,
                structured_data=f"[{BindStudentToTurn.ENDPOINT_PATHS[0]} Verb POST]")
            return create_response(message={'error': 'conflict error'}, status_code=STATUS_CODES["conflict"])
        except Exception as ex:
            log(type='error',
                message=f'User {get_jwt_identity().get("email")} failed to bind student {matricola} to turn {idTurno} with error: {str(ex)}',
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT,
                structured_data=f"[{BindStudentToTurn.ENDPOINT_PATHS[0]} Verb POST]")
            return create_response(message={'error': "internal server error"}, status_code=STATUS_CODES["internal_error"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def options(self) -> Response:
        # Define allowed methods
        allowed_methods = get_class_http_verbs(type(self))
        
        # Create the response
        response = Response(status=STATUS_CODES["ok"])
        response.headers['Allow'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Origin'] = '*'  # Adjust as needed for CORS
        response.headers['Access-Control-Allow-Methods'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response

class StudentList(Resource):

    ENDPOINT_PATHS = [f'/{BP_NAME}/list/<int:turn_id>']

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self, turn_id) -> Response:
        """
        Get a list of all students that are associated to a turn passed by its id as a path variable.
        """
        # Log the request
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} requested student list that are associated to turn {turn_id}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{StudentList.ENDPOINT_PATHS[0]} Verb GET]")
        
        # Check if the turn exists
        turn: Dict[str, Any] = fetchone_query("SELECT * FROM turni WHERE idTurno = %s", (turn_id,))
        if not turn:
            return create_response(
                message={"outcome": "no turn found with the provided id"},
                status_code=STATUS_CODES["not_found"]
            )

        # Get all students
        students: List[Dict[str, Any]] = fetchall_query("SELECT S.matricola, S.nome, S.cognome, S.comune"
                                                        "FROM studenti AS S "
                                                        "JOIN studenteTurno AS ST ON S.matricola = ST.matricola JOIN turni AS T ON ST.idTurno = T.idTurno "
                                                        "WHERE T.idTurno = %s", 
                                                        (turn_id,)
                                                        )

        # Return the response
        return create_response(message=students, status_code=STATUS_CODES["ok"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def options(self) -> Response:
        # Define allowed methods
        allowed_methods = get_class_http_verbs(type(self))
        
        # Create the response
        response = Response(status=STATUS_CODES["ok"])
        response.headers['Allow'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Origin'] = '*'  # Adjust as needed for CORS
        response.headers['Access-Control-Allow-Methods'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response

api.add_resource(Student, *Student.ENDPOINT_PATHS)
api.add_resource(BindStudentToTurn, *BindStudentToTurn.ENDPOINT_PATHS)
api.add_resource(StudentList, *StudentList.ENDPOINT_PATHS)