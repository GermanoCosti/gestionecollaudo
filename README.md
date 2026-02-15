# Gestione Collaudo

App Windows (Python) per gestire checklist di collaudo/commissioning:
- progetti (impianto/linea/macchina)
- checklist (voci di prova)
- esecuzioni (run) con esito Pass/Fail, note, timestamp, operatore
- export report (Markdown/HTML)

Stato: MVP.

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

