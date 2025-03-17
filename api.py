from flask import Flask, jsonify, request
import mysql.connector, signal

conn = mysql.connector.connect(
    host='localhost',
    user='pctowa',
    password='pctowa2025',
    database='pctowa'
)
app = Flask(__name__)

@app.route('/user_login', methods=['GET'])
def user_login():
    username = request.args.get('email')
    password = request.args.get('password')

    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE emailUtente = %s AND password = %s', (username, password))
    user = cursor.fetchone()
    if user is None:
        return jsonify({"outcome": "error, user with provided credentials does not exist"})
    else:
        return jsonify({"outcome": "user with provided credentials exists"})

@app.route('/user_register', methods=['GET'])
def user_register():
    email = request.args.get('email')
    password = request.args.get('password')
    name = request.args.get('nome')
    surname = request.args.get('cognome')
    type = request.args.get('tipo')
    
    cursor = conn.cursor(dictionary=True)
    # Find out if user already exists
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cursor.fetchone()
    if user is None:
        return jsonify({"outcome": "error, user with provided credentials already exists"})  # If it does return error data
    else:
        # If not insert the user
        cursor.execute('INSERT INTO users (email, password, nome, cognome, tipo) VALUES (%s, %s, %s, %s, %s)', (email, password, name, surname, int(type)))
        return jsonify({"outcome": "user successfully created"})

@app.route('/class_register', methods=['GET'])
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
    
@app.route('/student_register', methods=['GET'])
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

@app.route('/turn_register', methods=['GET'])
def turn_register():

    # Gather GET parameters
    dataInizio = request.args.get('dataInizio')
    dataFine = request.args.get('dataFine')
    settore = request.args.get('settore')
    posti = request.args.get('posti')
    ore = request.args.get('ore')
    idAzienda = request.args.get('idAzienda')
    idIndirizzo = request.args.get('idIndirizzo')
    idTutor = request.args.get('idTutor')
    oraInizio = request.args.get('oraInizio')
    oraFine = request.args.get('oraFine')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if idAzienda exists
    cursor.execute('SELECT * FROM aziende WHERE idAzienda = %s', (int(idAzienda,)))
    agency = cursor.fetchone()
    if agency is None:
        return jsonify({'outcome': 'error, specified agency does not exist'})

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

@app.route('/address_register', methods=['GET'])
def address_register():

    #Gather GET parameters
    stato = request.args.get('stato')
    provincia = request.args.get('provincia')
    comune = request.args.get('comune')
    cap = request.args.get('cap')
    indirizzo = request.args.get('indirizzo')
    idAzienda = request.args.get('idAzienda')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if idAzienda exists
    cursor.execute('SELECT * FROM aziende WHERE idAzienda = %s', (int(idAzienda)))
    agency = cursor.fetchone()
    if agency is None:
        return jsonify({'outcome': 'error, specified agency does not exist'})
    
    # Insert the address
    cursor.execute('INSERT INTO indirizzi (stato, provincia, comune, cap, indirizzo, idAzienda) VALUES (%s, %s, %s, %s, %s, %s)', 
                   (stato, provincia, comune, cap, indirizzo, idAzienda))
    return jsonify({'outcome': 'address successfully created'})

@app.route('/contact_register', methods=['GET'])
def contact_register():

    # Gather GET parameters
    nome = request.args.get('nome')
    cognome = request.args.get('cognome')
    telefono = request.args.get('telefono')
    email = request.args.get('email')
    ruolo = request.args.get('ruolo')
    idAzienda = request.args.get('idAzienda')

    # Create new cursor
    cursor = conn.cursor(dictionary=True)

    # Check if idAzienda exists
    cursor.execute('SELECT * FROM aziende WHERE idAzienda = %s', (int(idAzienda)))
    agency = cursor.fetchone()
    if agency is None:
        return jsonify({'outcome': 'error, specified agency does not exist'})
    
    # Insert the contact
    cursor.execute('INSERT INTO contatti (nome, cognome, telefono, email, ruolo, idAzienda) VALUES (%s, %s, %s, %s, %s, %s)', 
                   (nome, cognome, telefono, email, ruolo, idAzienda))

def close_api(signal, frame):  # Parameters are necessary even if not used because it has to match the signal signature
    conn.close()
    exit(0)  # Close the API

signal.signal(signal.SIGINT, close_api)  # Bind CTRL+C to close_api function

if __name__ == '__main__':
    app.run(host='172.16.1.98', port=12345, debug=True)  # Bind to the specific IP address