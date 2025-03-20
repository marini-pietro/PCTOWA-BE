# Webapp-PCTO API

Questo progetto è un'API RESTful basata su Flask per la gestione di dati relativi a una piattaforma di collaborazione scuola-azienda.  
L'API fornisce endpoint per gestire utenti, classi, studenti, aziende, tutor, indirizzi, settori, materie e turni di lavoro.

## Funzionalità

- **Gestione Utenti**: Registrazione, aggiornamento, eliminazione e autenticazione degli utenti.
- **Gestione Classi**: Creazione, aggiornamento ed eliminazione delle classi.
- **Gestione Studenti**: Registrazione, aggiornamento ed eliminazione degli studenti.
- **Gestione Aziende**: Registrazione, aggiornamento ed eliminazione delle aziende.
- **Gestione Tutor**: Registrazione, aggiornamento ed eliminazione dei tutor.
- **Gestione Indirizzi**: Registrazione, aggiornamento ed eliminazione degli indirizzi.
- **Gestione Settori**: Registrazione, aggiornamento ed eliminazione dei settori.
- **Gestione Materie**: Registrazione, aggiornamento ed eliminazione delle materie.
- **Gestione Turni di Lavoro**: Registrazione, aggiornamento ed eliminazione dei turni.

## Prerequisiti

- Python 3.x.x (sviluppato con 3.11.4)
- Database MySQL/MariaDB
- Flask e dipendenze richieste (vedi `requirements.txt`)

## Installazione

1. Clona il repository:
   ```
   git clone https://github.com/your-username/Webapp-PCTO.git
   cd Webapp-PCTO
   ```

2. Installa le dipendenze:
    ```
    pip install -r requirements.txt
    ```

3. Configura la connessione al database in `api.py`:
    ```
    conn = mysql.connector.connect(
    host='localhost',
    user='tuo-username',
    password='tua-password',
    database='tuo-database'
    )
    ```

4. Configura le impostazioni dell' api:
    ```
    app.run(host='tuo-host', 
            port='tua-porta-come-intero', 
            ssl_context=('tuo-file cert.pem', 'tuo-file key.pem'),
            debug='false per produzione, True per facilitare lo sviluppo')
    ```

# Utilizzo

```
    python3 api.py
```

# Licenza

Questo progetto è inteso per essere utilizzato nei confini della scuola G. Marconi ITIS di Verona, la sua riproduzione, commerciale o non, è severamente vietata senza previo permesso dai rispettivi referenti/responsabili all'interno della scuola G.Marconi ITIS situata a Verona.  
La modifica o l'implementazione di nuove funzionalità, se necessarie, sarà diretta dai rispettivi referenti/responsabili all'interno della scuola G. Marconi.

# Crediti

Realizzato nell' anno scolastico 2024-2025 dal gruppo Marini, Peretti, Rigo della 5BI, come progetto intermateria, con i seguenti ruoli:

- Marini: Backend/API Developer e DBA
- Rigo: Frontend developer e project analyst
- Peretti: Frontend developer e project analyst