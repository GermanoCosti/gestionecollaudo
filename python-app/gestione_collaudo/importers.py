from __future__ import annotations

import csv
import pathlib


def import_checklist_csv(path: str) -> list[tuple[str, str, str]]:
    p = pathlib.Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"File non trovato: {p}")
    with p.open("r", encoding="utf-8", errors="replace", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\\t,")
        reader = csv.DictReader(f, dialect=dialect)
        if not reader.fieldnames:
            raise ValueError("CSV senza intestazioni.")
        headers = [h.strip().lower() for h in reader.fieldnames]
        if "titolo" not in headers:
            raise ValueError("CSV deve contenere la colonna 'titolo'.")

        out: list[tuple[str, str, str]] = []
        for r in reader:
            titolo = str(r.get(_col(reader.fieldnames, "titolo"), "") or "").strip()
            categoria = str(r.get(_col(reader.fieldnames, "categoria"), "") or "").strip()
            atteso = str(r.get(_col(reader.fieldnames, "atteso"), "") or "").strip()
            if titolo:
                out.append((titolo, categoria, atteso))
    return out


def _col(fieldnames: list[str] | None, name: str) -> str:
    if not fieldnames:
        return name
    for f in fieldnames:
        if f.strip().lower() == name:
            return f
    return name

