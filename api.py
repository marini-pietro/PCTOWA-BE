from flask import Flask, jsonify, request
from datetime import datetime
import mysql.connector, signal

def parse_time_string(time_string) -> datetime:
    """
    Parse a time string in the format HH:MM and return a datetime object.
    
    params:
        time_string - The time string to parse
    
    returns: 
        A datetime object if the string is in the correct format, None otherwise

    """

    try: return datetime.strptime(time_string, '%H:%M').time()
    except ValueError: return None

def parse_date_string(date_string) -> datetime:
    """
    Parse a date string in the format YYYY-MM-DD and return a datetime object.
    
    params:
        date_string - The date string to parse
    
    returns: 
        A datetime object if the string is in the correct format, None otherwise

    """

    try: return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError: return None

conn = mysql.connector.connect(
    host='localhost',
    user='pctowa',
    password='pctowa2025',
    database='pctowa'
)
app = Flask(__name__)

@app.route('/api/user_login', methods=['GET'])
def user_login():

    # Gather parameters
    username = request.args.get('email')
    password = request.args.get('password')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)
    
    # Check if user exists
    cursor.execute('SELECT * FROM utenti WHERE emailUtente = %s AND password = %s', (username, password))
    user = cursor.fetchone()
    if user is None:
        return jsonify({"outcome": "error, user with provided credentials does not exist"})
    
    # Return that the user exists
    return jsonify({"outcome": "user with provided credentials exists"})

@app.route('/api/user_register', methods=['POST'])
def user_register():

    # Gather parameters
    email = request.args.get('email')
    password = request.args.get('password')
    name = request.args.get('nome')
    surname = request.args.get('cognome')
    type = request.args.get('tipo')
    
    # Create new cursor
    cursor = conn.cursor(dictionary=True)
    
    # Insert the user
    try:
        cursor.execute('INSERT INTO utente (emailUtente, password, nome, cognome, tipo) VALUES (%s, %s, %s, %s, %s)', (email, password, name, surname, int(type)))
        conn.commit()
        return jsonify({"outcome": "user successfully created"})
    except mysql.connector.IntegrityError as ex:
        return jsonify({'outcome': 'error, user with provided credentials already exists'})

@app.route('/api/user_update', methods=['PATCH'])
def user_update():
    
    # Gather parameters
    email = request.args.get('email')
    toModify = request.args.get('toModify')
    newValue = request.args.get('newValue')

    # Check if the field to modify is allowed
    if toModify in ['email']:
        return jsonify({'outcome': 'error, specified field cannot be modified'})
    
    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if user exists
    cursor.execute('SELECT * FROM utente WHERE emailUtente = %s', (email,))
    user = cursor.fetchone()
    if user is None:
        return jsonify({'outcome': 'error, user with provided email does not exist'})
    
    # Update the user
    cursor.execute(f'UPDATE utente SET {toModify} = %s WHERE emailUtente = %s', (newValue, email))
    conn.commit()
    return jsonify({'outcome': 'user successfully updated'})

@app.route('/api/user_delete', methods=['DELETE'])
def user_delete():
    
    # Gather parameters
    email = request.args.get('email')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if user exists
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cursor.fetchone()
    if user is None:
        return jsonify({'outcome': 'error, user with provided email does not exist'})
    
    # Delete the user
    cursor.execute('DELETE FROM users WHERE email = %s', (email,))
    conn.commit()
    return jsonify({'outcome': 'user successfully deleted'})

@app.route('/api/class_register', methods=['POST'])
def class_register():
    # Gather parameters
    classe = request.args.get('classe')
    anno = request.args.get('anno')
    emailResponsabile = request.args.get('emailResponsabile')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)          
    
    try:
        cursor.execute('INSERT INTO classi (classe, anno, emailResponsabile) VALUES (%s, %s, %s)', (classe, anno, emailResponsabile))
        conn.commit()
        return jsonify({"outcome": "class successfully created"})
    except mysql.connector.IntegrityError as ex:
        return jsonify({'outcome': 'error, class with provided credentials already exists'})

@app.route('/api/class_delete', methods=['DELETE'])
def class_delete():
    # Gather parameters
    idClasse = request.args.get('idClasse')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if class exists
    cursor.execute('SELECT * FROM classi WHERE idClasse = %s', (idClasse,))
    classe = cursor.fetchone()
    if classe is None:
        return jsonify({'outcome': 'error, specified class does not exist'})
    
    # Delete the class
    cursor.execute('DELETE FROM classi WHERE idClasse = %s', (idClasse,))
    conn.commit()
    return jsonify({'outcome': 'class successfully deleted'})

@app.route('/api/class_update', methods=['PATCH'])
def class_update():
    # Gather parameters
    idClasse = request.args.get('idClasse')
    toModify = request.args.get('toModify')
    newValue = request.args.get('newValue')

    # Check if the field to modify is allowed
    if toModify in ['idClasse']:
        return jsonify({'outcome': 'error, specified field cannot be modified'})
    
    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if class exists
    cursor.execute('SELECT * FROM classi WHERE idClasse = %s', (idClasse))
    classe = cursor.fetchone()
    if classe is None:
        return jsonify({'outcome': 'error, specified class does not exist'})
    
    # Update the class
    cursor.execute(f'UPDATE classi SET {toModify} = %s WHERE idClasse = %s', (newValue, idClasse))
    conn.commit()
    return jsonify({'outcome': 'class successfully updated'})

@app.route('/api/class_read', methods = ['GET'])
def class_read():
    # Gather parameters
    try:
        idClasse = int(request.args.get('idClasse'))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid idClasse parameter"}), 400

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Execute query
    try:
        cursor.execute('SELECT * FROM classi WHERE idClasse = %s', (idClasse,))
        return jsonify(cursor.fetchall()), 200
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

@app.route('/api/student_register', methods=['POST'])
def student_register():
    # Gather parameters
    matricola = request.args.get('matricola')
    nome = request.args.get('nome')
    cognome = request.args.get('cognome')
    idClasse = request.args.get('idClasse')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute('INSERT INTO studenti VALUES (%s, %s, %s, %s)', (matricola, nome, cognome, idClasse))
        conn.commit()
        return jsonify({"outcome": "student successfully created"})
    except mysql.connector.IntegrityError as ex:
        return jsonify({'outcome': 'student with provided matricola already exists'})

@app.route('/api/student_delete', methods=['DELETE'])
def student_delete():
    # Gather parameters
    matricola = request.args.get('matricola')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if student exists
    cursor.execute('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
    student = cursor.fetchone()
    if student is None:
        return jsonify({'outcome': 'error, specified student does not exist'})
    
    # Delete the student
    cursor.execute('DELETE FROM studenti WHERE matricola = %s', (matricola,))
    conn.commit()
    return jsonify({'outcome': 'student successfully deleted'})

@app.route('/api/student_update', methods=['PATCH'])
def student_update():
    # Gather parameters
    matricola = request.args.get('matricola')
    toModify = request.args.get('toModify')
    newValue = request.args.get('newValue')

    # Check if the field to modify is allowed
    if toModify in ['matricola']:
        return jsonify({'outcome': 'error, specified field cannot be modified'})
    
    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if student exists
    cursor.execute('SELECT * FROM studenti WHERE matricola = %s', (matricola))
    student = cursor.fetchone()
    if student is None:
        return jsonify({'outcome': 'error, specified student does not exist'})
    
    # Update the student
    cursor.execute(f'UPDATE studenti SET {toModify} = %s WHERE matricola = %s', (newValue, matricola))
    conn.commit()
    return jsonify({'outcome': 'student successfully updated'})

@app.route('/api/student_read', methods = ['GET'])
def student_read():
    # Gather parameters
    try:
        matricola = int(request.args.get('matricola'))
    except (ValueError, TypeError):
        return jsonify({'error': 'invalid matricola parameter'}), 400
    
    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Execute query
    try:
        cursor.execute('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
        return jsonify(cursor.fetchall()), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/api/turn_register', methods=['POST'])
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

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if idAzienda exists
    cursor.execute('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda))
    company = cursor.fetchone()
    if company is None:
        return jsonify({'outcome': 'error, specified company does not exist'})

    # Check that idIndirizzo exist if an idIndirizzo is provided
    if idIndirizzo is not None: 
        cursor.execute('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (int(idIndirizzo)))
        address = cursor.fetchone()
        if address is None:
            return jsonify({'outcome': 'error, specified address does not exist'})
        
    # Check that settore if one is provided
    if settore is not None: 
        cursor.execute('SELECT * FROM settori WHERE settore = %s', (settore,))
        sector = cursor.fetchone()
        if sector is None:
            return jsonify({'outcome': 'error, specified sector does not exist'})
    
    # Check that idTutor exists if one is provided
    if idTutor is not None:
        cursor.execute('SELECT * FROM tutor WHERE idTutor = %s', (int(idTutor)))
        tutor = cursor.fetchone()
        if tutor is None:
            return jsonify({'outcome': 'error, specified tutor does not exist'})
    
    # Insert the turn
    cursor.execute('INSERT INTO turni (dataInizio, dataFine, settore, posti, ore, idAzienda, idIndirizzo, idTutor, oraInizio, oraFine) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', 
                   (dataInizio, dataFine, settore, posti, ore, idAzienda, idIndirizzo, idTutor, oraInizio, oraFine))
    conn.commit()
    return jsonify({'outcome': 'turn successfully created'}), 201

@app.route('/api/turn_delete', methods=['DELETE'])
def turn_delete():
    
    # Gather parameters
    idTurno = int(request.args.get('idTurno'))

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if turn exists
    cursor.execute('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
    turn = cursor.fetchone()
    if turn is None:
        return jsonify({'outcome': 'error, specified turn does not exist'})
    
    # Delete the turn
    cursor.execute('DELETE FROM turni WHERE idTurno = %s', (idTurno,))
    conn.commit()
    return jsonify({'outcome': 'turn successfully deleted'})

@app.route('/api/turn_update', methods=['PATCH'])
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
    
    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if turn exists
    cursor.execute('SELECT * FROM turni WHERE idTurno = %s', (idTurno))
    turn = cursor.fetchone()
    if turn is None:
        return jsonify({'outcome': 'error, specified turn does not exist'})
    
    # Update the turn
    cursor.execute(f'UPDATE turni SET {toModify} = %s WHERE idTurno = %s', (newValue, idTurno))
    conn.commit()
    return jsonify({'outcome': 'turn successfully updated'})

@app.route('/api/turn_read', methods=['GET'])
def turn_read():
    # Gather parameters
    try:
        idTurno = int(request.args.get('idTurno'))
    except (ValueError, TypeError):
        return jsonify({'error': 'invalid idTurno parameter'}), 400
    
    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Execute query
    try:
        cursor.execute('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
        return jsonify(cursor.fetchall()), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/api/address_register', methods=['POST'])
def address_register():

    #Gather GET parameters
    stato = request.args.get('stato')
    provincia = request.args.get('provincia')
    comune = request.args.get('comune')
    cap = request.args.get('cap')
    indirizzo = request.args.get('indirizzo')
    idAzienda = int(request.args.get('idAzienda'))

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if idAzienda exists
    cursor.execute('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda))
    company = cursor.fetchone()
    if company is None:
        return jsonify({'outcome': 'error, specified company does not exist'})
    
    # Insert the address
    cursor.execute('INSERT INTO indirizzi (stato, provincia, comune, cap, indirizzo, idAzienda) VALUES (%s, %s, %s, %s, %s, %s)', 
                   (stato, provincia, comune, cap, indirizzo, idAzienda))
    conn.commit()
    return jsonify({'outcome': 'address successfully created'})

@app.route('/api/address_delete', methods=['DELETE'])
def address_delete():
    
    # Gather parameters
    idIndirizzo = int(request.args.get('idIndirizzo'))

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if address exists
    cursor.execute('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))
    address = cursor.fetchone()
    if address is None:
        return jsonify({'outcome': 'error, specified address does not exist'})
    
    # Delete the address
    cursor.execute('DELETE FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))
    conn.commit()
    return jsonify({'outcome': 'address successfully deleted'})

@app.route('/api/address_update', methods=['PATCH'])
def address_update():

    # Gather parameters
    idIndirizzo = int(request.args.get('idIndirizzo'))
    toModify = request.args.get('toModify')
    newValue = request.args.get('newValue')

    # Check if the field to modify is allowed
    if toModify in ['idIndirizzo']:
        return jsonify({'outcome': 'error, specified field cannot be modified'})
    
    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if address exists
    cursor.execute('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo))
    address = cursor.fetchone()
    if address is None:
        return jsonify({'outcome': 'error, specified address does not exist'})
    
    # Update the address
    cursor.execute(f'UPDATE indirizzi SET {toModify} = %s WHERE idIndirizzo = %s', (newValue, idIndirizzo))
    conn.commit()
    return jsonify({'outcome': 'address successfully updated'})

@app.route('/api/address_read', methods = ['GET'])
def address_read():
    #Gather parameters
    try:
        idIndirizzo = int(request.args.get('idIndirizzo'))
    except (ValueError, TypeError):
        return jsonify({'error': 'invalid idIndirizzo parameter'}), 400
    
    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Execute query
    try:
        cursor.execute('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))
        return jsonify(cursor.fetchall()), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/api/contact_register', methods=['POST'])
def contact_register():

    # Gather parameters
    nome = request.args.get('nome')
    cognome = request.args.get('cognome')
    telefono = request.args.get('telefono')
    email = request.args.get('email')
    ruolo = request.args.get('ruolo')
    idAzienda = int(request.args.get('idAzienda'))

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if idAzienda exists
    cursor.execute('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda))
    company = cursor.fetchone()
    if company is None:
        return jsonify({'outcome': 'error, specified company does not exist'})
    
    # Insert the contact
    cursor.execute('INSERT INTO contatti (nome, cognome, telefono, email, ruolo, idAzienda) VALUES (%s, %s, %s, %s, %s, %s)', 
                   (nome, cognome, telefono, email, ruolo, idAzienda))
    conn.commit()
    return jsonify({'outcome': 'success, company inserted'})

@app.route('/api/contact_delete', methods=['DELETE'])
def contact_delete():

    # Gather parameters
    idContatto = int(request.args.get('idContatto'))

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if contact exists
    cursor.execute('SELECT * FROM contatti WHERE idContatto = %s', (idContatto,))
    contact = cursor.fetchone()
    if contact is None:
        return jsonify({'outcome': 'error, specified contact does not exist'})
    
    # Delete the contact
    cursor.execute('DELETE FROM contatti WHERE idContatto = %s', (idContatto,))
    conn.commit()
    return jsonify({'outcome': 'contact successfully deleted'})

@app.route('/api/contact_update', methods=['PATCH'])
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
    
    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if contact exists
    cursor.execute('SELECT * FROM contatti WHERE idContatto = %s', (idContatto))
    contact = cursor.fetchone()
    if contact is None:
        return jsonify({'outcome': 'error, specified contact does not exist'})
    
    # Update the contact
    cursor.execute(f'UPDATE contatti SET {toModify} = %s WHERE idContatto = %s', (newValue, idContatto))
    conn.commit()
    return jsonify({'outcome': 'contact successfully updated'})

@app.route('/api/contact_read', methods = ['GET'])
def contact_read():
    # Gather parameters
    try:
        idContatto = int(request.args.get('idContatto'))
    except (ValueError, TypeError):
        return jsonify({'error': 'invalid idContatto parameter'}), 400

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Execute query
    try:
        cursor.execute('SELECT * FROM contatti WHERE idContatto = %s', (idContatto,))
        return jsonify(cursor.fetchall()), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/api/sector_register', methods=['POST'])
def sector_register():
    
    # Gather parameters
    settore = request.args.get('settore')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if sector exists
    cursor.execute('SELECT * FROM settori WHERE settore = %s', (settore,))
    sector = cursor.fetchone()
    if sector is None:
        return jsonify({'outcome': 'error, specified sector already exists'})
    
    # Insert the sector
    cursor.execute('INSERT INTO settori (settore) VALUES (%s)', (settore,))
    conn.commit()
    return jsonify({'outcome': 'sector successfully created'})

@app.route('/api/sector_delete', methods=['DELETE'])
def sector_delete():
    
    # Gather parameters
    settore = request.args.get('settore')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if sector exists
    cursor.execute('SELECT * FROM settori WHERE settore = %s', (settore,))
    sector = cursor.fetchone()
    if sector is None:
        return jsonify({'outcome': 'error, specified sector does not exist'})
    
    # Delete the sector
    cursor.execute('DELETE FROM settori WHERE settore = %s', (settore,))
    conn.commit()
    return jsonify({'outcome': 'sector successfully deleted'})

@app.route('/api/sector_update', methods=['PATCH'])
def sector_update():

    # Gather parameters
    settore = request.args.get('settore')
    newValue = request.args.get('newValue')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if sector exists
    cursor.execute('SELECT * FROM settori WHERE settore = %s', (settore,))
    sector = cursor.fetchone()
    if sector is None:
        return jsonify({'outcome': 'error, specified sector does not exist'})
    
    # Update the sector
    cursor.execute('UPDATE settori SET settore = %s WHERE settore = %s', (newValue, settore))
    conn.commit()
    return jsonify({'outcome': 'sector successfully updated'})

@app.route('/api/subject_register', methods=['POST'])
def subject_register():
    
    # Gather parameters
    materia = request.args.get('materia')
    descrizione = request.args.get('descrizione')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if subject exists
    cursor.execute('SELECT * FROM materie WHERE materia = %s', (materia,))
    subject = cursor.fetchone()
    if subject is None:
        return jsonify({'outcome': 'error, specified subject already exists'})
    
    # Insert the subject
    cursor.execute('INSERT INTO materie (materia, descr) VALUES (%s)', (materia,descrizione))
    conn.commit()
    return jsonify({'outcome': 'subject successfully created'})

@app.route('/api/subject_delete', methods=['DELETE'])
def subject_delete():

    # Gather parameters
    materia = request.args.get('materia')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if subject exists
    cursor.execute('SELECT * FROM materie WHERE materia = %s', (materia,))
    subject = cursor.fetchone()
    if subject is None:
        return jsonify({'outcome': 'error, specified subject does not exist'})
    
    # Delete the subject
    cursor.execute('DELETE FROM materie WHERE materia = %s', (materia,))
    conn.commit()
    return jsonify({'outcome': 'subject successfully deleted'})

@app.route('/api/subject_update', methods=['PATCH'])
def subject_update():
    
    # Gather parameters
    materia = request.args.get('materia')
    toModify = request.args.get('toModify')
    newValue = request.args.get('newValue')

    # Check if the field to modify is allowed
    if toModify in ['materia']:
        return jsonify({'outcome': 'error, specified field cannot be modified'})
    
    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if subject exists
    cursor.execute('SELECT * FROM materie WHERE materia = %s', (materia))
    subject = cursor.fetchone()
    if subject is None:
        return jsonify({'outcome': 'error, specified subject does not exist'})
    
    # Update the subject
    cursor.execute(f'UPDATE materie SET {toModify} = %s WHERE materia = %s', (newValue, materia))
    conn.commit()
    return jsonify({'outcome': 'subject successfully updated'})

@app.route('/api/tutor_register', methods=['POST'])
def tutor_register():

    # Gather parameters
    nome = request.args.get('nome')
    cognome = request.args.get('cognome')
    telefono = request.args.get('telefono')
    email = request.args.get('email')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if tutor already exists by checking if the combination of email and phone number already exists
    cursor.execute('SELECT * FROM tutor WHERE emailTutor = %s AND telefonoTutor = %s', (email, telefono))
    tutor = cursor.fetchone()
    if tutor is None:
        return jsonify({'outcome': 'error, specified company does not exist'})
    
    # Insert the tutor
    cursor.execute('INSERT INTO tutor (nome, cognome, telefonoTutor, emailTutor) VALUES (%s, %s, %s, %s)', 
                   (nome, cognome, telefono, email))
    conn.commit()
    return jsonify({'outcome': 'tutor successfully created'})

@app.route('/api/tutor_delete', methods=['DELETE'])
def tutor_delete():
    # Gather parameters
    idTutor = int(request.args.get('idTutor'))

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if tutor exists
    cursor.execute('SELECT * FROM tutor WHERE idTutor = %s', (idTutor,))
    tutor = cursor.fetchone()
    if tutor is None:
        return jsonify({'outcome': 'error, specified tutor does not exist'})
    
    # Delete the tutor
    cursor.execute('DELETE FROM tutor WHERE idTutor = %s', (idTutor,))
    conn.commit()
    return jsonify({'outcome': 'tutor successfully deleted'})

@app.route('/api/tutor_update', methods=['PATCH'])
def tutor_update():
    
    # Gather parameters
    idTutor = int(request.args.get('idTutor'))
    toModify = request.args.get('toModify')
    newValue = request.args.get('newValue')

    # Check if the field to modify is allowed
    if toModify in ['idTutor']:
        return jsonify({'outcome': 'error, specified field cannot be modified'})
    
    # Check if any casting operations are needed
    if toModify in ['telefonoTutor']:
        newValue = int(newValue)

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if tutor exists
    cursor.execute('SELECT * FROM tutor WHERE idTutor = %s', (idTutor))
    tutor = cursor.fetchone()
    if tutor is None:
        return jsonify({'outcome': 'error, specified tutor does not exist'})
    
    # Update the tutor
    cursor.execute(f'UPDATE tutor SET {toModify} = %s WHERE idTutor = %s', (newValue, idTutor))
    conn.commit()
    return jsonify({'outcome': 'tutor successfully updated'})

@app.route('/api/company_register', methods=['POST'])
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

    # Create new cursor
    cursor = conn.cursor(dictionary=True)
    
    # Insert the company
    try:
        cursor.execute('INSERT INTO aziende (ragioneSociale, nome, sitoWeb, indirizzoLogo, codiceAteco, partitaIVA, telefonoAzienda, fax, emailAzienda, pec, formaGiuridica, dataConvenzione, scadenzaConvenzione, settore, categoria) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', 
                    (ragioneSociale, nome, sitoWeb, indirizzoLogo, codiceAteco, partitaIVA, telefonoAzienda, fax, emailAzienda, pec, formaGiuridica, dataConvenzione, scadenzaConvenzione, settore, categoria))
        conn.commit()
        return jsonify({'outcome': 'company successfully created'})
    except mysql.connector.IntegrityError as ex:
        return jsonify({'outcome': 'error, company already exists, integrity error: {ex}'})

@app.route('/api/company_delete', methods=['DELETE'])
def company_delete():
    # Gather parameters
    idAzienda = int(request.args.get('idAzienda'))

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if company exists
    cursor.execute('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
    company = cursor.fetchone()
    if company is None:
        return jsonify({'outcome': 'error, specified company does not exist'})

    # Delete the company (cascade delete will handle related rows)
    cursor.execute('DELETE FROM aziende WHERE idAzienda = %s', (idAzienda,))
    conn.commit()
    return jsonify({'outcome': 'company successfully deleted'})

@app.route('/api/company_update', methods=['PATCH'])
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

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if company exists
    cursor.execute('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda))
    company = cursor.fetchone()
    if company is None:
        return jsonify({'outcome': 'error, specified company does not exist'})
    
    # Update the company
    cursor.execute(f'UPDATE aziende SET {toModify} = %s WHERE idAzienda = %s', (newValue, idAzienda))
    conn.commit()
    return jsonify({'outcome': 'company successfully updated'})

@app.route('/api/bind_turn_to_student', methods = ['GET'])
def bind_turn_to_student():

    # Gather parameters
    matricola = int(request.args.get('matricola'))
    idTurno = int(request.args.get('idTurno'))

    return bind_turn_to_student_logic    

def bind_turn_to_student_logic(matricola, idTurno):
    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if student exists
    cursor.execute('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
    student = cursor.fetchone()
    if student is None:
        return jsonify({'outcome': 'error, specified student does not exist'})
    
    # Check if turn exists
    cursor.execute('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
    turn = cursor.fetchone()
    if turn is None:
        return jsonify({'outcome': 'error, specified turn does not exist'})
    
    # Check if the turn is full
    cursor.execute('SELECT posti, postiOccupati WHERE idTurno = %s', (idTurno,))
    data = cursor.fecthone()
    ci_sono_posti = data["posti"] != data["postiOccupati"]
    if not ci_sono_posti:
        return jsonify({'outcome': 'error, no available spots for the specified turn'})

    # Bind the turn to the student
    cursor.execute('INSERT INTO studenteTurno (matricola, idTurno) VALUES (%s, %s)', (matricola, idTurno))
    conn.commit()
    return jsonify({'outcome': 'success, student binded to turn successfully'})

@app.route('/api/bind_company_to_user', methods = ['POST'])
def bind_company_to_user():

    # Gather parameters
    email = request.args.get('email')
    anno = request.args.get('anno')
    idAzienda = request.args.get('idAzienda')

    return bind_company_to_user_logic(email, anno, idAzienda)
    
def bind_company_to_user_logic(email, anno, idAzienda):
    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if user exists
    cursor.execute('SELECT * FROM utenti WHERE emailUtente = %s', (email,))
    user = cursor.fetchone()
    if user is None:
        return jsonify({'outcome': 'error, specified user does not exist'})
    
    # Check if company exists
    cursor.execute('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
    company = cursor.fetchone()
    if company is None:
        return jsonify({'outcome': 'error, specified company does not exist'})
    
    # Bind the company to the user
    cursor.execute('INSERT INTO utenteAzienda (emailUtente, idAzienda, anno) VALUES (%s, %s, %s)', (email, idAzienda, anno))
    conn.commit()
    return jsonify({'outcome': 'success, company binded to user successfully'})

@app.route('/api/bind_turn_to_sector', methods=['POST'])
def bind_turn_to_sector():
    # Gather parameters
    idTurno = int(request.args.get('idTurno'))
    settore = request.args.get('settore')

    # Call the reusable logic
    result = bind_turn_to_sector_logic(idTurno, settore)
    return jsonify(result)

def bind_turn_to_sector_logic(idTurno, settore):
    """
    Logic to bind a turn to a sector.
    """
    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if turn exists
    cursor.execute('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
    turn = cursor.fetchone()
    if turn is None:
        return {'outcome': 'error, specified turn does not exist'}
    
    # Check if sector exists
    cursor.execute('SELECT * FROM settori WHERE settore = %s', (settore,))
    sector = cursor.fetchone()
    if sector is None:
        return {'outcome': 'error, specified sector does not exist'}
    
    # Bind the turn to the sector
    cursor.execute('INSERT INTO turnoSectore (idTurno, settore) VALUES (%s, %s)', (idTurno, settore))
    conn.commit()
    return {'outcome': 'success, turn binded to sector successfully'}

@app.route('/api/bind_turn_to_subject', methods = ['POST'])
def bind_turn_to_subject():

    # Gather parameters
    idTurno = int(request.args.get('idTurno'))
    materia = request.args.get('materia')

    return bind_turn_to_subject_logic(idTurno, materia)

def bind_turn_to_subject_logic(idTurno, materia):
    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if turn exists
    cursor.execute('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
    turn = cursor.fetchone()
    if turn is None:
        return jsonify({'outcome': 'error, specified turn does not exist'})
    
    # Check if subject exists
    cursor.execute('SELECT * FROM materie WHERE materia = %s', (materia,))
    subject = cursor.fetchone()
    if subject is None:
        return jsonify({'outcome': 'error, specified subject does not exist'})
    
    # Bind the turn to the subject
    cursor.execute('INSERT INTO turnoMateria (idTurno, materia) VALUES (%s, %s)', (idTurno, materia))
    conn.commit()
    return jsonify({'outcome': 'success, turn binded to subject successfully'})

def close_api(signal, frame):  # Parameters are necessary even if not used because it has to match the signal signature
    conn.close()
    exit(0)  # Close the API

signal.signal(signal.SIGINT, close_api)  # Bind CTRL+C to close_api function

if __name__ == '__main__':
    app.run(host='172.16.1.98', 
            port=12345,
            debug=True)  # Bind to the specific IP address