-- phpMyAdmin SQL Dump
-- version 5.1.0
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Creato il: Mag 02, 2025 alle 20:40
-- Versione del server: 8.0.27
-- Versione PHP: 7.3.31-1~deb10u7

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `pctowa`
--

-- --------------------------------------------------------

--
-- Struttura della tabella `aziende`
--

CREATE TABLE `aziende` (
  `id_azienda` int NOT NULL,
  `ragione_sociale` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `codice_ateco` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `partita_iva` char(11) COLLATE utf8_unicode_ci NOT NULL,
  `fax` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `pec` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `telefono_azienda` varchar(13) COLLATE utf8_unicode_ci NOT NULL COMMENT 'con prefisso',
  `email_azienda` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `data_convenzione` date DEFAULT NULL,
  `scadenza_convenzione` date DEFAULT NULL,
  `categoria` varchar(25) COLLATE utf8_unicode_ci NOT NULL,
  `indirizzo_logo` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `sito_web` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `forma_giuridica` varchar(25) COLLATE utf8_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `aziende`
--

INSERT INTO `aziende` (`id_azienda`, `ragione_sociale`, `codice_ateco`, `partita_iva`, `fax`, `pec`, `telefono_azienda`, `email_azienda`, `data_convenzione`, `scadenza_convenzione`, `categoria`, `indirizzo_logo`, `sito_web`, `forma_giuridica`) VALUES
(1, 'Tech Solutions', '6201', '12345678901', '0123456789', 'tech@pec.it', '1234567890', 'info@techsolutions.it', '2023-01-01', '2026-01-01', 'Tecnologia', 'logo1.png', 'https://techsolutions.it', 'S.r.l.'),
(2, 'GreenFuture', '0112', '98765432109', '0234567890', 'green@pec.it', '0987654321', 'info@greenfuture.it', '2022-09-01', '2025-09-01', 'Energia', 'logo2.png', 'https://greenfuture.it', 'S.p.A.'),
(3, 'EduInnovazione', '8542', '19283746501', '0345678912', 'edu@pec.it', '1122334455', 'info@eduinnovazione.it', '2024-01-10', '2027-01-10', 'Formazione', 'logo3.png', 'https://eduinnovazione.it', 'Cooperativa');

-- --------------------------------------------------------

--
-- Struttura della tabella `classi`
--

CREATE TABLE `classi` (
  `id_classe` int NOT NULL,
  `sigla` char(3) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL COMMENT 'sigla della classe (e.g. 5BI)',
  `email_responsabile` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `anno` char(5) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL COMMENT 'anno scolastico (e.g. 24-25)'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dump dei dati per la tabella `classi`
--

INSERT INTO `classi` (`id_classe`, `sigla`, `email_responsabile`, `anno`) VALUES
(1, '4AI', 'lorenzo.decarli@marconiverona.edu.it', '24-25'),
(2, '4BI', 'lorenzo.decarli@marconiverona.edu.it', '24-25'),
(3, '4CI', 'lorenzo.decarli@marconiverona.edu.it', '24-25');

-- --------------------------------------------------------

--
-- Struttura della tabella `contatti`
--

CREATE TABLE `contatti` (
  `id_contatto` int NOT NULL,
  `nome` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `cognome` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `telefono` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `email` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `ruolo` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `id_azienda` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `contatti`
--

INSERT INTO `contatti` (`id_contatto`, `nome`, `cognome`, `telefono`, `email`, `ruolo`, `id_azienda`) VALUES
(1, 'Mario', 'Rossi', '3216549870', 'm.rossi@techsolutions.it', 'HR', 1),
(2, 'Lucia', 'Neri', '3311122233', 'l.neri@greenfuture.it', 'Referente', 2),
(3, 'Paolo', 'Bianchi', '3667788990', 'p.bianchi@eduinnovazione.it', 'Tutor Aziendale', 3);

-- --------------------------------------------------------

--
-- Struttura della tabella `docente_referente`
--

CREATE TABLE `docente_referente` (
  `email_docente` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `anno` char(4) COLLATE utf8_unicode_ci NOT NULL,
  `id_azienda` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `docente_referente`
--

INSERT INTO `docente_referente` (`email_docente`, `anno`, `id_azienda`) VALUES
('cinzia.decarli@marconiverona.edu.it', '2025', 3),
('irene.decarli@marconiverona.edu.it', '2025', 2),
('lorenzo.decarli@marconiverona.edu.it', '2025', 1);

-- --------------------------------------------------------

--
-- Struttura della tabella `forma_giuridica`
--

CREATE TABLE `forma_giuridica` (
  `forma` varchar(25) COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `forma_giuridica`
--

INSERT INTO `forma_giuridica` (`forma`) VALUES
('Cooperativa'),
('S.p.A.'),
('S.r.l.');

-- --------------------------------------------------------

--
-- Struttura della tabella `indirizzi`
--

CREATE TABLE `indirizzi` (
  `id_indirizzo` int NOT NULL,
  `stato` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `provincia` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `comune` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `cap` char(5) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `indirizzo` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `id_azienda` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dump dei dati per la tabella `indirizzi`
--

INSERT INTO `indirizzi` (`id_indirizzo`, `stato`, `provincia`, `comune`, `cap`, `indirizzo`, `id_azienda`) VALUES
(1, 'Italia', 'VR', 'Verona', '20100', 'Via Roma 10', 1),
(2, 'Italia', 'VR', 'Verona', '10100', 'Via Andrea d’Angeli', 2),
(3, 'Italia', 'VR', 'Verona', '50100', 'Via Verdi 7', 3);

-- --------------------------------------------------------

--
-- Struttura della tabella `materie`
--

CREATE TABLE `materie` (
  `materia` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `descrizione` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `hex_color` char(7) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL COMMENT 'colore della tag nel frontend, obbligatorio esprimerlo con 7 caratteri'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dump dei dati per la tabella `materie`
--

INSERT INTO `materie` (`materia`, `descrizione`, `hex_color`) VALUES
('Android app', 'Sistemi e Reti', '#ffcc00'),
('Programmazione web', 'Programmazione web', '#00ccff'),
('Sistemista', 'Sistemista', '#cc00ff');

-- --------------------------------------------------------

--
-- Struttura della tabella `settori`
--

CREATE TABLE `settori` (
  `settore` varchar(255) COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `settori`
--

INSERT INTO `settori` (`settore`) VALUES
('Aereonautica'),
('Costruzione del mezzo'),
('Elettronica'),
('Informatica'),
('Logistica'),
('Telecomunicazioni');

-- --------------------------------------------------------

--
-- Struttura della tabella `studente_turno`
--

CREATE TABLE `studente_turno` (
  `matricola` int NOT NULL,
  `id_turno` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `studente_turno`
--

INSERT INTO `studente_turno` (`matricola`, `id_turno`) VALUES
(10001, 1),
(10002, 2),
(10003, 3);

-- --------------------------------------------------------

--
-- Struttura della tabella `studenti`
--

CREATE TABLE `studenti` (
  `matricola` int NOT NULL,
  `nome` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `cognome` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `id_classe` int NOT NULL,
  `comune` varchar(255) COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `studenti`
--

INSERT INTO `studenti` (`matricola`, `nome`, `cognome`, `id_classe`, `comune`) VALUES
(10001, 'Marco', 'Neri', 1, '37131'),
(10002, 'Giulia', 'Bianchi', 2, '37132'),
(10003, 'Luca', 'Verdi', 3, '37133');

-- --------------------------------------------------------

--
-- Struttura della tabella `turni`
--

CREATE TABLE `turni` (
  `id_turno` int NOT NULL,
  `data_inizio` date DEFAULT NULL,
  `data_fine` date DEFAULT NULL,
  `posti` int DEFAULT NULL,
  `posti_occupati` int DEFAULT '0',
  `ore` int DEFAULT NULL,
  `id_azienda` int NOT NULL,
  `id_indirizzo` int DEFAULT NULL,
  `ora_inizio` varchar(5) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `ora_fine` varchar(5) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `giorno_inizio` enum('lunedì','martedì','mercoledì','giovedì','venerdì') CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `giorno_fine` enum('lunedì','martedì','mercoledì','giovedì','venerdì') CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dump dei dati per la tabella `turni`
--

INSERT INTO `turni` (`id_turno`, `data_inizio`, `data_fine`, `posti`, `posti_occupati`, `ore`, `id_azienda`, `id_indirizzo`, `ora_inizio`, `ora_fine`, `giorno_inizio`, `giorno_fine`) VALUES
(1, '2024-03-01', '2024-05-31', 2, 2, 120, 1, 1, '09:00', '13:00', 'lunedì', 'venerdì'),
(2, '2024-04-01', '2024-06-30', 3, 1, 100, 2, 2, '10:00', '14:00', 'martedì', 'giovedì'),
(3, '2024-05-15', '2024-07-31', 1, 1, 80, 3, 3, '08:30', '12:00', 'mercoledì', 'venerdì');

-- --------------------------------------------------------

--
-- Struttura della tabella `turno_materia`
--

CREATE TABLE `turno_materia` (
  `materia` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `id_turno` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `turno_materia`
--

INSERT INTO `turno_materia` (`materia`, `id_turno`) VALUES
('Sistemista', 1),
('Sistemista', 2),
('Android App', 3);

-- --------------------------------------------------------

--
-- Struttura della tabella `turno_settore`
--

CREATE TABLE `turno_settore` (
  `settore` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `id_turno` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `turno_settore`
--

INSERT INTO `turno_settore` (`settore`, `id_turno`) VALUES
('Informatica', 1),
('Elettronica', 3);

-- --------------------------------------------------------

--
-- Struttura della tabella `turno_tutor`
--

CREATE TABLE `turno_tutor` (
  `id_tutor` int NOT NULL,
  `id_turno` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `tutor`
--

CREATE TABLE `tutor` (
  `id_tutor` int NOT NULL,
  `nome` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `cognome` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `email_tutor` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `telefono_tutor` varchar(13) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dump dei dati per la tabella `tutor`
--

INSERT INTO `tutor` (`id_tutor`, `nome`, `cognome`, `email_tutor`, `telefono_tutor`) VALUES
(1, 'Andrea', 'Gialli', 'a.gialli@techsolutions.it', '3456789012'),
(2, 'Chiara', 'Blu', 'c.blu@greenfuture.it', '3344556677'),
(3, 'Elena', 'Rosa', 'e.rosa@eduinnovazione.it', '3399988776');

-- --------------------------------------------------------

--
-- Struttura della tabella `utenti`
--

CREATE TABLE `utenti` (
  `email_utente` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `password` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `nome` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `cognome` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `ruolo` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dump dei dati per la tabella `utenti`
--

INSERT INTO `utenti` (`email_utente`, `password`, `nome`, `cognome`, `ruolo`) VALUES
('cinzia.decarli@marconiverona.edu.it', 'hashed_pwd3', 'Giorgio', 'Rosa', 3),
('irene.decarli@marconiverona.edu.it', 'hashed_pwd2', 'Anna', 'Verdi', 2),
('lorenzo.decarli@marconiverona.edu.it', 'hashed_pwd1', 'Luca', 'Bianchi', 1);

--
-- Indici per le tabelle scaricate
--

--
-- Indici per le tabelle `aziende`
--
ALTER TABLE `aziende`
  ADD PRIMARY KEY (`id_azienda`),
  ADD UNIQUE KEY `partitaIVA` (`partita_iva`),
  ADD KEY `fk_formaGiuridica` (`forma_giuridica`);

--
-- Indici per le tabelle `classi`
--
ALTER TABLE `classi`
  ADD PRIMARY KEY (`id_classe`),
  ADD KEY `classi_ibfk_1` (`email_responsabile`);

--
-- Indici per le tabelle `contatti`
--
ALTER TABLE `contatti`
  ADD PRIMARY KEY (`id_contatto`),
  ADD KEY `contatti_ibfk_1` (`id_azienda`);

--
-- Indici per le tabelle `docente_referente`
--
ALTER TABLE `docente_referente`
  ADD PRIMARY KEY (`email_docente`,`id_azienda`),
  ADD KEY `docenteReferente_ibfk_2` (`id_azienda`);

--
-- Indici per le tabelle `forma_giuridica`
--
ALTER TABLE `forma_giuridica`
  ADD PRIMARY KEY (`forma`);

--
-- Indici per le tabelle `indirizzi`
--
ALTER TABLE `indirizzi`
  ADD PRIMARY KEY (`id_indirizzo`),
  ADD KEY `indirizzi_ibfk_1` (`id_azienda`);

--
-- Indici per le tabelle `materie`
--
ALTER TABLE `materie`
  ADD PRIMARY KEY (`materia`);

--
-- Indici per le tabelle `settori`
--
ALTER TABLE `settori`
  ADD PRIMARY KEY (`settore`);

--
-- Indici per le tabelle `studente_turno`
--
ALTER TABLE `studente_turno`
  ADD PRIMARY KEY (`matricola`,`id_turno`),
  ADD KEY `studenteTurno_ibfk_2` (`id_turno`);

--
-- Indici per le tabelle `studenti`
--
ALTER TABLE `studenti`
  ADD PRIMARY KEY (`matricola`),
  ADD KEY `studenti_ibfk_1` (`id_classe`);

--
-- Indici per le tabelle `turni`
--
ALTER TABLE `turni`
  ADD PRIMARY KEY (`id_turno`),
  ADD KEY `turni_ibfk_1` (`id_azienda`),
  ADD KEY `turni_ibfk_3` (`id_indirizzo`);

--
-- Indici per le tabelle `turno_materia`
--
ALTER TABLE `turno_materia`
  ADD PRIMARY KEY (`materia`,`id_turno`),
  ADD KEY `turnoMateria_ibfk_2` (`id_turno`);

--
-- Indici per le tabelle `turno_settore`
--
ALTER TABLE `turno_settore`
  ADD PRIMARY KEY (`settore`,`id_turno`),
  ADD KEY `turnoSettore_ibfk_2` (`id_turno`);

--
-- Indici per le tabelle `turno_tutor`
--
ALTER TABLE `turno_tutor`
  ADD PRIMARY KEY (`id_tutor`,`id_turno`),
  ADD KEY `idTurno` (`id_turno`);

--
-- Indici per le tabelle `tutor`
--
ALTER TABLE `tutor`
  ADD PRIMARY KEY (`id_tutor`);

--
-- Indici per le tabelle `utenti`
--
ALTER TABLE `utenti`
  ADD PRIMARY KEY (`email_utente`);

--
-- AUTO_INCREMENT per le tabelle scaricate
--

--
-- AUTO_INCREMENT per la tabella `aziende`
--
ALTER TABLE `aziende`
  MODIFY `id_azienda` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT per la tabella `classi`
--
ALTER TABLE `classi`
  MODIFY `id_classe` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT per la tabella `contatti`
--
ALTER TABLE `contatti`
  MODIFY `id_contatto` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT per la tabella `indirizzi`
--
ALTER TABLE `indirizzi`
  MODIFY `id_indirizzo` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT per la tabella `turni`
--
ALTER TABLE `turni`
  MODIFY `id_turno` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT per la tabella `tutor`
--
ALTER TABLE `tutor`
  MODIFY `id_tutor` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Limiti per le tabelle scaricate
--

--
-- Limiti per la tabella `aziende`
--
ALTER TABLE `aziende`
  ADD CONSTRAINT `aziende_ibfk_1` FOREIGN KEY (`forma_giuridica`) REFERENCES `forma_giuridica` (`forma`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_formaGiuridica` FOREIGN KEY (`forma_giuridica`) REFERENCES `forma_giuridica` (`forma`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `classi`
--
ALTER TABLE `classi`
  ADD CONSTRAINT `classi_ibfk_1` FOREIGN KEY (`email_responsabile`) REFERENCES `utenti` (`email_utente`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `contatti`
--
ALTER TABLE `contatti`
  ADD CONSTRAINT `contatti_ibfk_1` FOREIGN KEY (`id_azienda`) REFERENCES `aziende` (`id_azienda`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `docente_referente`
--
ALTER TABLE `docente_referente`
  ADD CONSTRAINT `docenteReferente_ibfk_1` FOREIGN KEY (`email_docente`) REFERENCES `utenti` (`email_utente`) ON UPDATE CASCADE,
  ADD CONSTRAINT `docenteReferente_ibfk_2` FOREIGN KEY (`id_azienda`) REFERENCES `aziende` (`id_azienda`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `indirizzi`
--
ALTER TABLE `indirizzi`
  ADD CONSTRAINT `indirizzi_ibfk_1` FOREIGN KEY (`id_azienda`) REFERENCES `aziende` (`id_azienda`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `studente_turno`
--
ALTER TABLE `studente_turno`
  ADD CONSTRAINT `studenteTurno_ibfk_1` FOREIGN KEY (`matricola`) REFERENCES `studenti` (`matricola`) ON UPDATE CASCADE,
  ADD CONSTRAINT `studenteTurno_ibfk_2` FOREIGN KEY (`id_turno`) REFERENCES `turni` (`id_turno`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `studenti`
--
ALTER TABLE `studenti`
  ADD CONSTRAINT `studenti_ibfk_1` FOREIGN KEY (`id_classe`) REFERENCES `classi` (`id_classe`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `turni`
--
ALTER TABLE `turni`
  ADD CONSTRAINT `fk_azienda` FOREIGN KEY (`id_azienda`) REFERENCES `aziende` (`id_azienda`) ON UPDATE CASCADE,
  ADD CONSTRAINT `turni_ibfk_1` FOREIGN KEY (`id_azienda`) REFERENCES `aziende` (`id_azienda`) ON UPDATE CASCADE,
  ADD CONSTRAINT `turni_ibfk_3` FOREIGN KEY (`id_indirizzo`) REFERENCES `indirizzi` (`id_indirizzo`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `turno_materia`
--
ALTER TABLE `turno_materia`
  ADD CONSTRAINT `fk_materia` FOREIGN KEY (`materia`) REFERENCES `materie` (`materia`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_turno_cascade` FOREIGN KEY (`id_turno`) REFERENCES `turni` (`id_turno`) ON UPDATE CASCADE,
  ADD CONSTRAINT `turnoMateria_ibfk_1` FOREIGN KEY (`materia`) REFERENCES `materie` (`materia`) ON UPDATE CASCADE,
  ADD CONSTRAINT `turnoMateria_ibfk_2` FOREIGN KEY (`id_turno`) REFERENCES `turni` (`id_turno`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `turno_settore`
--
ALTER TABLE `turno_settore`
  ADD CONSTRAINT `fk_settore` FOREIGN KEY (`settore`) REFERENCES `settori` (`settore`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_turno` FOREIGN KEY (`id_turno`) REFERENCES `turni` (`id_turno`) ON UPDATE CASCADE,
  ADD CONSTRAINT `turnoSettore_ibfk_1` FOREIGN KEY (`settore`) REFERENCES `settori` (`settore`) ON UPDATE CASCADE,
  ADD CONSTRAINT `turnoSettore_ibfk_2` FOREIGN KEY (`id_turno`) REFERENCES `turni` (`id_turno`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `turno_tutor`
--
ALTER TABLE `turno_tutor`
  ADD CONSTRAINT `turnoTutor_ibfk_1` FOREIGN KEY (`id_tutor`) REFERENCES `tutor` (`id_tutor`),
  ADD CONSTRAINT `turnoTutor_ibfk_2` FOREIGN KEY (`id_turno`) REFERENCES `turni` (`id_turno`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
