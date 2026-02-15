from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Iterable

from gestione_collaudo.models import ChecklistItem, Project, Run


def connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")
    _init_schema(con)
    return con


def _init_schema(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS projects (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          nome TEXT NOT NULL,
          cliente TEXT NOT NULL DEFAULT '',
          sito TEXT NOT NULL DEFAULT '',
          note TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS checklist_items (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          project_id INTEGER NOT NULL,
          titolo TEXT NOT NULL,
          categoria TEXT NOT NULL DEFAULT '',
          atteso TEXT NOT NULL DEFAULT '',
          ordine INTEGER NOT NULL DEFAULT 0,
          FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS runs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          project_id INTEGER NOT NULL,
          nome TEXT NOT NULL,
          operatore TEXT NOT NULL DEFAULT '',
          started_at TEXT NOT NULL,
          closed_at TEXT,
          FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS run_items (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          run_id INTEGER NOT NULL,
          checklist_item_id INTEGER NOT NULL,
          esito TEXT NOT NULL,
          note TEXT NOT NULL DEFAULT '',
          timestamp TEXT NOT NULL,
          FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE,
          FOREIGN KEY(checklist_item_id) REFERENCES checklist_items(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_checklist_project ON checklist_items(project_id);
        CREATE INDEX IF NOT EXISTS idx_runs_project ON runs(project_id);
        CREATE INDEX IF NOT EXISTS idx_run_items_run ON run_items(run_id);
        """
    )
    con.commit()


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def create_project(con: sqlite3.Connection, nome: str, cliente: str = "", sito: str = "", note: str = "") -> int:
    cur = con.execute(
        "INSERT INTO projects(nome, cliente, sito, note, created_at) VALUES(?,?,?,?,?)",
        (nome.strip(), cliente.strip(), sito.strip(), note.strip(), _now_iso()),
    )
    con.commit()
    return int(cur.lastrowid)


def list_projects(con: sqlite3.Connection) -> list[Project]:
    cur = con.execute("SELECT * FROM projects ORDER BY created_at DESC")
    out: list[Project] = []
    for r in cur.fetchall():
        out.append(
            Project(
                id=int(r["id"]),
                nome=str(r["nome"]),
                cliente=str(r["cliente"]),
                sito=str(r["sito"]),
                note=str(r["note"]),
                created_at=datetime.fromisoformat(str(r["created_at"]).replace("Z", "")),
            )
        )
    return out


def delete_project(con: sqlite3.Connection, project_id: int) -> None:
    con.execute("DELETE FROM projects WHERE id=?", (project_id,))
    con.commit()


def replace_checklist(con: sqlite3.Connection, project_id: int, items: Iterable[tuple[str, str, str]]) -> int:
    con.execute("DELETE FROM checklist_items WHERE project_id=?", (project_id,))
    rows = []
    ordine = 1
    for titolo, categoria, atteso in items:
        t = (titolo or "").strip()
        if not t:
            continue
        rows.append((project_id, t, (categoria or "").strip(), (atteso or "").strip(), ordine))
        ordine += 1
    con.executemany(
        "INSERT INTO checklist_items(project_id, titolo, categoria, atteso, ordine) VALUES(?,?,?,?,?)",
        rows,
    )
    con.commit()
    return len(rows)


def list_checklist(con: sqlite3.Connection, project_id: int) -> list[ChecklistItem]:
    cur = con.execute("SELECT * FROM checklist_items WHERE project_id=? ORDER BY ordine ASC, id ASC", (project_id,))
    return [
        ChecklistItem(
            id=int(r["id"]),
            project_id=int(r["project_id"]),
            titolo=str(r["titolo"]),
            categoria=str(r["categoria"]),
            atteso=str(r["atteso"]),
            ordine=int(r["ordine"]),
        )
        for r in cur.fetchall()
    ]


def create_run(con: sqlite3.Connection, project_id: int, nome: str, operatore: str = "") -> int:
    cur = con.execute(
        "INSERT INTO runs(project_id, nome, operatore, started_at) VALUES(?,?,?,?)",
        (project_id, nome.strip(), operatore.strip(), _now_iso()),
    )
    con.commit()
    return int(cur.lastrowid)


def list_runs(con: sqlite3.Connection, project_id: int) -> list[Run]:
    cur = con.execute("SELECT * FROM runs WHERE project_id=? ORDER BY started_at DESC", (project_id,))
    out: list[Run] = []
    for r in cur.fetchall():
        out.append(
            Run(
                id=int(r["id"]),
                project_id=int(r["project_id"]),
                nome=str(r["nome"]),
                operatore=str(r["operatore"]),
                started_at=datetime.fromisoformat(str(r["started_at"]).replace("Z", "")),
                closed_at=(
                    datetime.fromisoformat(str(r["closed_at"]).replace("Z", "")) if r["closed_at"] else None
                ),
            )
        )
    return out


def close_run(con: sqlite3.Connection, run_id: int) -> None:
    con.execute("UPDATE runs SET closed_at=? WHERE id=?", (_now_iso(), run_id))
    con.commit()


def set_run_item(con: sqlite3.Connection, run_id: int, checklist_item_id: int, esito: str, note: str = "") -> None:
    esito_n = esito.strip().upper()
    if esito_n not in ["PASS", "FAIL", "SKIP"]:
        raise ValueError("Esito non valido. Usa PASS, FAIL o SKIP.")

    cur = con.execute(
        "SELECT id FROM run_items WHERE run_id=? AND checklist_item_id=?",
        (run_id, checklist_item_id),
    )
    row = cur.fetchone()
    if row:
        con.execute(
            "UPDATE run_items SET esito=?, note=?, timestamp=? WHERE id=?",
            (esito_n, (note or "").strip(), _now_iso(), int(row["id"])),
        )
    else:
        con.execute(
            "INSERT INTO run_items(run_id, checklist_item_id, esito, note, timestamp) VALUES(?,?,?,?,?)",
            (run_id, checklist_item_id, esito_n, (note or "").strip(), _now_iso()),
        )
    con.commit()


def get_run_progress(con: sqlite3.Connection, run_id: int) -> dict[int, dict[str, str]]:
    cur = con.execute("SELECT checklist_item_id, esito, note, timestamp FROM run_items WHERE run_id=?", (run_id,))
    out: dict[int, dict[str, str]] = {}
    for r in cur.fetchall():
        out[int(r["checklist_item_id"])] = {
            "esito": str(r["esito"]),
            "note": str(r["note"]),
            "timestamp": str(r["timestamp"]),
        }
    return out


def get_project(con: sqlite3.Connection, project_id: int) -> Project | None:
    cur = con.execute("SELECT * FROM projects WHERE id=?", (project_id,))
    r = cur.fetchone()
    if not r:
        return None
    return Project(
        id=int(r["id"]),
        nome=str(r["nome"]),
        cliente=str(r["cliente"]),
        sito=str(r["sito"]),
        note=str(r["note"]),
        created_at=datetime.fromisoformat(str(r["created_at"]).replace("Z", "")),
    )

