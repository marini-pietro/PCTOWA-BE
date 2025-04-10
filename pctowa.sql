-- phpMyAdmin SQL Dump
-- version 5.1.0
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Creato il: Apr 10, 2025 alle 12:49
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
  `idAzienda` int NOT NULL,
  `ragioneSociale` varchar(50) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `codiceAteco` varchar(10) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `partitaIVA` char(11) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `fax` varchar(50) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `pec` varchar(50) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `telefonoAzienda` varchar(13) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL COMMENT 'con prefisso',
  `emailAzienda` varchar(50) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `dataConvenzione` date DEFAULT NULL,
  `scadenzaConvenzione` date DEFAULT NULL,
  `categoria` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `indirizzoLogo` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `sitoWeb` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `formaGiuridica` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `aziende`
--

INSERT INTO `aziende` (`idAzienda`, `ragioneSociale`, `codiceAteco`, `partitaIVA`, `fax`, `pec`, `telefonoAzienda`, `emailAzienda`, `dataConvenzione`, `scadenzaConvenzione`, `categoria`, `indirizzoLogo`, `sitoWeb`, `formaGiuridica`) VALUES
(1, 'Tech Solutions', '6201', '12345678901', '0123456789', 'tech@pec.it', '1234567890', 'info@techsolutions.it', '2023-01-01', '2026-01-01', 'Tecnologia', 'logo1.png', 'https://techsolutions.it', 'S.r.l.'),
(2, 'GreenFuture S.p.A.', '0112', '98765432109', '0234567890', 'green@pec.it', '0987654321', 'info@greenfuture.it', '2022-09-01', '2025-09-01', 'Energia', 'logo2.png', 'https://greenfuture.it', 'S.p.A.'),
(3, 'EduInnovazione', '8542', '19283746501', '0345678912', 'edu@pec.it', '1122334455', 'info@eduinnovazione.it', '2024-01-10', '2027-01-10', 'Formazione', 'logo3.png', 'https://eduinnovazione.it', 'Cooperativa');

-- --------------------------------------------------------

--
-- Struttura della tabella `classi`
--

CREATE TABLE `classi` (
  `idClasse` int NOT NULL,
  `classe` char(3) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL COMMENT 'sigla della classe (e.g. 5BI)',
  `emailResponsabile` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `anno` char(5) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL COMMENT 'anno scolastico (e.g. 24-25)'
) ;

--
-- Dump dei dati per la tabella `classi`
--

INSERT INTO `classi` (`idClasse`, `classe`, `emailResponsabile`, `anno`) VALUES
(1, '4AI', 'lorenzo.decarli@marconiverona.edu.it', '24-25'),
(2, '4BI', 'lorenzo.decarli@marconiverona.edu.it', '24-25'),
(3, '4CI', 'lorenzo.decarli@marconiverona.edu.it', '24-25');

-- --------------------------------------------------------

--
-- Struttura della tabella `contatti`
--

CREATE TABLE `contatti` (
  `idContatto` int NOT NULL,
  `nome` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `cognome` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `telefono` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `email` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `ruolo` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `idAzienda` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `contatti`
--

INSERT INTO `contatti` (`idContatto`, `nome`, `cognome`, `telefono`, `email`, `ruolo`, `idAzienda`) VALUES
(1, 'Mario', 'Rossi', '3216549870', 'm.rossi@techsolutions.it', 'HR', 1),
(2, 'Lucia', 'Neri', '3311122233', 'l.neri@greenfuture.it', 'Referente', 2),
(3, 'Paolo', 'Bianchi', '3667788990', 'p.bianchi@eduinnovazione.it', 'Tutor Aziendale', 3);

-- --------------------------------------------------------

--
-- Struttura della tabella `docenteReferente`
--

CREATE TABLE `docenteReferente` (
  `emailDocente` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `anno` char(4) COLLATE utf8_unicode_ci NOT NULL,
  `idAzienda` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `docenteReferente`
--

INSERT INTO `docenteReferente` (`emailDocente`, `anno`, `idAzienda`) VALUES
('cinzia.decarli@marconiverona.edu.it', '2025', 3),
('irene.decarli@marconiverona.edu.it', '2025', 2),
('lorenzo.decarli@marconiverona.edu.it', '2025', 1);

-- --------------------------------------------------------

--
-- Struttura della tabella `formaGiuridica`
--

CREATE TABLE `formaGiuridica` (
  `forma` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `formaGiuridica`
--

INSERT INTO `formaGiuridica` (`forma`) VALUES
('Cooperativa'),
('S.p.A.'),
('S.r.l.');

-- --------------------------------------------------------

--
-- Struttura della tabella `indirizzi`
--

CREATE TABLE `indirizzi` (
  `idIndirizzo` int NOT NULL,
  `stato` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `provincia` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `comune` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `cap` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `indirizzo` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `idAzienda` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `indirizzi`
--

INSERT INTO `indirizzi` (`idIndirizzo`, `stato`, `provincia`, `comune`, `cap`, `indirizzo`, `idAzienda`) VALUES
(1, 'Italia', 'VR', 'Verona', '20100', 'Via Roma 10', 1),
(2, 'Italia', 'VR', 'Verona', '10100', 'Via Andrea d’Angeli', 2),
(3, 'Italia', 'VR', 'Verona', '50100', 'Via Verdi 7', 3);

-- --------------------------------------------------------

--
-- Struttura della tabella `materie`
--

CREATE TABLE `materie` (
  `materia` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `descrizione` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `hexColor` char(7) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL COMMENT 'colore della tag nel frontend, obbligatorio esprimerlo con 7 caratteri'
) ;

--
-- Dump dei dati per la tabella `materie`
--

INSERT INTO `materie` (`materia`, `descrizione`, `hexColor`) VALUES
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
-- Struttura della tabella `studenteTurno`
--

CREATE TABLE `studenteTurno` (
  `matricola` int NOT NULL,
  `idTurno` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `studenteTurno`
--

INSERT INTO `studenteTurno` (`matricola`, `idTurno`) VALUES
(10001, 1),
(10002, 2),
(10003, 3);

-- --------------------------------------------------------

--
-- Struttura della tabella `studenti`
--

CREATE TABLE `studenti` (
  `matricola` int NOT NULL,
  `nome` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `cognome` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `idClasse` int NOT NULL,
  `comune` varchar(255) COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `studenti`
--

INSERT INTO `studenti` (`matricola`, `nome`, `cognome`, `idClasse`, `comune`) VALUES
(10001, 'Marco', 'Neri', 1, '37131'),
(10002, 'Giulia', 'Bianchi', 2, '37132'),
(10003, 'Luca', 'Verdi', 3, '37133');

-- --------------------------------------------------------

--
-- Struttura della tabella `turni`
--

CREATE TABLE `turni` (
  `idTurno` int NOT NULL,
  `dataInizio` date DEFAULT NULL,
  `dataFine` date DEFAULT NULL,
  `posti` int DEFAULT NULL,
  `postiOccupati` int DEFAULT '0',
  `ore` int DEFAULT NULL,
  `idAzienda` int NOT NULL,
  `idTutor` int DEFAULT NULL,
  `idIndirizzo` int DEFAULT NULL,
  `oraInizio` varchar(5) COLLATE utf8_unicode_ci NOT NULL,
  `oraFine` varchar(5) COLLATE utf8_unicode_ci NOT NULL,
  `giornoInizio` enum('lunedì','martedì','mercoledì','giovedì','venerdì') COLLATE utf8_unicode_ci DEFAULT NULL,
  `giornoFine` enum('lunedì','martedì','mercoledì','giovedì','venerdì') COLLATE utf8_unicode_ci DEFAULT NULL
) ;

--
-- Dump dei dati per la tabella `turni`
--

INSERT INTO `turni` (`idTurno`, `dataInizio`, `dataFine`, `posti`, `postiOccupati`, `ore`, `idAzienda`, `idTutor`, `idIndirizzo`, `oraInizio`, `oraFine`, `giornoInizio`, `giornoFine`) VALUES
(1, '2024-03-01', '2024-05-31', 2, 2, 120, 1, 1, 1, '09:00', '13:00', 'lunedì', 'venerdì'),
(2, '2024-04-01', '2024-06-30', 3, 1, 100, 2, 2, 2, '10:00', '14:00', 'martedì', 'giovedì'),
(3, '2024-05-15', '2024-07-31', 1, 1, 80, 3, 3, 3, '08:30', '12:00', 'mercoledì', 'venerdì');

-- --------------------------------------------------------

--
-- Struttura della tabella `turnoMateria`
--

CREATE TABLE `turnoMateria` (
  `materia` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `idTurno` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `turnoMateria`
--

INSERT INTO `turnoMateria` (`materia`, `idTurno`) VALUES
('Sistemista', 1),
('Sistemista', 2),
('Android App', 3);

-- --------------------------------------------------------

--
-- Struttura della tabella `turnoSettore`
--

CREATE TABLE `turnoSettore` (
  `settore` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `idTurno` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

--
-- Dump dei dati per la tabella `turnoSettore`
--

INSERT INTO `turnoSettore` (`settore`, `idTurno`) VALUES
('Informatica', 1),
('Elettronica', 3);

-- --------------------------------------------------------

--
-- Struttura della tabella `tutor`
--

CREATE TABLE `tutor` (
  `idTutor` int NOT NULL,
  `nome` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `cognome` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `emailTutor` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `telefonoTutor` varchar(13) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL
) ;

--
-- Dump dei dati per la tabella `tutor`
--

INSERT INTO `tutor` (`idTutor`, `nome`, `cognome`, `emailTutor`, `telefonoTutor`) VALUES
(1, 'Andrea', 'Gialli', 'a.gialli@techsolutions.it', '3456789012'),
(2, 'Chiara', 'Blu', 'c.blu@greenfuture.it', '3344556677'),
(3, 'Elena', 'Rosa', 'e.rosa@eduinnovazione.it', '3399988776');

-- --------------------------------------------------------

--
-- Struttura della tabella `utenti`
--

CREATE TABLE `utenti` (
  `emailUtente` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `password` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `nome` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `cognome` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `ruolo` int NOT NULL
) ;

--
-- Dump dei dati per la tabella `utenti`
--

INSERT INTO `utenti` (`emailUtente`, `password`, `nome`, `cognome`, `ruolo`) VALUES
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
  ADD PRIMARY KEY (`idAzienda`),
  ADD UNIQUE KEY `partitaIVA` (`partitaIVA`),
  ADD KEY `fk_formaGiuridica` (`formaGiuridica`);

--
-- Indici per le tabelle `classi`
--
ALTER TABLE `classi`
  ADD PRIMARY KEY (`idClasse`),
  ADD KEY `classi_ibfk_1` (`emailResponsabile`);

--
-- Indici per le tabelle `contatti`
--
ALTER TABLE `contatti`
  ADD PRIMARY KEY (`idContatto`),
  ADD KEY `contatti_ibfk_1` (`idAzienda`);

--
-- Indici per le tabelle `docenteReferente`
--
ALTER TABLE `docenteReferente`
  ADD PRIMARY KEY (`emailDocente`,`idAzienda`),
  ADD KEY `docenteReferente_ibfk_2` (`idAzienda`);

--
-- Indici per le tabelle `formaGiuridica`
--
ALTER TABLE `formaGiuridica`
  ADD PRIMARY KEY (`forma`);

--
-- Indici per le tabelle `indirizzi`
--
ALTER TABLE `indirizzi`
  ADD PRIMARY KEY (`idIndirizzo`),
  ADD KEY `indirizzi_ibfk_1` (`idAzienda`);

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
-- Indici per le tabelle `studenteTurno`
--
ALTER TABLE `studenteTurno`
  ADD PRIMARY KEY (`matricola`,`idTurno`),
  ADD KEY `studenteTurno_ibfk_2` (`idTurno`);

--
-- Indici per le tabelle `studenti`
--
ALTER TABLE `studenti`
  ADD PRIMARY KEY (`matricola`),
  ADD KEY `studenti_ibfk_1` (`idClasse`);

--
-- Indici per le tabelle `turni`
--
ALTER TABLE `turni`
  ADD PRIMARY KEY (`idTurno`),
  ADD KEY `turni_ibfk_1` (`idAzienda`),
  ADD KEY `turni_ibfk_2` (`idTutor`),
  ADD KEY `turni_ibfk_3` (`idIndirizzo`);

--
-- Indici per le tabelle `turnoMateria`
--
ALTER TABLE `turnoMateria`
  ADD PRIMARY KEY (`materia`,`idTurno`),
  ADD KEY `turnoMateria_ibfk_2` (`idTurno`);

--
-- Indici per le tabelle `turnoSettore`
--
ALTER TABLE `turnoSettore`
  ADD PRIMARY KEY (`settore`,`idTurno`),
  ADD KEY `turnoSettore_ibfk_2` (`idTurno`);

--
-- Indici per le tabelle `tutor`
--
ALTER TABLE `tutor`
  ADD PRIMARY KEY (`idTutor`);

--
-- Indici per le tabelle `utenti`
--
ALTER TABLE `utenti`
  ADD PRIMARY KEY (`emailUtente`);

--
-- AUTO_INCREMENT per le tabelle scaricate
--

--
-- AUTO_INCREMENT per la tabella `aziende`
--
ALTER TABLE `aziende`
  MODIFY `idAzienda` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT per la tabella `classi`
--
ALTER TABLE `classi`
  MODIFY `idClasse` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la tabella `contatti`
--
ALTER TABLE `contatti`
  MODIFY `idContatto` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT per la tabella `indirizzi`
--
ALTER TABLE `indirizzi`
  MODIFY `idIndirizzo` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT per la tabella `turni`
--
ALTER TABLE `turni`
  MODIFY `idTurno` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la tabella `tutor`
--
ALTER TABLE `tutor`
  MODIFY `idTutor` int NOT NULL AUTO_INCREMENT;

--
-- Limiti per le tabelle scaricate
--

--
-- Limiti per la tabella `aziende`
--
ALTER TABLE `aziende`
  ADD CONSTRAINT `aziende_ibfk_1` FOREIGN KEY (`formaGiuridica`) REFERENCES `formaGiuridica` (`forma`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_formaGiuridica` FOREIGN KEY (`formaGiuridica`) REFERENCES `formaGiuridica` (`forma`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `classi`
--
ALTER TABLE `classi`
  ADD CONSTRAINT `classi_ibfk_1` FOREIGN KEY (`emailResponsabile`) REFERENCES `utenti` (`emailUtente`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `contatti`
--
ALTER TABLE `contatti`
  ADD CONSTRAINT `contatti_ibfk_1` FOREIGN KEY (`idAzienda`) REFERENCES `aziende` (`idAzienda`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `docenteReferente`
--
ALTER TABLE `docenteReferente`
  ADD CONSTRAINT `docenteReferente_ibfk_1` FOREIGN KEY (`emailDocente`) REFERENCES `utenti` (`emailUtente`) ON UPDATE CASCADE,
  ADD CONSTRAINT `docenteReferente_ibfk_2` FOREIGN KEY (`idAzienda`) REFERENCES `aziende` (`idAzienda`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `indirizzi`
--
ALTER TABLE `indirizzi`
  ADD CONSTRAINT `indirizzi_ibfk_1` FOREIGN KEY (`idAzienda`) REFERENCES `aziende` (`idAzienda`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `studenteTurno`
--
ALTER TABLE `studenteTurno`
  ADD CONSTRAINT `studenteTurno_ibfk_1` FOREIGN KEY (`matricola`) REFERENCES `studenti` (`matricola`) ON UPDATE CASCADE,
  ADD CONSTRAINT `studenteTurno_ibfk_2` FOREIGN KEY (`idTurno`) REFERENCES `turni` (`idTurno`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `studenti`
--
ALTER TABLE `studenti`
  ADD CONSTRAINT `studenti_ibfk_1` FOREIGN KEY (`idClasse`) REFERENCES `classi` (`idClasse`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `turni`
--
ALTER TABLE `turni`
  ADD CONSTRAINT `fk_azienda` FOREIGN KEY (`idAzienda`) REFERENCES `aziende` (`idAzienda`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_tutor` FOREIGN KEY (`idTutor`) REFERENCES `tutor` (`idTutor`) ON UPDATE CASCADE,
  ADD CONSTRAINT `turni_ibfk_1` FOREIGN KEY (`idAzienda`) REFERENCES `aziende` (`idAzienda`) ON UPDATE CASCADE,
  ADD CONSTRAINT `turni_ibfk_2` FOREIGN KEY (`idTutor`) REFERENCES `tutor` (`idTutor`) ON UPDATE CASCADE,
  ADD CONSTRAINT `turni_ibfk_3` FOREIGN KEY (`idIndirizzo`) REFERENCES `indirizzi` (`idIndirizzo`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `turnoMateria`
--
ALTER TABLE `turnoMateria`
  ADD CONSTRAINT `fk_materia` FOREIGN KEY (`materia`) REFERENCES `materie` (`materia`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_turno_cascade` FOREIGN KEY (`idTurno`) REFERENCES `turni` (`idTurno`) ON UPDATE CASCADE,
  ADD CONSTRAINT `turnoMateria_ibfk_1` FOREIGN KEY (`materia`) REFERENCES `materie` (`materia`) ON UPDATE CASCADE,
  ADD CONSTRAINT `turnoMateria_ibfk_2` FOREIGN KEY (`idTurno`) REFERENCES `turni` (`idTurno`) ON UPDATE CASCADE;

--
-- Limiti per la tabella `turnoSettore`
--
ALTER TABLE `turnoSettore`
  ADD CONSTRAINT `fk_settore` FOREIGN KEY (`settore`) REFERENCES `settori` (`settore`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_turno` FOREIGN KEY (`idTurno`) REFERENCES `turni` (`idTurno`) ON UPDATE CASCADE,
  ADD CONSTRAINT `turnoSettore_ibfk_1` FOREIGN KEY (`settore`) REFERENCES `settori` (`settore`) ON UPDATE CASCADE,
  ADD CONSTRAINT `turnoSettore_ibfk_2` FOREIGN KEY (`idTurno`) REFERENCES `turni` (`idTurno`) ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
