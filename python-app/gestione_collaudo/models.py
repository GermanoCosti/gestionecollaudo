from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Project:
    id: int
    nome: str
    cliente: str
    sito: str
    note: str
    created_at: datetime


@dataclass(frozen=True)
class ChecklistItem:
    id: int
    project_id: int
    titolo: str
    categoria: str
    atteso: str
    ordine: int


@dataclass(frozen=True)
class Run:
    id: int
    project_id: int
    nome: str
    operatore: str
    started_at: datetime
    closed_at: datetime | None


@dataclass(frozen=True)
class RunItem:
    id: int
    run_id: int
    checklist_item_id: int
    esito: str  # PASS/FAIL/SKIP
    note: str
    timestamp: datetime

