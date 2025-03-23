from flask import Flask, jsonify, request # From Flask import the Flask object, jsonify function and request object
from requests import post as requests_post # From requests import the post function
import mysql.connector, signal
from utils import jwt_required_endpoint, fetchone_query, execute_query, log, close_log_socket, parse_date_string, parse_time_string, AUTH_SERVER_HOST

# Create a Flask app
app = Flask(__name__)

# Define host and port for the API server
API_SERVER_HOST = '172.16.1.98' # The host of the API server
API_SERVER_PORT = 5000 # The port of the API server

# Utility functions
def close_api(signal, frame):  # Parameters are necessary even if not used because it has to match the signal signature
    """
    Gracefully close the API server.
    """
    log('info', 'API server shutting down')
    close_log_socket()  # Close the socket connection to the log server
    exit(0)  # Close the API

signal.signal(signal.SIGINT, close_api)  # Bind CTRL+C to close_api function
signal.signal(signal.SIGTERM, close_api)  # Bind SIGTERM to close_api function

# Functions used for testing purposes, should be removed in production
@app.route('/api/endpoints', methods=['GET']) # Only used for testing purposes should be removed in production
def list_endpoints():
    endpoints = []
    for rule in app.url_map.iter_rules():
        endpoints.append({
            "endpoint": rule.endpoint,
            "methods": list(rule.methods),
            "url": rule.rule
        })
    return {"endpoints": endpoints}

@app.route('/api/shutdown', methods=['GET']) # Only used for testing purposes should be removed in production (used to remotely close the server while testing)
def shutdown_endpoint():
    close_api()

# API endpoints

@app.route('/api/user_login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')

    # Forward login request to the authentication service
    response = requests_post(f'{AUTH_SERVER_HOST}/auth/login', json={'email': email, 'password': password})
    if response.status_code == 200:
        return jsonify(response.json()), 200
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/user_register', methods=['POST'])
def register():
    """
    Register a new user.
    """
    # Gather parameters
    email = request.json.get('email')
    password = request.json.get('password')
    name = request.json.get('nome')
    surname = request.json.get('cognome')
    user_type = request.json.get('tipo')
    
    # Insert the user
    try:
        execute_query('INSERT INTO utenti (emailUtente, password, nome, cognome, tipo) VALUES (%s, %s, %s, %s, %s)',
                      (email, password, name, surname, int(user_type)))
        log('info', f'User {email} registered')
        return jsonify({"outcome": "user successfully created"}), 201
    except mysql.connector.IntegrityError:
        return jsonify({'outcome': 'error, user with provided credentials already exists'}), 400

@app.route('/api/user_update', methods=['PATCH'])
@jwt_required_endpoint()
def user_update():
    
    # Gather parameters
    email = request.args.get('email')
    toModify = request.args.get('toModify')
    newValue = request.args.get('newValue')

    # Check if the field to modify is allowed
    if toModify in ['email']:
        return jsonify({'outcome': 'error, specified field cannot be modified'})
    
    # Check if user exists
    user = fetchone_query('SELECT * FROM utente WHERE emailUtente = %s', (email,))
    if user is None:
        return jsonify({'outcome': 'error, user with provided email does not exist'})
    
    # Update the user
    execute_query(f'UPDATE utente SET {toModify} = %s WHERE emailUtente = %s', (newValue, email))

    # Log the update
    log('info', f'User {request.user_identity} updated')

    return jsonify({'outcome': 'user successfully updated'})

@app.route('/api/user_delete', methods=['DELETE'])
@jwt_required_endpoint()
def user_delete():
    
    # Gather parameters
    email = request.args.get('email')

    # Check if user exists
    user = fetchone_query('SELECT * FROM utente WHERE emailUtente = %s', (email,))
    if user is None:
        return jsonify({'outcome': 'error, user with provided email does not exist'})
    
    # Delete the user
    execute_query('DELETE FROM utente WHERE emailUtente = %s', (email,))

    # Log the deletion
    log('info', f'User {request.user_identity} deleted')

    return jsonify({'outcome': 'user successfully deleted'})

@app.route('/api/class_register', methods=['POST'])
@jwt_required_endpoint()
def class_register():
    # Gather parameters
    classe = request.args.get('classe')
    anno = request.args.get('anno')
    emailResponsabile = request.args.get('emailResponsabile')     
    
    try:
        execute_query('INSERT INTO classi VALUES (%s, %s, %s)', (classe, anno, emailResponsabile))

        # Log the class creation
        log('info', f'User {request.user_identity} created class {classe}')

        return jsonify({"outcome": "class successfully created"})
    except mysql.connector.IntegrityError as ex:
        return jsonify({'outcome': 'error, class with provided credentials already exists'})

@app.route('/api/class_delete', methods=['DELETE'])
@jwt_required_endpoint()
def class_delete():
    # Gather parameters
    idClasse = request.args.get('idClasse')

    # Check if class exists
    classe = fetchone_query('SELECT * FROM classi WHERE idClasse = %s', (idClasse,))
    if classe is None:
        return jsonify({'outcome': 'error, specified class does not exist'})
    
    # Delete the class
    execute_query('DELETE FROM classi WHERE idClasse = %s', (idClasse,))

    # Log the deletion
    log('info', f'User {request.user_identity} deleted class')

    return jsonify({'outcome': 'class successfully deleted'})

@app.route('/api/class_update', methods=['PATCH'])
@jwt_required_endpoint()
def class_update():
    # Gather parameters
    idClasse = request.args.get('idClasse')
    toModify = request.args.get('toModify')
    newValue = request.args.get('newValue')

    # Check if the field to modify is allowed
    if toModify in ['idClasse']:
        return jsonify({'outcome': 'error, specified field cannot be modified'})

    # Check if class exists
    classe = fetchone_query('SELECT * FROM classi WHERE idClasse = %s', (idClasse,))
    if classe is None:
        return jsonify({'outcome': 'error, specified class does not exist'})
    
    # Update the class
    execute_query(f'UPDATE classi SET {toModify} = %s WHERE idClasse = %s', (newValue, idClasse))
    
    # Log the update
    log('info', f'User {request.user_identity} updated class')

    return jsonify({'outcome': 'class successfully updated'})

@app.route('/api/class_read', methods = ['GET'])
@jwt_required_endpoint()
def class_read():
    # Gather parameters
    try:
        idClasse = int(request.args.get('idClasse'))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid idClasse parameter"}), 400

    # Execute query
    try:
        execute_query('SELECT * FROM classi WHERE idClasse = %s', (idClasse,))

        # Execute query
        class_ = fetchone_query('SELECT * FROM classi WHERE idClasse = %s', (idClasse,))

        # Log the read
        log('info', f'User {request.user_identity} read class')

        return jsonify(class_), 200
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

@app.route('/api/student_register', methods=['POST'])
@jwt_required_endpoint()
def student_register():
    # Gather parameters
    matricola = request.args.get('matricola')
    nome = request.args.get('nome')
    cognome = request.args.get('cognome')
    idClasse = request.args.get('idClasse')
    
    try:
        execute_query('INSERT INTO studenti VALUES (%s, %s, %s, %s)', (matricola, nome, cognome, idClasse))

        # Log the student creation
        log('info', f'User {request.user_identity} created student {matricola}')

        return jsonify({"outcome": "student successfully created"})
    except mysql.connector.IntegrityError as ex:
        return jsonify({'outcome': 'student with provided matricola already exists'})

@app.route('/api/student_delete', methods=['DELETE'])
@jwt_required_endpoint()
def student_delete():
    # Gather parameters
    matricola = request.args.get('matricola')

    # Check if student exists
    student = fetchone_query('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
    if student is None:
        return jsonify({'outcome': 'error, specified student does not exist'})
    
    # Delete the student
    execute_query('DELETE FROM studenti WHERE matricola = %s', (matricola,))

    # Log the deletion
    log('info', f'User {request.user_identity} deleted student {matricola}')

    return jsonify({'outcome': 'student successfully deleted'})

@app.route('/api/student_update', methods=['PATCH'])
@jwt_required_endpoint()
def student_update():
    # Gather parameters
    matricola = request.args.get('matricola')
    toModify = request.args.get('toModify')
    newValue = request.args.get('newValue')

    # Check if the field to modify is allowed
    if toModify in ['matricola']:
        return jsonify({'outcome': 'error, specified field cannot be modified'})

    # Check if student exists
    student = fetchone_query('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
    if student is None:
        return jsonify({'outcome': 'error, specified student does not exist'})
    
    # Update the student
    execute_query(f'UPDATE studenti SET {toModify} = %s WHERE matricola = %s', (newValue, matricola))
    
    # Log the update
    log('info', f'User {request.user_identity} updated student {matricola}')

    return jsonify({'outcome': 'student successfully updated'})

@app.route('/api/student_read', methods = ['GET'])
@jwt_required_endpoint()
def student_read():
    # Gather parameters
    try:
        matricola = int(request.args.get('matricola'))
    except (ValueError, TypeError):
        return jsonify({'error': 'invalid matricola parameter'}), 400

    # Execute query
    try:
        student = fetchone_query('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
    
        # Log the read
        log('info', f'User {request.user_identity} read student {matricola}')

        return jsonify(student), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/api/turn_register', methods=['POST'])
@jwt_required_endpoint()
def turn_register():

    # Gather parameters
    settore = request.args.get('settore')
    posti = request.args.get('posti')
    ore = request.args.get('ore')
    idAzienda = int(request.args.get('idAzienda'))
    idIndirizzo = request.args.get('idIndirizzo')
    idTutor = request.args.get('idTutor')
    dataInizio = parse_date_string(date_string=request.args.get('dataInizio')) # Parse function will return None if string is incorrectly formatted or value is None to begin with
    dataFine = parse_date_string(date_string=request.args.get('dataFine')) # Parse function will return None if string is incorrectly formatted or value is None to begin with
    oraInizio =  parse_time_string(time_string=request.args.get('oraInizio')) # Parse function will return None if string is incorrectly formatted or value is None to begin with
    oraFine = parse_time_string(time_string=request.args.get('oraFine')) # Parse function will return None if string is incorrectly formatted or value is None to begin with

    # Check if idAzienda exists
    company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
    if company is None:
        return jsonify({'outcome': 'error, specified company does not exist'})

    # Check that idIndirizzo exist if an idIndirizzo is provided
    if idIndirizzo is not None: 
        address = fetchone_query('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (int(idIndirizzo)))
        if address is None:
            return jsonify({'outcome': 'error, specified address does not exist'})
        
    # Check that settore if one is provided
    if settore is not None: 
        sector = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore))
        if sector is None:
            return jsonify({'outcome': 'error, specified sector does not exist'})
    
    # Check that idTutor exists if one is provided
    if idTutor is not None:
        tutor = fetchone_query('SELECT * FROM tutor WHERE idTutor = %s', (int(idTutor)))
        if tutor is None:
            return jsonify({'outcome': 'error, specified tutor does not exist'})
    
    # Insert the turn
    execute_query('INSERT INTO turni (dataInizio, dataFine, settore, posti, ore, idAzienda, idIndirizzo, idTutor, oraInizio, oraFine) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', 
                   (dataInizio, dataFine, settore, posti, ore, idAzienda, idIndirizzo, idTutor, oraInizio, oraFine))
    
    # Log the turn creation
    log('info', f'User {request.user_identity} created a turn')

    return jsonify({'outcome': 'turn successfully created'}), 201

@app.route('/api/turn_delete', methods=['DELETE'])
@jwt_required_endpoint()
def turn_delete():
    
    # Gather parameters
    idTurno = int(request.args.get('idTurno'))

    # Check if turn exists
    turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
    if turn is None:
        return jsonify({'outcome': 'error, specified turn does not exist'})
    
    # Delete the turn
    execute_query('DELETE FROM turni WHERE idTurno = %s', (idTurno,))
    
    # Log the deletion
    log('info', f'User {request.user_identity} deleted turn')

    return jsonify({'outcome': 'turn successfully deleted'})

@app.route('/api/turn_update', methods=['PATCH'])
@jwt_required_endpoint()
def turn_update():

    # Gather parameters
    idTurno = int(request.args.get('idTurno'))
    toModify = request.args.get('toModify')
    newValue = request.args.get('newValue')

    # Check if the field to modify is allowed
    if toModify in ['idTurno']:
        return jsonify({'outcome': 'error, specified field cannot be modified'})
    
    # Check if any casting operations are needed
    if toModify in ['posti', 'ore']:
        newValue = int(newValue)
    elif toModify in ['dataInizio', 'dataFine']:
        newValue = parse_date_string(date_string=newValue)
    elif toModify in ['oraInizio', 'oraFine']:
        newValue = parse_time_string(time_string=newValue)

    # Check if turn exists
    turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno))
    if turn is None:
        return jsonify({'outcome': 'error, specified turn does not exist'})
    
    # Update the turn
    execute_query(f'UPDATE turni SET {toModify} = %s WHERE idTurno = %s', (newValue, idTurno))
    
    # Log the update
    log('info', f'User {request.user_identity} updated turn')

    return jsonify({'outcome': 'turn successfully updated'})

@app.route('/api/turn_read', methods=['GET'])
@jwt_required_endpoint()
def turn_read():
    # Gather parameters
    try:
        idTurno = int(request.args.get('idTurno'))
    except (ValueError, TypeError):
        return jsonify({'error': 'invalid idTurno parameter'}), 400

    # Execute query
    try:
        turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))

        # Log the read
        log('info', f'User {request.user_identity} read turn')

        return jsonify(turn), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/api/address_register', methods=['POST'])
@jwt_required_endpoint()
def address_register():

    #Gather GET parameters
    stato = request.args.get('stato')
    provincia = request.args.get('provincia')
    comune = request.args.get('comune')
    cap = request.args.get('cap')
    indirizzo = request.args.get('indirizzo')
    idAzienda = int(request.args.get('idAzienda'))

    # Check if idAzienda exists
    company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
    if company is None:
        return jsonify({'outcome': 'error, specified company does not exist'})
    
    # Insert the address
    execute_query('INSERT INTO indirizzi (stato, provincia, comune, cap, indirizzo, idAzienda) VALUES (%s, %s, %s, %s, %s, %s)',
                   (stato, provincia, comune, cap, indirizzo, idAzienda))
    
    # Log the address creation
    log('info', f'User {request.user_identity} created address')

    return jsonify({'outcome': 'address successfully created'})

@app.route('/api/address_delete', methods=['DELETE'])
@jwt_required_endpoint()
def address_delete():
    
    # Gather parameters
    idIndirizzo = int(request.args.get('idIndirizzo'))

    # Check if address exists
    address = fetchone_query('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))
    if address is None:
        return jsonify({'outcome': 'error, specified address does not exist'})
    
    # Delete the address
    execute_query('DELETE FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))
    
    # Log the deletion
    log('info', f'User {request.user_identity} deleted address')

    return jsonify({'outcome': 'address successfully deleted'})

@app.route('/api/address_update', methods=['PATCH'])
@jwt_required_endpoint()
def address_update():

    # Gather parameters
    idIndirizzo = int(request.args.get('idIndirizzo'))
    toModify = request.args.get('toModify')
    newValue = request.args.get('newValue')

    # Check if the field to modify is allowed
    if toModify in ['idIndirizzo']:
        return jsonify({'outcome': 'error, specified field cannot be modified'})

    # Check if address exists
    address = fetchone_query('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo))
    if address is None:
        return jsonify({'outcome': 'error, specified address does not exist'})
    
    # Update the address
    execute_query(f'UPDATE indirizzi SET {toModify} = %s WHERE idIndirizzo = %s', (newValue, idIndirizzo))
    
    # Log the update
    log('info', f'User {request.user_identity} updated address')

    return jsonify({'outcome': 'address successfully updated'})

@app.route('/api/address_read', methods = ['GET'])
@jwt_required_endpoint()
def address_read():
    #Gather parameters
    try:
        idIndirizzo = int(request.args.get('idIndirizzo'))
    except (ValueError, TypeError):
        return jsonify({'error': 'invalid idIndirizzo parameter'}), 400

    # Execute query
    try:
        address = fetchone_query('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))
        
        # Log the read
        
        log('info', f'User {request.user_identity} read address')

        return jsonify(address), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/api/contact_register', methods=['POST'])
@jwt_required_endpoint()
def contact_register():

    # Gather parameters
    nome = request.args.get('nome')
    cognome = request.args.get('cognome')
    telefono = request.args.get('telefono')
    email = request.args.get('email')
    ruolo = request.args.get('ruolo')
    idAzienda = int(request.args.get('idAzienda'))

    # Check if idAzienda exists
    company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
    if company is None:
        return jsonify({'outcome': 'error, specified company does not exist'})
    
    # Insert the contact
    contact = execute_query('INSERT INTO contatti (nome, cognome, telefono, email, ruolo, idAzienda) VALUES (%s, %s, %s, %s, %s, %s)',
                     (nome, cognome, telefono, email, ruolo, idAzienda))
    
    # Log the contact creation
    
    log('info', f'User {request.user_identity} created contact')

    return jsonify({'outcome': 'success, company inserted'})

@app.route('/api/contact_delete', methods=['DELETE'])
@jwt_required_endpoint()
def contact_delete():

    # Gather parameters
    idContatto = int(request.args.get('idContatto'))

    # Check if contact exists
    contact = fetchone_query('SELECT * FROM contatti WHERE idContatto = %s', (idContatto,))
    if contact is None:
        return jsonify({'outcome': 'error, specified contact does not exist'})
    
    # Delete the contact
    execute_query('DELETE FROM contatti WHERE idContatto = %s', (idContatto,))

    # Log the deletion
    log('info', f'User {request.user_identity} deleted contact')

    return jsonify({'outcome': 'contact successfully deleted'})

@app.route('/api/contact_update', methods=['PATCH'])
@jwt_required_endpoint()
def contact_update():

    # Gather parameters
    idContatto = int(request.args.get('idContatto'))
    toModify = request.args.get('toModify')
    newValue = request.args.get('newValue')

    # Check if the field to modify is allowed
    if toModify in ['idContatto']:
        return jsonify({'outcome': 'error, specified field cannot be modified'})
    
    # Check if any casting operations are needed
    if toModify in ['telefono']:
        newValue = int(newValue)

    # Check if contact exists
    contact = fetchone_query('SELECT * FROM contatti WHERE idContatto = %s', (idContatto))
    if contact is None:
        return jsonify({'outcome': 'error, specified contact does not exist'})
    
    # Update the contact
    execute_query(f'UPDATE contatti SET {toModify} = %s WHERE idContatto = %s', (newValue, idContatto))

    # Log the update
    log('info', f'User {request.user_identity} updated contact')

    return jsonify({'outcome': 'contact successfully updated'})

@app.route('/api/contact_read', methods = ['GET'])
@jwt_required_endpoint()
def contact_read():
    # Gather parameters
    try:
        idContatto = int(request.args.get('idContatto'))
    except (ValueError, TypeError):
        return jsonify({'error': 'invalid idContatto parameter'}), 400

    # Execute query
    try:
        contact = execute_query('SELECT * FROM contatti WHERE idContatto = %s', (idContatto,))
        
        # Log the read
        log('info', f'User {request.user_identity} read contact')

        return jsonify(contact), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/api/tutor_register', methods=['POST'])
@jwt_required_endpoint()
def tutor_register():

    # Gather parameters
    nome = request.args.get('nome')
    cognome = request.args.get('cognome')
    telefono = request.args.get('telefono')
    email = request.args.get('email')

    # Check if tutor already exists by checking if the combination of email and phone number already exists
    tutor = fetchone_query('SELECT * FROM tutor WHERE emailTutor = %s AND telefonoTutor = %s', (email, telefono))
    if tutor is None:
        return jsonify({'outcome': 'error, specified company does not exist'})
    
    # Insert the tutor
    execute_query('INSERT INTO tutor (nome, cognome, telefonoTutor, emailTutor) VALUES (%s, %s, %s, %s)',
                     (nome, cognome, telefono, email))
    
    # Log the tutor creation
    
    log('info', f'User {request.user_identity} created a tutor')

    return jsonify({'outcome': 'tutor successfully created'})

@app.route('/api/tutor_delete', methods=['DELETE'])
@jwt_required_endpoint()
def tutor_delete():
    # Gather parameters
    idTutor = int(request.args.get('idTutor'))

    # Check if tutor exists
    tutor = fetchone_query('SELECT * FROM tutor WHERE idTutor = %s', (idTutor,))
    if tutor is None:
        return jsonify({'outcome': 'error, specified tutor does not exist'})
    
    # Delete the tutor
    execute_query('DELETE FROM tutor WHERE idTutor = %s', (idTutor,))
    
    # Log the deletion
    log('info', f'User {request.user_identity} deleted tutor')

    return jsonify({'outcome': 'tutor successfully deleted'})

@app.route('/api/tutor_update', methods=['PATCH'])
@jwt_required_endpoint()
def tutor_update():
    
    # Gather parameters
    idTutor = int(request.args.get('idTutor'))
    toModify = request.args.get('toModify')
    newValue = request.args.get('newValue')

    # Check if the field to modify is allowed
    if toModify in ['idTutor']:
        return jsonify({'outcome': 'error, specified field cannot be modified'})

    # Check if tutor exists
    tutor = fetchone_query('SELECT * FROM tutor WHERE idTutor = %s', (idTutor,))
    if tutor is None:
        return jsonify({'outcome': 'error, specified tutor does not exist'})
    
    # Update the tutor
    execute_query(f'UPDATE tutor SET {toModify} = %s WHERE idTutor = %s', (newValue, idTutor))
    
    # Log the update
    log('info', f'User {request.user_identity} updated tutor with id {idTutor}')

    return jsonify({'outcome': 'tutor successfully updated'})

@app.route('/api/tutor_read', methods = ['GET'])
@jwt_required_endpoint()
def tutor_read():
    # Gather parameters
    try:
        idTutor = int(request.args.get('idTutor'))
    except (ValueError, TypeError):
        return jsonify({'error': 'invalid idTutor parameter'}), 400

    # Execute query
    try:
        tutor = fetchone_query('SELECT * FROM tutor WHERE idTutor = %s', (idTutor,))
        
        # Log the read
        log('info', f'User {request.user_identity} read tutor with id {idTutor}')

        return jsonify(tutor), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/api/company_register', methods=['POST'])
@jwt_required_endpoint()
def company_register():

    # Gather parameters
    ragioneSociale = request.args.get('ragioneSociale')
    nome = request.args.get('nome')
    sitoWeb = request.args.get('sitoWeb')
    indirizzoLogo = request.args.get('indirizzoLogo')
    codiceAteco = request.args.get('codiceAteco')
    partitaIVA = request.args.get('partitaIVA')
    telefonoAzienda = request.args.get('telefonoAzienda')
    fax = request.args.get('fax')
    emailAzienda = request.args.get('emailAzienda')
    pec = request.args.get('pec')
    formaGiuridica = request.args.get('formaGiuridica')
    dataConvenzione = request.args.get('dataConvenzione')
    scadenzaConvenzione = request.args.get('scadenzaConvenzione')
    settore = request.args.get('settore')
    categoria = request.args.get('categoria')
    
    # Insert the company
    try:
        execute_query('INSERT INTO aziende (ragioneSociale, nome, sitoWeb, indirizzoLogo, codiceAteco, partitaIVA, telefonoAzienda, fax, emailAzienda, pec, formaGiuridica, dataConvenzione, scadenzaConvenzione, settore, categoria) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', 
                    (ragioneSociale, nome, sitoWeb, indirizzoLogo, codiceAteco, partitaIVA, telefonoAzienda, fax, emailAzienda, pec, formaGiuridica, dataConvenzione, scadenzaConvenzione, settore, categoria))
        
        # Log the company creation
        log('info', f'User {request.user_identity} created a company')

        return jsonify({'outcome': 'company successfully created'})
    except mysql.connector.IntegrityError as ex:
        return jsonify({'outcome': 'error, company already exists, integrity error: {ex}'})

@app.route('/api/company_delete', methods=['DELETE'])
@jwt_required_endpoint()
def company_delete():
    # Gather parameters
    idAzienda = int(request.args.get('idAzienda'))

    # Check if company exists
    company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
    if company is None:
        return jsonify({'outcome': 'error, specified company does not exist'})

    # Delete the company (cascade delete will handle related rows)
    execute_query('DELETE FROM indirizzi WHERE idAzienda = %s', (idAzienda))
    
    # Log the deletion
    log('info', f'User {request.user_identity} deleted company with id {idAzienda}')

    return jsonify({'outcome': 'company successfully deleted'})

@app.route('/api/company_update', methods=['PATCH'])
@jwt_required_endpoint()
def company_update():
    # Gather parameters
    idAzienda = int(request.args.get('idAzienda'))
    toModify = request.args.get('toModify')
    newValue = request.args.get('newValue')

    # Check if the field to modify is allowed
    if toModify in ['idAzienda']:
        return jsonify({'outcome': 'error, specified field cannot be modified'})
    
    # Check if any casting operations are needed
    if toModify in ['telefonoAzienda', 'fax']:
        newValue = int(newValue)
    elif toModify in ['dataConvenzione', 'scadenzaConvenzione']:
        newValue = parse_date_string(date_string=newValue)

    # Check if company exists
    company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda))
    if company is None:
        return jsonify({'outcome': 'error, specified company does not exist'})
    
    # Update the company
    execute_query(f'UPDATE aziende SET {toModify} = %s WHERE idAzienda = %s', (newValue, idAzienda))
    
    # Log the update
    log('info', f'User {request.user_identity} updated company with id {idAzienda}')

    return jsonify({'outcome': 'company successfully updated'})

@app.route('/api/company_read', methods = ['GET'])
@jwt_required_endpoint()
def company_read():
    # Gather parameters
    try:
        idAzienda = int(request.args.get('idAzienda'))
    except (ValueError, TypeError):
        return jsonify({'error': 'invalid idAzienda parameter'}), 400

    # Execute query
    try:
        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
        
        # Log the read
        log('info', f'User {request.user_identity} read company with id {idAzienda}')

        return jsonify(company), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/api/sector_register', methods=['POST'])
@jwt_required_endpoint()
def sector_register():
    
    # Gather parameters
    settore = request.args.get('settore')

    # Check if sector exists
    sector = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore,))
    if sector is None:
        return jsonify({'outcome': 'error, specified sector already exists'})
    
    # Insert the sector
    execute_query('INSERT INTO settori (settore) VALUES (%s)', (settore,))
    
    # Log the sector creation
    log('info', f'User {request.user_identity} created sector {settore}')

    return jsonify({'outcome': 'sector successfully created'})

@app.route('/api/sector_delete', methods=['DELETE'])
@jwt_required_endpoint()
def sector_delete():
    
    # Gather parameters
    settore = request.args.get('settore')

    # Check if sector exists
    sector = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore,))
    if sector is None:
        return jsonify({'outcome': 'error, specified sector does not exist'})
    
    # Delete the sector
    execute_query('DELETE FROM settori WHERE settore = %s', (settore,))
    
    # Log the deletion
    log('info', f'User {request.user_identity} deleted sector {settore}')

    return jsonify({'outcome': 'sector successfully deleted'})

@app.route('/api/sector_update', methods=['PATCH'])
@jwt_required_endpoint()
def sector_update():

    # Gather parameters
    settore = request.args.get('settore')
    newValue = request.args.get('newValue')

    # Check if sector exists
    sector = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore,))
    if sector is None:
        return jsonify({'outcome': 'error, specified sector does not exist'})
    
    # Update the sector
    execute_query('UPDATE settori SET settore = %s WHERE settore = %s', (newValue, settore))
    
    # Log the update
    log('info', f'User {request.user_identity} updated sector {settore}')

    return jsonify({'outcome': 'sector successfully updated'})

@app.route('/api/subject_register', methods=['POST'])
@jwt_required_endpoint()
def subject_register():
    
    # Gather parameters
    materia = request.args.get('materia')
    descrizione = request.args.get('descrizione')

    # Check if subject exists
    subject = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
    if subject is None:
        return jsonify({'outcome': 'error, specified subject already exists'})
    
    # Insert the subject
    execute_query('INSERT INTO materie (materia, descr) VALUES (%s, %s)', (materia, descrizione))

    # Log the subject creation
    log('info', f'User {request.user_identity} created subject {materia}')

    return jsonify({'outcome': 'subject successfully created'})

@app.route('/api/subject_delete', methods=['DELETE'])
@jwt_required_endpoint()
def subject_delete():

    # Gather parameters
    materia = request.args.get('materia')

    # Check if subject exists
    subject = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
    if subject is None:
        return jsonify({'outcome': 'error, specified subject does not exist'})
    
    # Delete the subject
    execute_query('DELETE FROM materie WHERE materia = %s', (materia,))

    # Log the deletion
    log('info', f'User {request.user_identity} deleted subject {materia}')

    return jsonify({'outcome': 'subject successfully deleted'})

@app.route('/api/subject_update', methods=['PATCH'])
@jwt_required_endpoint()
def subject_update():
    
    # Gather parameters
    materia = request.args.get('materia')
    toModify = request.args.get('toModify')
    newValue = request.args.get('newValue')

    # Check if the field to modify is allowed
    if toModify in ['materia']:
        return jsonify({'outcome': 'error, specified field cannot be modified'})

    # Check if subject exists
    subject = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
    if subject is None:
        return jsonify({'outcome': 'error, specified subject does not exist'})
    
    # Update the subject
    execute_query(f'UPDATE materie SET {toModify} = %s WHERE materia = %s', (newValue, materia))
    
    # Log the update
    log('info', f'User {request.user_identity} updated subject {materia}')

    return jsonify({'outcome': 'subject successfully updated'})

@app.route('/api/bind_turn_to_student', methods = ['GET'])
@jwt_required_endpoint()
def bind_turn_to_student():

    # Gather parameters
    matricola = int(request.args.get('matricola'))
    idTurno = int(request.args.get('idTurno'))

    return bind_turn_to_student_logic(matricola, idTurno)    

def bind_turn_to_student_logic(matricola, idTurno):

    # Check if student exists
    student = fetchone_query('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
    if student is None:
        return jsonify({'outcome': 'error, specified student does not exist'})
    
    # Check if turn exists
    turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
    if turn is None:
        return jsonify({'outcome': 'error, specified turn does not exist'})
    
    # Check if the turn is full
    data = fetchone_query('SELECT posti, postiOccupati WHERE idTurno = %s', (idTurno,))
    ci_sono_posti = data["posti"] != data["postiOccupati"]
    if not ci_sono_posti:
        return jsonify({'outcome': 'error, no available spots for the specified turn'})

    # Bind the turn to the student
    execute_query('INSERT INTO studenteTurno (matricola, idTurno) VALUES (%s, %s)', (matricola, idTurno))

    # Update the number of occupied spots
    execute_query('UPDATE turni SET postiOccupati = postiOccupati + 1 WHERE idTurno = %s', (idTurno,))
    
    # Log the binding
    log('info', f'User {request.user_identity} binded student {matricola} to turn {idTurno}')

    return jsonify({'outcome': 'success, student binded to turn successfully'})

@app.route('/api/bind_company_to_user', methods = ['POST'])
@jwt_required_endpoint()
def bind_company_to_user():

    # Gather parameters
    email = request.args.get('email')
    anno = request.args.get('anno')
    idAzienda = request.args.get('idAzienda')

    return bind_company_to_user_logic(email, anno, idAzienda)
    
def bind_company_to_user_logic(email, anno, idAzienda):

    # Check if user exists
    user = fetchone_query('SELECT * FROM utenti WHERE emailUtente = %s', (email,))
    if user is None:
        return jsonify({'outcome': 'error, specified user does not exist'})
    
    # Check if company exists
    company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
    if company is None:
        return jsonify({'outcome': 'error, specified company does not exist'})
    
    # Bind the company to the user
    execute_query('INSERT INTO utenteAzienda (emailUtente, idAzienda, anno) VALUES (%s, %s, %s)', (email, idAzienda, anno))
    
    # Log the binding
    log('info', f'User {request.user_identity} binded company {idAzienda} to user {email}')

    return jsonify({'outcome': 'success, company binded to user successfully'})

@app.route('/api/bind_turn_to_sector', methods=['POST'])
@jwt_required_endpoint()
def bind_turn_to_sector():
    # Gather parameters
    idTurno = int(request.args.get('idTurno'))
    settore = request.args.get('settore')

    # Call the reusable logic
    return bind_turn_to_sector_logic(idTurno, settore)

def bind_turn_to_sector_logic(idTurno, settore):
    """
    Logic to bind a turn to a sector.
    """

    # Check if turn exists
    turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
    if turn is None:
        return {'outcome': 'error, specified turn does not exist'}
    
    # Check if sector exists
    sector = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore,))
    if sector is None:
        return {'outcome': 'error, specified sector does not exist'}
    
    # Bind the turn to the sector
    execute_query('INSERT INTO turnoSectore (idTurno, settore) VALUES (%s, %s)', (idTurno, settore))
    
    # Log the binding
    log('info', f'User {request.user_identity} binded turn {idTurno} to sector {settore}')

    return jsonify({'outcome': 'success, turn binded to sector successfully'})

@app.route('/api/bind_turn_to_subject', methods = ['POST'])
@jwt_required_endpoint()
def bind_turn_to_subject():

    # Gather parameters
    idTurno = int(request.args.get('idTurno'))
    materia = request.args.get('materia')

    return bind_turn_to_subject_logic(idTurno, materia)

def bind_turn_to_subject_logic(idTurno, materia):

    # Check if turn exists
    turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
    if turn is None:
        return jsonify({'outcome': 'error, specified turn does not exist'})
    
    # Check if subject exists
    subject = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
    if subject is None:
        return jsonify({'outcome': 'error, specified subject does not exist'})
    
    # Bind the turn to the subject
    execute_query('INSERT INTO turnoMateria (idTurno, materia) VALUES (%s, %s)', (idTurno, materia))
    
    # Log the binding
    log('info', f'User {request.user_identity} binded turn {idTurno} to subject {materia}')
    
    return jsonify({'outcome': 'success, turn binded to subject successfully'})

if __name__ == '__main__':
    app.run(host=API_SERVER_HOST, 
            port=API_SERVER_PORT,
            debug=True)  # Bind to the specific IP address