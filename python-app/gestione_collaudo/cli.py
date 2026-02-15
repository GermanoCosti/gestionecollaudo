from __future__ import annotations

import argparse
import pathlib
import sys

from gestione_collaudo import APP_AUTORE, APP_NOME, APP_VERSIONE
from gestione_collaudo import db
from gestione_collaudo.importers import import_checklist_csv
from gestione_collaudo.reports import build_markdown_report, markdown_to_simple_html


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="gestione-collaudo",
        description=f"{APP_NOME} (MVP) - {APP_AUTORE}",
    )
    parser.add_argument("--version", action="store_true", help="Mostra versione e esce")
    parser.add_argument("--db", default="collaudo.sqlite", help="Percorso DB SQLite")
    # Non rendiamo obbligatorio il subcomando per consentire `--version` senza errori.
    sub = parser.add_subparsers(dest="cmd")

    p_new = sub.add_parser("new-project", help="Crea un progetto")
    p_new.add_argument("--nome", required=True)
    p_new.add_argument("--cliente", default="")
    p_new.add_argument("--sito", default="")
    p_new.add_argument("--note", default="")

    p_imp = sub.add_parser("import-checklist", help="Importa checklist da CSV (sostituisce)")
    p_imp.add_argument("--project-id", type=int, required=True)
    p_imp.add_argument("--csv", required=True)

    p_run = sub.add_parser("new-run", help="Crea una nuova esecuzione")
    p_run.add_argument("--project-id", type=int, required=True)
    p_run.add_argument("--nome", required=True)
    p_run.add_argument("--operatore", default="")

    p_rep = sub.add_parser("export-report", help="Esporta report di un run")
    p_rep.add_argument("--project-id", type=int, required=True)
    p_rep.add_argument("--run-id", type=int, required=True)
    p_rep.add_argument("--out-md", required=True)
    p_rep.add_argument("--out-html", required=False)

    args = parser.parse_args()
    if args.version:
        print(f"{APP_NOME} v{APP_VERSIONE} - {APP_AUTORE}")
        return 0
    if not args.cmd:
        parser.print_help()
        return 2
    con = db.connect(args.db)

    if args.cmd == "new-project":
        pid = db.create_project(con, args.nome, args.cliente, args.sito, args.note)
        print(f"OK project_id={pid}")
        return 0

    if args.cmd == "import-checklist":
        items = import_checklist_csv(args.csv)
        n = db.replace_checklist(con, args.project_id, items)
        print(f"OK checklist importata: {n} voci")
        return 0

    if args.cmd == "new-run":
        rid = db.create_run(con, args.project_id, args.nome, args.operatore)
        print(f"OK run_id={rid}")
        return 0

    if args.cmd == "export-report":
        project = db.get_project(con, args.project_id)
        if not project:
            print("Progetto non trovato.", file=sys.stderr)
            return 1
        runs = [r for r in db.list_runs(con, args.project_id) if r.id == args.run_id]
        if not runs:
            print("Run non trovato.", file=sys.stderr)
            return 1
        run = runs[0]
        checklist = db.list_checklist(con, args.project_id)
        progress = db.get_run_progress(con, args.run_id)
        md = build_markdown_report(project, run, checklist, progress, generated_by=f"{APP_NOME} v{APP_VERSIONE} ({APP_AUTORE})")
        out_md = pathlib.Path(args.out_md).resolve()
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(md, encoding="utf-8")
        print(f"OK MD: {out_md}")
        if args.out_html:
            out_html = pathlib.Path(args.out_html).resolve()
            out_html.parent.mkdir(parents=True, exist_ok=True)
            out_html.write_text(markdown_to_simple_html(md, footer=f"{APP_NOME} v{APP_VERSIONE} - {APP_AUTORE}"), encoding="utf-8")
            print(f"OK HTML: {out_html}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
