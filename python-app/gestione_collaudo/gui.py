from __future__ import annotations

import pathlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from gestione_collaudo import db
from gestione_collaudo.importers import import_checklist_csv
from gestione_collaudo.reports import build_markdown_report, markdown_to_simple_html


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Gestione Collaudo (MVP)")
        self.geometry("1080x720")
        self.minsize(980, 660)

        self.db_path = tk.StringVar(value=str(pathlib.Path("collaudo.sqlite").resolve()))

        self.project_id = tk.IntVar(value=0)
        self.run_id = tk.IntVar(value=0)
        self.operatore = tk.StringVar(value="")

        self._build()
        self._refresh_projects()

    def _build(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        top = ttk.LabelFrame(root, text="Database")
        top.pack(fill="x")
        ttk.Label(top, text="SQLite").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        ttk.Entry(top, textvariable=self.db_path).grid(row=0, column=1, sticky="ew", padx=8, pady=8)
        ttk.Button(top, text="Scegli...", command=self._choose_db).grid(row=0, column=2, padx=8, pady=8)
        ttk.Button(top, text="Aggiorna", command=self._refresh_projects).grid(row=0, column=3, padx=8, pady=8)
        top.columnconfigure(1, weight=1)

        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, pady=(12, 0))

        self.tab_proj = ttk.Frame(nb, padding=12)
        self.tab_check = ttk.Frame(nb, padding=12)
        self.tab_run = ttk.Frame(nb, padding=12)
        self.tab_rep = ttk.Frame(nb, padding=12)
        nb.add(self.tab_proj, text="Progetti")
        nb.add(self.tab_check, text="Checklist")
        nb.add(self.tab_run, text="Esecuzione")
        nb.add(self.tab_rep, text="Report")

        self._build_projects_tab()
        self._build_checklist_tab()
        self._build_run_tab()
        self._build_report_tab()

    def _con(self):
        return db.connect(self.db_path.get().strip())

    def _choose_db(self) -> None:
        p = filedialog.asksaveasfilename(
            title="Scegli DB SQLite",
            defaultextension=".sqlite",
            filetypes=[("SQLite", "*.sqlite;*.db"), ("Tutti i file", "*.*")],
            initialfile="collaudo.sqlite",
        )
        if p:
            self.db_path.set(p)
            self._refresh_projects()

    # Progetti
    def _build_projects_tab(self) -> None:
        f = self.tab_proj
        left = ttk.Frame(f)
        left.pack(side="left", fill="both", expand=True)
        right = ttk.LabelFrame(f, text="Nuovo progetto")
        right.pack(side="right", fill="y", padx=(12, 0))

        self.projects = ttk.Treeview(left, columns=("id", "nome", "cliente", "sito"), show="headings", height=18)
        for c, w in [("id", 60), ("nome", 280), ("cliente", 200), ("sito", 260)]:
            self.projects.heading(c, text=c)
            self.projects.column(c, width=w, anchor="w")
        self.projects.pack(fill="both", expand=True)
        self.projects.bind("<<TreeviewSelect>>", lambda e: self._on_project_select())

        btns = ttk.Frame(left)
        btns.pack(fill="x", pady=(10, 0))
        ttk.Button(btns, text="Elimina progetto", command=self._delete_project).pack(side="left")

        self.p_nome = tk.StringVar(value="")
        self.p_cliente = tk.StringVar(value="")
        self.p_sito = tk.StringVar(value="")

        def row(r: int, label: str, var: tk.StringVar) -> None:
            ttk.Label(right, text=label).grid(row=r, column=0, sticky="w", padx=8, pady=(8, 0))
            ttk.Entry(right, textvariable=var, width=34).grid(row=r + 1, column=0, sticky="ew", padx=8, pady=(0, 8))

        row(0, "Nome", self.p_nome)
        row(2, "Cliente", self.p_cliente)
        row(4, "Sito", self.p_sito)
        ttk.Label(right, text="Note").grid(row=6, column=0, sticky="w", padx=8, pady=(8, 0))
        self.p_note_box = tk.Text(right, height=4, width=34)
        self.p_note_box.grid(row=7, column=0, padx=8, pady=(0, 8))
        ttk.Button(right, text="Crea", command=self._create_project).grid(row=8, column=0, padx=8, pady=8, sticky="ew")

    def _refresh_projects(self) -> None:
        con = self._con()
        projs = db.list_projects(con)
        for i in self.projects.get_children():
            self.projects.delete(i)
        for p in projs:
            self.projects.insert("", "end", values=(p.id, p.nome, p.cliente, p.sito))
        if projs and self.project_id.get() == 0:
            self.project_id.set(projs[0].id)
        self._refresh_checklist()
        self._refresh_runs()

    def _on_project_select(self) -> None:
        sel = self.projects.selection()
        if not sel:
            return
        vals = self.projects.item(sel[0], "values")
        if vals:
            self.project_id.set(int(vals[0]))
            self.run_id.set(0)
            self._refresh_checklist()
            self._refresh_runs()

    def _create_project(self) -> None:
        nome = self.p_nome.get().strip()
        if not nome:
            messagebox.showerror("Errore", "Inserisci un nome progetto.")
            return
        note = self.p_note_box.get("1.0", tk.END).strip()
        con = self._con()
        pid = db.create_project(con, nome, self.p_cliente.get(), self.p_sito.get(), note)
        self.project_id.set(pid)
        self.p_nome.set("")
        self.p_cliente.set("")
        self.p_sito.set("")
        self.p_note_box.delete("1.0", tk.END)
        self._refresh_projects()

    def _delete_project(self) -> None:
        pid = self.project_id.get()
        if pid <= 0:
            return
        if messagebox.askyesno("Conferma", "Eliminare il progetto selezionato? (anche checklist e run)"):
            con = self._con()
            db.delete_project(con, pid)
            self.project_id.set(0)
            self.run_id.set(0)
            self._refresh_projects()

    # Checklist
    def _build_checklist_tab(self) -> None:
        f = self.tab_check
        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Button(top, text="Importa checklist da CSV (sostituisce)", command=self._import_checklist).pack(side="left")
        ttk.Button(top, text="Aggiorna", command=self._refresh_checklist).pack(side="left", padx=8)
        self.check_label = ttk.Label(top, text="Nessun progetto selezionato.")
        self.check_label.pack(side="right")

        self.checklist = ttk.Treeview(f, columns=("ordine", "categoria", "titolo", "atteso"), show="headings", height=20)
        for c, w in [("ordine", 60), ("categoria", 140), ("titolo", 420), ("atteso", 340)]:
            self.checklist.heading(c, text=c)
            self.checklist.column(c, width=w, anchor="w")
        self.checklist.pack(fill="both", expand=True, pady=(10, 0))

    def _refresh_checklist(self) -> None:
        pid = self.project_id.get()
        for i in self.checklist.get_children():
            self.checklist.delete(i)
        if pid <= 0:
            self.check_label.configure(text="Nessun progetto selezionato.")
            return
        con = self._con()
        items = db.list_checklist(con, pid)
        self.check_label.configure(text=f"Voci: {len(items)} | project_id={pid}")
        for it in items:
            self.checklist.insert("", "end", values=(it.ordine, it.categoria, it.titolo, it.atteso))

    def _import_checklist(self) -> None:
        pid = self.project_id.get()
        if pid <= 0:
            messagebox.showerror("Errore", "Seleziona un progetto.")
            return
        p = filedialog.askopenfilename(
            title="Scegli checklist CSV",
            filetypes=[("CSV", "*.csv;*.txt"), ("Tutti i file", "*.*")],
        )
        if not p:
            return
        try:
            items = import_checklist_csv(p)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Errore import", str(exc))
            return
        con = self._con()
        n = db.replace_checklist(con, pid, items)
        messagebox.showinfo("OK", f"Checklist importata: {n} voci")
        self._refresh_checklist()

    # Esecuzioni
    def _build_run_tab(self) -> None:
        f = self.tab_run
        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Label(top, text="Operatore").pack(side="left")
        ttk.Entry(top, textvariable=self.operatore, width=18).pack(side="left", padx=(8, 16))
        ttk.Button(top, text="Nuovo run", command=self._new_run).pack(side="left")
        ttk.Button(top, text="Chiudi run", command=self._close_run).pack(side="left", padx=8)
        ttk.Button(top, text="Aggiorna", command=self._refresh_runs).pack(side="left")
        self.run_label = ttk.Label(top, text="Nessun run.")
        self.run_label.pack(side="right")

        mid = ttk.Frame(f)
        mid.pack(fill="both", expand=True, pady=(10, 0))
        left = ttk.Frame(mid)
        left.pack(side="left", fill="both", expand=True)
        right = ttk.LabelFrame(mid, text="Esito voce selezionata")
        right.pack(side="right", fill="y", padx=(12, 0))

        self.runs = ttk.Treeview(left, columns=("id", "nome", "operatore", "started", "closed"), show="headings", height=8)
        for c, w in [("id", 60), ("nome", 240), ("operatore", 120), ("started", 170), ("closed", 170)]:
            self.runs.heading(c, text=c)
            self.runs.column(c, width=w, anchor="w")
        self.runs.pack(fill="x")
        self.runs.bind("<<TreeviewSelect>>", lambda e: self._on_run_select())

        self.run_items = ttk.Treeview(left, columns=("id", "categoria", "titolo", "esito", "timestamp"), show="headings", height=18)
        for c, w in [("id", 60), ("categoria", 140), ("titolo", 420), ("esito", 90), ("timestamp", 170)]:
            self.run_items.heading(c, text=c)
            self.run_items.column(c, width=w, anchor="w")
        self.run_items.pack(fill="both", expand=True, pady=(10, 0))
        self.run_items.bind("<<TreeviewSelect>>", lambda e: self._on_item_select())

        self.item_id = tk.IntVar(value=0)

        ttk.Label(right, text="Note").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 0))
        self.note_box = tk.Text(right, height=8, width=36)
        self.note_box.grid(row=1, column=0, padx=8, pady=(0, 8))

        btns = ttk.Frame(right)
        btns.grid(row=2, column=0, padx=8, pady=8, sticky="ew")
        ttk.Button(btns, text="PASS", command=lambda: self._set_esito("PASS")).pack(side="left")
        ttk.Button(btns, text="FAIL", command=lambda: self._set_esito("FAIL")).pack(side="left", padx=8)
        ttk.Button(btns, text="SKIP", command=lambda: self._set_esito("SKIP")).pack(side="left")

    def _refresh_runs(self) -> None:
        pid = self.project_id.get()
        for i in self.runs.get_children():
            self.runs.delete(i)
        for i in self.run_items.get_children():
            self.run_items.delete(i)
        if pid <= 0:
            self.run_label.configure(text="Nessun progetto selezionato.")
            return
        con = self._con()
        runs = db.list_runs(con, pid)
        self.run_label.configure(text=f"Run: {len(runs)} | project_id={pid}")
        for r in runs:
            self.runs.insert(
                "",
                "end",
                values=(
                    r.id,
                    r.nome,
                    r.operatore,
                    r.started_at.isoformat(timespec="seconds"),
                    r.closed_at.isoformat(timespec="seconds") if r.closed_at else "",
                ),
            )

    def _on_run_select(self) -> None:
        sel = self.runs.selection()
        if not sel:
            return
        vals = self.runs.item(sel[0], "values")
        if not vals:
            return
        self.run_id.set(int(vals[0]))
        self._refresh_run_items()

    def _new_run(self) -> None:
        pid = self.project_id.get()
        if pid <= 0:
            messagebox.showerror("Errore", "Seleziona un progetto.")
            return
        con = self._con()
        rid = db.create_run(con, pid, f"Run {pid}", self.operatore.get())
        self.run_id.set(rid)
        self._refresh_runs()
        self._refresh_run_items()

    def _close_run(self) -> None:
        rid = self.run_id.get()
        if rid <= 0:
            return
        con = self._con()
        db.close_run(con, rid)
        self._refresh_runs()

    def _refresh_run_items(self) -> None:
        rid = self.run_id.get()
        pid = self.project_id.get()
        for i in self.run_items.get_children():
            self.run_items.delete(i)
        if rid <= 0 or pid <= 0:
            return
        con = self._con()
        checklist = db.list_checklist(con, pid)
        prog = db.get_run_progress(con, rid)
        for it in checklist:
            p = prog.get(it.id)
            esito = p["esito"] if p else "TODO"
            ts = p["timestamp"] if p else ""
            self.run_items.insert("", "end", values=(it.id, it.categoria, it.titolo, esito, ts))

    def _on_item_select(self) -> None:
        sel = self.run_items.selection()
        if not sel:
            return
        vals = self.run_items.item(sel[0], "values")
        if not vals:
            return
        self.item_id.set(int(vals[0]))
        con = self._con()
        prog = db.get_run_progress(con, self.run_id.get())
        p = prog.get(self.item_id.get())
        self.note_box.delete("1.0", tk.END)
        if p and p.get("note"):
            self.note_box.insert(tk.END, p["note"])

    def _set_esito(self, esito: str) -> None:
        rid = self.run_id.get()
        cid = self.item_id.get()
        if rid <= 0 or cid <= 0:
            messagebox.showerror("Errore", "Seleziona un run e una voce.")
            return
        note = self.note_box.get("1.0", tk.END).strip()
        con = self._con()
        db.set_run_item(con, rid, cid, esito, note)
        self._refresh_run_items()

    # Report
    def _build_report_tab(self) -> None:
        f = self.tab_rep
        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Button(top, text="Genera report (MD + HTML)", command=self._gen_report).pack(side="left")
        ttk.Button(top, text="Apri cartella export", command=self._open_export_dir).pack(side="left", padx=8)
        self.rep_label = ttk.Label(top, text="")
        self.rep_label.pack(side="right")

        self.rep_text = tk.Text(f, height=28, wrap="word")
        self.rep_text.pack(fill="both", expand=True, pady=(10, 0))
        self.rep_text.configure(state="disabled")

    def _open_export_dir(self) -> None:
        out = pathlib.Path("_export").resolve()
        out.mkdir(parents=True, exist_ok=True)
        try:
            import os

            os.startfile(str(out))  # type: ignore[attr-defined]
        except Exception:
            pass

    def _set_rep(self, text: str) -> None:
        self.rep_text.configure(state="normal")
        self.rep_text.delete("1.0", tk.END)
        self.rep_text.insert(tk.END, text)
        self.rep_text.configure(state="disabled")

    def _gen_report(self) -> None:
        pid = self.project_id.get()
        rid = self.run_id.get()
        if pid <= 0 or rid <= 0:
            messagebox.showerror("Errore", "Seleziona un progetto e un run.")
            return
        con = self._con()
        project = db.get_project(con, pid)
        runs = [r for r in db.list_runs(con, pid) if r.id == rid]
        if not project or not runs:
            messagebox.showerror("Errore", "Dati non trovati.")
            return
        run = runs[0]
        checklist = db.list_checklist(con, pid)
        progress = db.get_run_progress(con, rid)
        md = build_markdown_report(project, run, checklist, progress)
        outdir = pathlib.Path("_export").resolve()
        outdir.mkdir(parents=True, exist_ok=True)
        base = f"report_project{pid}_run{rid}"
        md_path = outdir / f"{base}.md"
        html_path = outdir / f"{base}.html"
        md_path.write_text(md, encoding="utf-8")
        html_path.write_text(markdown_to_simple_html(md), encoding="utf-8")
        self.rep_label.configure(text=f"Creati: {md_path.name}, {html_path.name}")
        self._set_rep(md)
        messagebox.showinfo("OK", f"Report creato in:\\n{outdir}")


def main() -> int:
    app = App()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
