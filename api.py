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

    # Gather GET parameters
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

@app.route('/api/user_register', methods=['GET'])
def user_register():

    # Gather GET parameters
    email = request.args.get('email')
    password = request.args.get('password')
    name = request.args.get('nome')
    surname = request.args.get('cognome')
    type = request.args.get('tipo')
    
    # Create new cursor
    cursor = conn.cursor(dictionary=True)
    
    # Find out if user already exists
    cursor.execute('SELECT * FROM utenti WHERE emailUtente = %s', (email,))
    user = cursor.fetchone()
    if user is not None:
        return jsonify({"outcome": "error, user with provided credentials already exists"})  # If it does return error data
    
    # If not insert the user
    cursor.execute('INSERT INTO utente (emailUtente, password, nome, cognome, tipo) VALUES (%s, %s, %s, %s, %s)', (email, password, name, surname, int(type)))
    return jsonify({"outcome": "user successfully created"})

@app.route('/api/user_update', methods=['GET'])
def user_update():
    
    # Gather GET parameters
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
    return jsonify({'outcome': 'user successfully updated'})

@app.route('/api/user_delete', methods=['GET'])
def user_delete():
    
    # Gather GET parameters
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
    return jsonify({'outcome': 'user successfully deleted'})

@app.route('/api/class_register', methods=['GET'])
def class_register():
    # Gather GET parameters
    classe = request.args.get('classe')
    anno = request.args.get('anno')
    emailResponsabile = request.args.get('emailResponsabile')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)
    
    # Find out if class with provided values already exists
    cursor.execute('SELECT * FROM classi WHERE classe = %s AND anno = %s', (classe, anno))
    classe = cursor.fetchone()
    if classe is None: # If it does return an error
        return jsonify({"outcome": "error, class with provided data already exists"})            
    else: # If not proceed with the insert
        cursor.execute('INSERT INTO classi (classe, anno, emailResponsabile) VALUES (%s, %s, %s)', (classe, anno, emailResponsabile))
        return jsonify({"outcome": "class successfully created"})

@app.route('/api/class_delete', methods=['GET'])
def class_delete():
    # Gather GET parameters
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
    return jsonify({'outcome': 'class successfully deleted'})

@app.route('/api/class_update', methods=['GET'])
def class_update():
    # Gather GET parameters
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
    return jsonify({'outcome': 'class successfully updated'})

@app.route('/api/student_register', methods=['GET'])
def student_register():
    # Gather GET parameters
    matricola = request.args.get('matricola')
    nome = request.args.get('nome')
    cognome = request.args.get('cognome')
    idClasse = request.args.get('idClasse')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Find out if students already exists
    cursor.execute('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
    student = cursor.fetchone()
    if student is None: #If it does return an error
        return jsonify({'outcome': 'student with provided matricola already exists'})
    else: # If not proceed with the insert
        cursor.execute('INSERT INTO studenti VALUES (%s, %s, %s, %s)', (matricola, nome, cognome, idClasse))
        return jsonify({"outcome": "student successfully created"})

@app.route('/api/student_delete', methods=['GET'])
def student_delete():
    # Gather GET parameters
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
    return jsonify({'outcome': 'student successfully deleted'})

@app.route('/api/student_update', methods=['GET'])
def student_update():
    # Gather GET parameters
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
    return jsonify({'outcome': 'student successfully updated'})

@app.route('/api/turn_register', methods=['GET'])
def turn_register():

    # Gather GET parameters
    settore = request.args.get('settore')
    posti = request.args.get('posti')
    ore = request.args.get('ore')
    idAzienda = int(request.args.get('idAzienda'))
    idIndirizzo = request.args.get('idIndirizzo')
    idTutor = request.args.get('idTutor')
    dataInizio = parse_date_string(date_string=request.args.get('dataInizio'))
    dataFine = parse_date_string(date_string=request.args.get('dataFine'))
    oraInizio =  parse_time_string(time_string=request.args.get('oraInizio'))
    oraFine = parse_time_string(time_string=request.args.get('oraFine'))

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if idAzienda exists
    cursor.execute('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda))
    company = cursor.fetchone()
    if company is None:
        return jsonify({'outcome': 'error, specified company does not exist'})

    # Check if idIndirizzo exist
    cursor.execute('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (int(idIndirizzo)))
    address = cursor.fetchone()
    if address is None:
        return jsonify({'outcome': 'error, specified address does not exist'})
    
    # Check if settore exists
    cursor.execute('SELECT * FROM settori WHERE settore = %s', (settore,))
    sector = cursor.fetchone()
    if sector is None:
        return jsonify({'outcome': 'error, specified sector does not exist'})
    
    # Check if idTutor exists
    cursor.execute('SELECT * FROM tutor WHERE idTutor = %s', (int(idTutor)))
    tutor = cursor.fetchone()
    if tutor is None:
        return jsonify({'outcome': 'error, specified tutor does not exist'})
    
    # Insert the turn
    cursor.execute('INSERT INTO turni (dataInizio, dataFine, settore, posti, ore, idAzienda, idIndirizzo, idTutor, oraInizio, oraFine) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', 
                   (dataInizio, dataFine, settore, posti, ore, idAzienda, idIndirizzo, idTutor, oraInizio, oraFine))
    return jsonify({'outcome': 'turn successfully created'})

@app.route('/api/turn_delete', methods=['GET'])
def turn_delete():
    
    # Gather GET parameters
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
    return jsonify({'outcome': 'turn successfully deleted'})

@app.route('/api/turn_update', methods=['GET'])
def turn_update():

    # Gather GET parameters
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
    return jsonify({'outcome': 'turn successfully updated'})

@app.route('/api/address_register', methods=['GET'])
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
    return jsonify({'outcome': 'address successfully created'})

@app.route('/api/address_delete', methods=['GET'])
def address_delete():
    
    # Gather GET parameters
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
    return jsonify({'outcome': 'address successfully deleted'})

@app.route('/api/address_update', methods=['GET'])
def address_update():

    # Gather GET parameters
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
    return jsonify({'outcome': 'address successfully updated'})

@app.route('/api/contact_register', methods=['GET'])
def contact_register():

    # Gather GET parameters
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

@app.route('/api/contact_delete', methods=['GET'])
def contact_delete():

    # Gather GET parameters
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
    return jsonify({'outcome': 'contact successfully deleted'})

@app.route('/api/contact_update', methods=['GET'])
def contact_update():

    # Gather GET parameters
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
    return jsonify({'outcome': 'contact successfully updated'})

@app.route('/api/sector_register', methods=['GET'])
def sector_register():
    
    # Gather GET parameters
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
    return jsonify({'outcome': 'sector successfully created'})

@app.route('/api/sector_delete', methods=['GET'])
def sector_delete():
    
    # Gather GET parameters
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
    return jsonify({'outcome': 'sector successfully deleted'})

@app.route('/api/sector_update', methods=['GET'])
def sector_update():

    # Gather GET parameters
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
    return jsonify({'outcome': 'sector successfully updated'})

@app.route('/api/subject_register', methods=['GET'])
def subject_register():
    
    # Gather GET parameters
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
    return jsonify({'outcome': 'subject successfully created'})

@app.route('/api/subject_delete', methods=['GET'])
def subject_delete():

    # Gather GET parameters
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
    return jsonify({'outcome': 'subject successfully deleted'})

@app.route('/api/subject_update', methods=['GET'])
def subject_update():
    
    # Gather GET parameters
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
    return jsonify({'outcome': 'subject successfully updated'})

@app.route('/api/tutor_register', methods=['GET'])
def tutor_register():

    # Gather GET parameters
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
    return jsonify({'outcome': 'tutor successfully created'})

@app.route('/api/tutor_delete', methods=['GET'])
def tutor_delete():
    # Gather GET parameters
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
    return jsonify({'outcome': 'tutor successfully deleted'})

@app.route('/api/tutor_update', methods=['GET'])
def tutor_update():
    
    # Gather GET parameters
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
    return jsonify({'outcome': 'tutor successfully updated'})

@app.route('/api/company_register', methods=['GET'])
def company_register():

    # Gather GET parameters
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

    # Check if company already exists
    cursor.execute('SELECT * FROM aziende WHERE ragioneSociale = %s', (ragioneSociale,))
    company = cursor.fetchone()
    if company is None:
        return jsonify({'outcome': 'error, specified company already exists'})
    
    # Insert the company
    cursor.execute('INSERT INTO aziende (ragioneSociale, nome, sitoWeb, indirizzoLogo, codiceAteco, partitaIVA, telefonoAzienda, fax, emailAzienda, pec, formaGiuridica, dataConvenzione, scadenzaConvenzione, settore, categoria) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', 
                   (ragioneSociale, nome, sitoWeb, indirizzoLogo, codiceAteco, partitaIVA, telefonoAzienda, fax, emailAzienda, pec, formaGiuridica, dataConvenzione, scadenzaConvenzione, settore, categoria))
    return jsonify({'outcome': 'company successfully created'})

@app.route('/api/company_delete', methods=['GET'])
def company_delete():
    # Gather GET parameters
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
    return jsonify({'outcome': 'company successfully deleted'})

@app.route('/api/company_update', methods=['GET'])
def company_update():

    # Gather GET parameters
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
    return jsonify({'outcome': 'company successfully updated'})

@app.route('/api/bind_turn_to_student', methods = ['GET'])
def bind_turn_to_student():

    # Gather GET parameters
    matricola = int(request.args.get('matricola'))
    idTurno = int(request.args.get('idTurno'))

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
    return jsonify({'outcome': 'success, student binded to turn successfully'})

@app.route('/api/bind_company_to_user', methods = ['GET'])
def bind_company_to_user():

    # Gather GET parameters
    email = request.args.get('email')
    anno = request.args.get('anno')
    idAzienda = request.args.get('idAzienda')

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
    return jsonify({'outcome': 'success, company binded to user successfully'})

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
    return {'outcome': 'success, turn binded to sector successfully'}

@app.route('/api/bind_turn_to_sector', methods=['GET'])
def bind_turn_to_sector():
    # Gather GET parameters
    idTurno = int(request.args.get('idTurno'))
    settore = request.args.get('settore')

    # Call the reusable logic
    result = bind_turn_to_sector_logic(idTurno, settore)
    return jsonify(result)

@app.route('/api/bind_turn_to_subject', methods = ['GET'])
def bind_turn_to_subject():

    # Gather GET parameters
    idTurno = int(request.args.get('idTurno'))
    materia = request.args.get('materia')

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
    return jsonify({'outcome': 'success, turn binded to subject successfully'})

def close_api(signal, frame):  # Parameters are necessary even if not used because it has to match the signal signature
    conn.close()
    exit(0)  # Close the API

signal.signal(signal.SIGINT, close_api)  # Bind CTRL+C to close_api function

if __name__ == '__main__':
    app.run(host='172.16.1.98', 
            port=12345,
            debug=True)  # Bind to the specific IP address