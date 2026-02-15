# Gestione Collaudo

Gestione collaudi e commissioning in azienda: checklist, esecuzioni, tracciabilita e report pronti da condividere (Windows, Python, SQLite).

## Scarica (Windows)
1. Apri la pagina Releases: https://github.com/GermanoCosti/gestionecollaudo/releases/latest
1. In "Assets" scarica `GestioneCollaudo.exe` (oppure lo zip)
1. Avvia l'eseguibile (Windows potrebbe mostrare SmartScreen al primo avvio)

App Windows (Python) per gestire checklist di collaudo/commissioning:
- progetti (impianto/linea/macchina)
- checklist (voci di prova)
- esecuzioni (run) con esito Pass/Fail, note, timestamp, operatore
- export report (Markdown/HTML)

Stato: MVP.

## Autore
Creato e mantenuto da **Germano Costi** (GitHub: `GermanoCosti`).

## Avvio rapido (sviluppo)
```powershell
cd python-app
python -m pip install -e .
gestione-collaudo-gui
```

## Import checklist (CSV)
Il CSV deve avere intestazioni (minime):
- `titolo`
- `categoria` (opzionale)
- `atteso` (opzionale)

## Nota
Questo tool non sostituisce procedure di sicurezza e normative: e' un supporto operativo per tracciare prove e risultati.
