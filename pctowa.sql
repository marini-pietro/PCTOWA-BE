-- phpMyAdmin SQL Dump
-- version 5.1.0
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Creato il: Apr 02, 2025 alle 12:54
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
  `telefonoAzienda` varchar(13) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `emailAzienda` varchar(50) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `dataConvenzione` date DEFAULT NULL,
  `scadenzaConvenzione` date DEFAULT NULL,
  `categoria` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `indirizzoLogo` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `sitoWeb` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `formaGiuridica` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `classi`
--

CREATE TABLE `classi` (
  `idClasse` int NOT NULL,
  `classe` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `anno` char(9) COLLATE utf8_unicode_ci NOT NULL COMMENT 'e.g. 2024-2025',
  `emailResponsabile` varchar(255) COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

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

-- --------------------------------------------------------

--
-- Struttura della tabella `docenteReferente`
--

CREATE TABLE `docenteReferente` (
  `emailDocente` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `anno` char(4) COLLATE utf8_unicode_ci NOT NULL,
  `idAzienda` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `formaGiuridica`
--

CREATE TABLE `formaGiuridica` (
  `forma` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

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

-- --------------------------------------------------------

--
-- Struttura della tabella `materie`
--

CREATE TABLE `materie` (
  `materia` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `descr` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `hexColor` char(7) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Colore della tag relativa alla materia nella webapp'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `settori`
--

CREATE TABLE `settori` (
  `settore` varchar(255) COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `studenteTurno`
--

CREATE TABLE `studenteTurno` (
  `matricola` int NOT NULL,
  `idTurno` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `studenti`
--

CREATE TABLE `studenti` (
  `matricola` int NOT NULL,
  `nome` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `cognome` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `idClasse` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

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
  `oraInizio` time DEFAULT NULL,
  `oraFine` time DEFAULT NULL
) ;

-- --------------------------------------------------------

--
-- Struttura della tabella `turnoMateria`
--

CREATE TABLE `turnoMateria` (
  `materia` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `idTurno` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `turnoSettore`
--

CREATE TABLE `turnoSettore` (
  `settore` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `idTurno` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Struttura della tabella `utenti`
--

CREATE TABLE `utenti` (
  `emailUtente` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `password` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `nome` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `cognome` varchar(25) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `tipo` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci;

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
  MODIFY `idAzienda` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT per la tabella `classi`
--
ALTER TABLE `classi`
  MODIFY `idClasse` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la tabella `contatti`
--
ALTER TABLE `contatti`
  MODIFY `idContatto` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la tabella `indirizzi`
--
ALTER TABLE `indirizzi`
  MODIFY `idIndirizzo` int NOT NULL AUTO_INCREMENT;

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
