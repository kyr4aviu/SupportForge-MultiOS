from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from . import __version__
from .bundle import create_bundle
from .platforms import current_platform
from .evidence import filter_findings, search_evidence
from .history import (
    DEFAULT_HISTORY_DIR,
    list_history,
    prune_history,
    save_history_snapshot,
    snapshot_stem,
)
from .html_report import generate_html_report
from .postgres_v2 import collect_postgres_snapshot
from .permissions import get_permissions
from .workstation import (
    collect_workstation_snapshot,
    load_snapshot,
    save_snapshot,
)

PRODUCT_NAME = "SupportForge Multi-OS"
APP_TITLE = f"{PRODUCT_NAME} {__version__}"


def default_export_dir() -> Path:
    desktop = Path.home() / "Desktop"
    return desktop if desktop.exists() else Path.home()


def default_export_stem(prefix: str = "supportforge-incident") -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def snapshot_export_stem(snapshot: dict[str, Any] | None, prefix: str = "supportforge-incident") -> str:
    """Return one stable export name for every artifact from the same scan."""
    if snapshot:
        return snapshot_stem(snapshot)
    return default_export_stem(prefix)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1280x800")
        self.minsize(1000, 650)

        self.snapshot: dict[str, Any] | None = None
        self.postgres_snapshot: dict[str, Any] | None = None
        self.previous_snapshot: dict[str, Any] | None = None
        self.busy = False
        self.closing = False
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._set_status("Ready — read-only diagnostics")

    def _build(self):
        self._configure_style()

        header = ttk.Frame(self, padding=(14, 12))
        header.pack(fill="x")
        title = ttk.Label(header, text=PRODUCT_NAME, style="Title.TLabel")
        title.pack(side="left")
        ttk.Label(
            header,
            text=f"{__version__}  •  Host: {current_platform().upper()}",
            style="Muted.TLabel",
        ).pack(side="right")

        toolbar = ttk.Frame(self, padding=(14, 0, 14, 10))
        toolbar.pack(fill="x")
        self.scan_btn = ttk.Button(
            toolbar, text="Run Full Diagnostic", command=self.run_scan
        )
        self.scan_btn.pack(side="left")
        ttk.Button(toolbar, text="HTML Report", command=self.export_html).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Incident Bundle", command=self.export_bundle).pack(
            side="left", padx=(8, 0)
        )

        self.progress = ttk.Progressbar(toolbar, mode="indeterminate", length=180)
        self.progress.pack(side="right")

        content = ttk.Frame(self, padding=(14, 0, 14, 10))
        content.pack(fill="both", expand=True)

        self.nav = ttk.Notebook(content)
        self.nav.pack(fill="both", expand=True)

        self.dashboard_tab = ttk.Frame(self.nav)
        self.system_tab = ttk.Frame(self.nav)
        self.network_tab = ttk.Frame(self.nav)
        self.logs_tab = ttk.Frame(self.nav)
        self.docker_tab = ttk.Frame(self.nav)
        self.security_tab = ttk.Frame(self.nav)
        self.postgres_tab = ttk.Frame(self.nav)
        self.history_tab = ttk.Frame(self.nav)
        self.permissions_tab = ttk.Frame(self.nav)
        self.evidence_tab = ttk.Frame(self.nav)
        self.diff_tab = ttk.Frame(self.nav)

        for tab, label in (
            (self.dashboard_tab, "Dashboard"),
            (self.system_tab, "System"),
            (self.network_tab, "Network"),
            (self.logs_tab, "Logs"),
            (self.docker_tab, "Docker"),
            (self.security_tab, "Security"),
            (self.postgres_tab, "PostgreSQL"),
            (self.history_tab, "History"),
            (self.permissions_tab, "Permissions"),
            (self.evidence_tab, "Raw Evidence"),
            (self.diff_tab, "Diff"),
        ):
            self.nav.add(tab, text=label)

        self._build_dashboard()
        self.system_text = self._text_view(self.system_tab)
        self.network_text = self._text_view(self.network_tab)
        self.logs_text = self._text_view(self.logs_tab)
        self.docker_text = self._text_view(self.docker_tab)
        self.security_text = self._text_view(self.security_tab)
        self._build_postgres_tab()
        self._build_history_tab()
        self._build_permissions_tab()
        self._build_evidence_tab()
        self._build_diff_tab()

        footer = ttk.Frame(self, padding=(14, 0, 14, 10))
        footer.pack(fill="x")
        self.status = ttk.Label(footer, style="Muted.TLabel")
        self.status.pack(side="left")
        self.last_run = ttk.Label(footer, text="No scan yet", style="Muted.TLabel")
        self.last_run.pack(side="right")

    def _build_permissions_tab(self):
        frame = ttk.Frame(self.permissions_tab, padding=10)
        frame.pack(fill="both", expand=True)
        ttk.Label(
            frame,
            text="SupportForge never automatically elevates privileges.",
            font=("TkDefaultFont", 12, "bold"),
        ).pack(anchor="w", pady=(0,10))
        tree = ttk.Treeview(
            frame, columns=("feature","context","elevation"), show="headings"
        )
        tree.heading("feature", text="Diagnostic area")
        tree.heading("context", text="Normal context")
        tree.heading("elevation", text="Elevation")
        tree.column("feature", width=300)
        tree.column("context", width=250)
        tree.column("elevation", width=420)
        for item in get_permissions(current_platform()):
            tree.insert("", "end", values=(
                item["feature"], item["default"], item["elevation"]
            ))
        tree.pack(fill="both", expand=True)

    def _build_evidence_tab(self):
        frame = ttk.Frame(self.evidence_tab, padding=10)
        frame.pack(fill="both", expand=True)
        controls = ttk.Frame(frame)
        controls.pack(fill="x")
        ttk.Label(controls, text="Search").pack(side="left")
        self.evidence_query = tk.StringVar()
        entry = ttk.Entry(controls, textvariable=self.evidence_query, width=45)
        entry.pack(side="left", padx=(6,8))
        entry.bind("<Return>", lambda _e: self.refresh_evidence())
        ttk.Button(controls, text="Find", command=self.refresh_evidence).pack(side="left")
        ttk.Button(controls, text="Clear", command=self.clear_evidence_search).pack(side="left", padx=(6,0))
        self.evidence_count = ttk.Label(controls, text="0 rows", style="Muted.TLabel")
        self.evidence_count.pack(side="right")

        self.evidence_tree = ttk.Treeview(frame, columns=("path","value"), show="headings")
        self.evidence_tree.heading("path", text="Path")
        self.evidence_tree.heading("value", text="Value")
        self.evidence_tree.column("path", width=360, stretch=False)
        self.evidence_tree.column("value", width=780)
        ys = ttk.Scrollbar(frame, orient="vertical", command=self.evidence_tree.yview)
        self.evidence_tree.configure(yscrollcommand=ys.set)
        self.evidence_tree.pack(side="left", fill="both", expand=True, pady=(10,0))
        ys.pack(side="right", fill="y", pady=(10,0))

    def refresh_evidence(self):
        for item in self.evidence_tree.get_children():
            self.evidence_tree.delete(item)
        if not self.snapshot:
            self.evidence_count.config(text="0 rows")
            return
        rows = search_evidence(self.snapshot, self.evidence_query.get())
        for row in rows[:5000]:
            self.evidence_tree.insert("", "end", values=(row["path"], row["value"]))
        suffix = " (limited to 5000)" if len(rows) > 5000 else ""
        self.evidence_count.config(text=f"{len(rows)} rows{suffix}")

    def clear_evidence_search(self):
        self.evidence_query.set("")
        self.refresh_evidence()

    def _build_postgres_tab(self):
        frame = ttk.Frame(self.postgres_tab, padding=10)
        frame.pack(fill="both", expand=True)
        controls = ttk.Frame(frame)
        controls.pack(fill="x")
        self.pg_host = tk.StringVar(value="localhost")
        self.pg_port = tk.StringVar(value="5432")
        self.pg_db = tk.StringVar(value="postgres")
        self.pg_user = tk.StringVar(value="")
        for label, var, width in (
            ("Host", self.pg_host, 18), ("Port", self.pg_port, 7),
            ("Database", self.pg_db, 14), ("User", self.pg_user, 14),
        ):
            ttk.Label(controls, text=label).pack(side="left", padx=(0,4))
            ttk.Entry(controls, textvariable=var, width=width).pack(side="left", padx=(0,10))
        ttk.Button(controls, text="Check PostgreSQL", command=self.run_postgres).pack(side="left")
        self.postgres_text = tk.Text(frame, wrap="none", font=("TkFixedFont",10))
        self.postgres_text.pack(fill="both", expand=True, pady=(10,0))

    def _build_history_tab(self):
        frame = ttk.Frame(self.history_tab, padding=10)
        frame.pack(fill="both", expand=True)
        ttk.Label(
            frame,
            text=("Saved diagnostics are stored automatically. Select one scan to load it, "
                  "or select exactly two scans to compare older → newer."),
            wraplength=950,
        ).pack(anchor="w", pady=(0, 8))
        controls = ttk.Frame(frame)
        controls.pack(fill="x")
        ttk.Button(controls, text="Refresh", command=self.refresh_history).pack(side="left")
        ttk.Button(controls, text="Load Selected", command=self.load_history_selected).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="Compare Two Selected", command=self.compare_history_selected).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="Delete Selected", command=self.delete_history_selected).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="Open History Folder", command=self.open_history_folder).pack(side="left", padx=(8, 0))
        ttk.Label(controls, text=str(DEFAULT_HISTORY_DIR), style="Muted.TLabel").pack(side="right")
        self.history_paths: list[Path] = []
        self.history_list = tk.Listbox(frame, selectmode="multiple", exportselection=False)
        self.history_list.pack(fill="both", expand=True, pady=(8,0))
        self.history_list.bind("<Double-1>", lambda _e: self.load_history_selected())
        self.refresh_history()

    def _build_diff_tab(self):
        frame = ttk.Frame(self.diff_tab, padding=10)
        frame.pack(fill="both", expand=True)
        ttk.Label(
            frame,
            text=("Diff shows what changed between two saved diagnostics. Use History, select "
                  "exactly two scans, then choose Compare Two Selected. Changes are shown "
                  "from the older scan to the newer scan; large raw outputs are summarized."),
            wraplength=1000,
        ).pack(anchor="w", pady=(0, 8))
        panes = ttk.Panedwindow(frame, orient="horizontal")
        panes.pack(fill="both", expand=True)
        older = ttk.LabelFrame(panes, text="Older snapshot", padding=4)
        newer = ttk.LabelFrame(panes, text="Newer snapshot — changed values highlighted", padding=4)
        panes.add(older, weight=1)
        panes.add(newer, weight=1)
        self.diff_older_label = older
        self.diff_newer_label = newer
        self.diff_older_text = self._text_view(older)
        self.diff_newer_text = self._text_view(newer)
        self.diff_older_text.tag_configure("removed", background="#ffd9d9", foreground="#7a0000")
        self.diff_newer_text.tag_configure(
            "changed", background="#fff1a8", foreground="#6b3b00",
            font=("TkFixedFont", 10, "bold"),
        )

    def refresh_history(self):
        self.history_list.delete(0, "end")
        self.history_paths = list_history()
        for path in self.history_paths:
            size_mb = path.stat().st_size / (1024 * 1024)
            self.history_list.insert("end", f"{path.stem}   ({size_mb:.1f} MB)")

    def load_history_selected(self):
        sel = self.history_list.curselection()
        if not sel:
            return
        if len(sel) != 1:
            messagebox.showinfo(APP_TITLE, "Select exactly one saved diagnostic to load.")
            return
        path = self.history_paths[sel[0]]
        try:
            loaded = load_snapshot(path)
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc)); return
        self.previous_snapshot = self.snapshot
        self.snapshot = loaded
        self.postgres_snapshot = loaded.get("postgresql")
        self._render(loaded)
        self._set_status(f"Loaded saved diagnostic: {path.name}")

    def compare_history_selected(self):
        selected = self.history_list.curselection()
        if len(selected) != 2:
            messagebox.showinfo(APP_TITLE, "Select exactly two saved diagnostics to compare.")
            return
        paths = [self.history_paths[index] for index in selected]
        try:
            snapshots = [(path, load_snapshot(path)) for path in paths]
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))
            return
        snapshots.sort(key=lambda item: str(item[1].get("generated_at_utc", "")))
        (previous_path, previous), (current_path, current) = snapshots
        self.previous_snapshot = previous
        self.snapshot = current
        self.postgres_snapshot = current.get("postgresql")
        self._render(current)
        self._render_diff(previous, current, previous_path.name, current_path.name)
        self.nav.select(self.diff_tab)
        self._set_status(f"Compared {previous_path.name} → {current_path.name}")

    def delete_history_selected(self):
        selected = self.history_list.curselection()
        if not selected:
            messagebox.showinfo(APP_TITLE, "Select one or more saved diagnostics to delete.")
            return
        paths = [self.history_paths[index] for index in selected]
        if not messagebox.askyesno(
            APP_TITLE,
            f"Delete {len(paths)} selected saved diagnostic(s)? This cannot be undone.",
        ):
            return
        failures = []
        for path in paths:
            try:
                path.unlink()
            except OSError as exc:
                failures.append(f"{path.name}: {exc}")
        self.refresh_history()
        if failures:
            messagebox.showerror(APP_TITLE, "Some files could not be deleted:\n" + "\n".join(failures))
        else:
            self._set_status(f"Deleted {len(paths)} saved diagnostic(s)")

    def open_history_folder(self):
        DEFAULT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        try:
            if platform.system() == "Windows":
                os.startfile(DEFAULT_HISTORY_DIR)  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(DEFAULT_HISTORY_DIR)])
            else:
                subprocess.Popen(["xdg-open", str(DEFAULT_HISTORY_DIR)])
        except OSError as exc:
            messagebox.showerror(APP_TITLE, f"Could not open history folder: {exc}")

    def run_postgres(self):
        try:
            port = int(self.pg_port.get())
        except ValueError:
            messagebox.showerror(APP_TITLE, "PostgreSQL port must be an integer."); return
        def job():
            return collect_postgres_snapshot(
                self.pg_host.get().strip() or "localhost",
                port,
                self.pg_db.get().strip() or "postgres",
                self.pg_user.get().strip() or None,
            )
        self._set_status("Checking PostgreSQL…")
        def worker():
            try:
                result = job()
                self._safe_after(lambda: self._on_postgres_success(result))
            except Exception as exc:
                self._safe_after(lambda: messagebox.showerror(APP_TITLE, str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def _on_postgres_success(self, result):
        self.postgres_snapshot = result
        self._set_text(self.postgres_text, result)
        if self.snapshot:
            try:
                save_history_snapshot(self._snapshot_for_export())
                self.refresh_history()
            except OSError:
                pass
        self._set_status("PostgreSQL check completed — included in exports")

    def _snapshot_for_export(self):
        return combine_snapshots(self.snapshot, self.postgres_snapshot)

    def export_html(self):
        if not self.snapshot:
            messagebox.showinfo(APP_TITLE, "Run or load a diagnostic first."); return
        suggested_name = snapshot_export_stem(self.snapshot) + ".html"
        path = filedialog.asksaveasfilename(
            title="Export SupportForge HTML report",
            defaultextension=".html",
            filetypes=[("HTML","*.html")],
            initialdir=str(default_export_dir()),
            initialfile=suggested_name,
        )
        if not path:
            return
        generate_html_report(self._snapshot_for_export(), Path(path), redaction="standard")
        self._set_status(f"HTML report created: {path}")

    def _safe_after(self, callback):
        if self.closing:
            return
        try:
            self.after(0, callback)
        except tk.TclError:
            pass

    def _on_close(self):
        self.closing = True
        try:
            self.progress.stop()
        except tk.TclError:
            pass
        self.destroy()

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("TkDefaultFont", 20, "bold"))
        style.configure("CardTitle.TLabel", font=("TkDefaultFont", 10, "bold"))
        style.configure("CardValue.TLabel", font=("TkDefaultFont", 17, "bold"))
        style.configure("Muted.TLabel", foreground="#666666")

    def _build_dashboard(self):
        wrap = ttk.Frame(self.dashboard_tab, padding=16)
        wrap.pack(fill="both", expand=True)

        self.health_card = self._card(wrap, "Overall Health", "Not scanned", 0, 0)
        self.platform_card = self._card(
            wrap, "Platform", current_platform().upper(), 0, 1
        )
        self.service_card = self._card(wrap, "Service Findings", "—", 0, 2)
        self.docker_card = self._card(wrap, "Docker", "—", 0, 3)

        for col in range(4):
            wrap.columnconfigure(col, weight=1)

        findings_bar = ttk.Frame(wrap)
        findings_bar.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(24, 8))
        ttk.Label(
            findings_bar, text="Findings", font=("TkDefaultFont", 13, "bold")
        ).pack(side="left")
        ttk.Label(findings_bar, text="Severity").pack(side="right", padx=(8,4))
        self.severity_filter = tk.StringVar(value="all")
        severity = ttk.Combobox(
            findings_bar, textvariable=self.severity_filter,
            values=("all","critical","warning","info"), state="readonly", width=10
        )
        severity.pack(side="right")
        severity.bind("<<ComboboxSelected>>", lambda _e: self.refresh_findings())

        self.findings = ttk.Treeview(
            wrap,
            columns=("severity", "component", "message"),
            show="headings",
            height=16,
        )
        self.findings.heading("severity", text="Severity")
        self.findings.heading("component", text="Component")
        self.findings.heading("message", text="Message")
        self.findings.column("severity", width=100, stretch=False)
        self.findings.column("component", width=140, stretch=False)
        self.findings.column("message", width=700)
        self.findings.grid(
            row=2, column=0, columnspan=4, sticky="nsew"
        )
        wrap.rowconfigure(2, weight=1)

    def _card(self, parent, title, value, row, column):
        frame = ttk.LabelFrame(parent, text=title, padding=12)
        frame.grid(row=row, column=column, sticky="nsew", padx=5, pady=5)
        label = ttk.Label(frame, text=value, style="CardValue.TLabel")
        label.pack(anchor="w")
        return label

    def _text_view(self, parent):
        frame = ttk.Frame(parent, padding=10)
        frame.pack(fill="both", expand=True)
        text = tk.Text(frame, wrap="none", font=("TkFixedFont", 10), undo=False)
        ys = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        xs = ttk.Scrollbar(frame, orient="horizontal", command=text.xview)
        text.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        text.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        return text

    def run_scan(self):
        if self.busy:
            return
        self.previous_snapshot = self.snapshot
        self._run_async("Collecting cross-platform diagnostics…", self._collect)

    def _collect(self):
        return collect_workstation_snapshot(include_docker=True)

    def _run_async(self, label, fn):
        self.busy = True
        self.scan_btn.state(["disabled"])
        self.progress.start(12)
        self._set_status(label)

        def worker():
            try:
                result = fn()
                self._safe_after(lambda: self._on_success(result))
            except Exception as exc:
                self._safe_after(lambda: self._on_error(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_success(self, snapshot):
        if self.closing:
            return
        self.snapshot = snapshot
        self._render(snapshot)
        try:
            save_history_snapshot(snapshot)
            prune_history(50)
            self.refresh_history()
        except OSError:
            pass
        self.busy = False
        self.scan_btn.state(["!disabled"])
        self.progress.stop()
        self._set_status("Completed")
        self.last_run.config(
            text="Last scan: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def _on_error(self, exc):
        if self.closing:
            return
        self.busy = False
        self.scan_btn.state(["!disabled"])
        self.progress.stop()
        self._set_status("Diagnostic failed")
        messagebox.showerror(APP_TITLE, f"{type(exc).__name__}: {exc}")

    def _render(self, snapshot):
        health = snapshot.get("health", {})
        counts = health.get("counts", {})
        self.health_card.config(text=str(health.get("state", "unknown")).upper())
        self.platform_card.config(text=str(snapshot.get("platform", "unknown")).upper())
        self.service_card.config(text=str(counts.get("warning", 0)))

        docker = snapshot.get("docker", {})
        if docker.get("installed") is False:
            docker_label = "Not installed"
        elif docker.get("available"):
            docker_label = f"{docker.get('container_count', 0)} containers"
        else:
            docker_label = "Unavailable"
        self.docker_card.config(text=docker_label)

        self.refresh_findings()

        self._set_text(self.system_text, snapshot.get("system", {}))
        self._set_text(self.network_text, snapshot.get("network", {}))
        self._set_text(self.logs_text, snapshot.get("logs", {}))
        self._set_text(self.docker_text, snapshot.get("docker", {}))
        self._set_text(self.security_text, snapshot.get("security", {}))
        if "postgresql" in snapshot:
            self.postgres_snapshot = snapshot["postgresql"]
            self._set_text(self.postgres_text, self.postgres_snapshot)
        self.refresh_evidence()

        if self.previous_snapshot:
            self._render_diff(self.previous_snapshot, snapshot)

    def refresh_findings(self):
        for row in self.findings.get_children():
            self.findings.delete(row)
        if not self.snapshot:
            return
        findings = self.snapshot.get("health", {}).get("findings", [])
        selected = self.severity_filter.get() if hasattr(self, "severity_filter") else "all"
        for finding in filter_findings(findings, selected):
            self.findings.insert(
                "", "end",
                values=(
                    str(finding.get("severity","")).upper(),
                    finding.get("component",""),
                    finding.get("message",""),
                ),
            )

    def _set_text(self, widget, value):
        widget.delete("1.0", "end")
        widget.insert("1.0", json.dumps(value, indent=2, ensure_ascii=False))

    def _render_diff(self, previous, current, previous_name="Previous scan", current_name="Current scan"):
        older, newer, changed = comparison_rows(previous, current)
        self.diff_older_label.config(text=f"Older snapshot — {previous_name}")
        self.diff_newer_label.config(text=f"Newer snapshot — {current_name} — changed values highlighted")
        self.diff_older_text.delete("1.0", "end")
        self.diff_newer_text.delete("1.0", "end")
        for path, value in older.items():
            tag = "removed" if path not in newer else None
            line = f"{path} = {value}\n"
            self.diff_older_text.insert("end", line, tag) if tag else self.diff_older_text.insert("end", line)
        for path, value in newer.items():
            tag = "changed" if path in changed else None
            prefix = "+ " if path not in older else "  "
            line = f"{prefix}{path} = {value}\n"
            self.diff_newer_text.insert("end", line, tag) if tag else self.diff_newer_text.insert("end", line)
        for path in sorted(set(older) - set(newer)):
            self.diff_newer_text.insert("end", f"- {path} = <removed>\n", "changed")

    def export_bundle(self):
        if not self.snapshot:
            messagebox.showinfo(APP_TITLE, "Run or load a diagnostic first.")
            return

        suggested_name = snapshot_export_stem(self.snapshot) + ".zip"
        target = filedialog.asksaveasfilename(
            title="Save SupportForge incident bundle",
            defaultextension=".zip",
            filetypes=[("ZIP archive", "*.zip")],
            initialdir=str(default_export_dir()),
            initialfile=suggested_name,
        )
        if not target:
            return

        bundle_stem = Path(target).stem
        temp_root = Path(tempfile.mkdtemp(prefix="supportforge-bundle-"))
        bundle_dir = temp_root / bundle_stem
        bundle_dir.mkdir(parents=True, exist_ok=True)
        snapshot = self._snapshot_for_export()
        report = bundle_dir / f"{bundle_stem}.json"
        html_report = bundle_dir / f"{bundle_stem}.html"
        try:
            save_snapshot(snapshot, report, redaction="strict")
            generate_html_report(snapshot, html_report, redaction="strict")
            result = create_bundle(bundle_dir, Path(target))
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)
        self._set_status(
            f"Bundle created: {target} | SHA-256 {result.get('bundle_sha256')}"
        )

    def _set_status(self, message):
        self.status.config(text=message)


def combine_snapshots(workstation, postgres=None):
    """Return an export snapshot containing the latest PostgreSQL check."""
    if workstation is None:
        return None
    combined = copy.deepcopy(workstation)
    if postgres is not None:
        combined["postgresql"] = copy.deepcopy(postgres)
    return combined


def comparison_rows(previous, current):
    """Flatten two snapshots into readable rows and identify changed paths."""
    older: dict[str, str] = {}
    newer: dict[str, str] = {}
    _flatten_comparison("", previous, older)
    _flatten_comparison("", current, newer)
    changed = {
        path for path in set(older) | set(newer)
        if older.get(path) != newer.get(path)
    }
    return older, newer, changed


def _flatten_comparison(path, value, rows):
    if isinstance(value, dict):
        if not value:
            rows[path or "root"] = "{}"
        for key in sorted(value):
            child = f"{path}.{key}" if path else str(key)
            _flatten_comparison(child, value[key], rows)
        return
    if isinstance(value, list):
        if not value:
            rows[path or "root"] = "[]"
        for index, item in enumerate(value):
            _flatten_comparison(f"{path}[{index}]", item, rows)
        return
    if isinstance(value, str) and len(value) > 1000:
        digest = hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:16]
        rows[path or "root"] = (
            f"<large text: {len(value)} characters, {len(value.splitlines())} lines, "
            f"sha256 {digest}…>"
        )
        return
    rows[path or "root"] = json.dumps(value, ensure_ascii=False)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="SupportForge Multi-OS diagnostic workstation")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Print the non-GUI guidance without trying to open a desktop window.",
    )
    args = parser.parse_args(argv)

    if args.headless:
        print(
            "SupportForge GUI requires an interactive desktop session. "
            "Run this in a local macOS/Linux/Windows desktop terminal or use a normal GUI VS Code window."
        )
        return 0

    try:
        app = App()
    except tk.TclError:
        print(
            "SupportForge GUI requires an interactive desktop session. "
            "Run this in a local macOS/Linux/Windows desktop terminal or use a normal GUI VS Code window."
        )
        return 0

    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
