from __future__ import annotations

import html

from gestione_collaudo.models import ChecklistItem, Project, Run


def build_markdown_report(
    project: Project,
    run: Run,
    checklist: list[ChecklistItem],
    progress: dict[int, dict[str, str]],
) -> str:
    done = 0
    fail = 0
    for item in checklist:
        p = progress.get(item.id)
        if not p:
            continue
        done += 1
        if p.get("esito") == "FAIL":
            fail += 1

    total = len(checklist)

    lines: list[str] = []
    lines.append(f"# Report collaudo - {project.nome}")
    lines.append("")
    lines.append(f"- Cliente: {project.cliente or '-'}")
    lines.append(f"- Sito: {project.sito or '-'}")
    lines.append(f"- Run: {run.nome}")
    lines.append(f"- Operatore: {run.operatore or '-'}")
    lines.append(f"- Avvio: {run.started_at.isoformat(timespec='seconds')}")
    if run.closed_at:
        lines.append(f"- Chiusura: {run.closed_at.isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Sintesi")
    lines.append("")
    lines.append(f"- Totale prove: **{total}**")
    lines.append(f"- Eseguite: **{done}**")
    lines.append(f"- Fail: **{fail}**")
    lines.append("")
    lines.append("## Dettaglio prove")
    lines.append("")

    for item in checklist:
        p = progress.get(item.id)
        esito = p.get("esito") if p else "TODO"
        note = (p.get("note") if p else "") or ""
        ts = (p.get("timestamp") if p else "") or ""
        cat = f"[{item.categoria}] " if item.categoria else ""

        lines.append(f"- **{esito}** - {cat}{item.titolo}")
        if item.atteso:
            lines.append(f"  - Atteso: {item.atteso}")
        if ts:
            lines.append(f"  - Timestamp: {ts}")
        if note:
            lines.append(f"  - Note: {note}")

    lines.append("")
    return "\n".join(lines)


def markdown_to_simple_html(md: str) -> str:
    # Convertitore minimale (non completo). Serve solo a rendere condivisibile il report.
    lines = md.splitlines()
    out: list[str] = []
    out.append('<!doctype html><html lang="it"><head><meta charset="utf-8"/>')
    out.append('<meta name="viewport" content="width=device-width, initial-scale=1"/>')
    out.append("<title>Report collaudo</title>")
    out.append(
        "<style>"
        "body{font-family:system-ui,Segoe UI,Arial;max-width:900px;margin:24px auto;padding:0 16px;}"
        "h1{font-size:28px;} h2{margin-top:22px;} ul{padding-left:18px;}"
        "code{background:#f2f2f2;padding:2px 6px;border-radius:6px;}"
        "</style>"
    )
    out.append("</head><body>")

    ul_open = False
    for line in lines:
        if line.startswith("# "):
            if ul_open:
                out.append("</ul>")
                ul_open = False
            out.append(f"<h1>{html.escape(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            if ul_open:
                out.append("</ul>")
                ul_open = False
            out.append(f"<h2>{html.escape(line[3:].strip())}</h2>")
        elif line.startswith("- "):
            if not ul_open:
                out.append("<ul>")
                ul_open = True
            out.append(f"<li>{html.escape(line[2:].strip())}</li>")
        elif not line.strip():
            if ul_open:
                out.append("</ul>")
                ul_open = False
        else:
            if ul_open:
                out.append("</ul>")
                ul_open = False
            out.append(f"<p>{html.escape(line)}</p>")

    if ul_open:
        out.append("</ul>")

    out.append("</body></html>")
    return "\n".join(out)

