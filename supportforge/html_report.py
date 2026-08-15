from __future__ import annotations
import html, json
from pathlib import Path
from typing import Any
from .redaction import redact_payload

def generate_html_report(snapshot: dict[str, Any], output: Path, redaction: str = "standard") -> Path:
    safe = redact_payload(snapshot, redaction)
    health = safe.get("health", {})
    findings = health.get("findings", [])
    counts = health.get("counts", {})

    finding_rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            _h(f.get("severity","")), _h(f.get("component","")), _h(f.get("message",""))
        ) for f in findings
    ) or '<tr><td colspan="3">No findings recorded.</td></tr>'

    system = safe.get("system", {})
    sys_rows = "".join(
        f"<tr><th>{_h(k)}</th><td>{_h(v)}</td></tr>"
        for k, v in system.items()
    )

    sections = []
    for key, title in (
        ("network","Network"),
        ("storage","Storage"),
        ("docker","Docker"),
        ("security","Security"),
        ("postgresql","PostgreSQL"),
        ("logs","Logs"),
    ):
        sections.append(
            f"<details><summary>{title}</summary><pre>{_json(safe.get(key, {}))}</pre></details>"
        )

    doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>SupportForge MultiOS Incident Report</title>
<style>
:root{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color-scheme:light dark}}
body{{max-width:1200px;margin:32px auto;padding:0 22px;line-height:1.45}}
.cards{{display:grid;grid-template-columns:repeat(4,minmax(120px,1fr));gap:12px}}
.card{{border:1px solid #8886;border-radius:10px;padding:14px}}
.card strong{{display:block;font-size:1.5rem;margin-top:5px}}
table{{border-collapse:collapse;width:100%;margin:12px 0}}
td,th{{border:1px solid #8886;padding:8px;text-align:left;vertical-align:top}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;padding:14px;border:1px solid #8885;border-radius:8px}}
details{{margin:10px 0}} summary{{font-weight:700;cursor:pointer}}
.meta{{opacity:.75}} .foot{{margin-top:30px;opacity:.7;font-size:.9rem}}
</style></head><body>
<h1>SupportForge MultiOS Incident Report</h1>
<p class="meta">Schema: {_h(safe.get("schema",""))}<br>
Generated: {_h(safe.get("generated_at_utc",""))}<br>
Platform: {_h(safe.get("platform",""))}</p>

<div class="cards">
<div class="card">Health<strong>{_h(str(health.get("state","unknown")).upper())}</strong></div>
<div class="card">Critical<strong>{_h(counts.get("critical",0))}</strong></div>
<div class="card">Warnings<strong>{_h(counts.get("warning",0))}</strong></div>
<div class="card">Info<strong>{_h(counts.get("info",0))}</strong></div>
</div>

<h2>Findings</h2>
<table><thead><tr><th>Severity</th><th>Component</th><th>Finding</th></tr></thead>
<tbody>{finding_rows}</tbody></table>

<h2>System</h2><table>{sys_rows}</table>
<h2>Evidence</h2>{''.join(sections)}
<p class="foot">Generated locally by SupportForge MultiOS. Export redaction profile: {_h(redaction)}.</p>
</body></html>"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(doc, encoding="utf-8")
    return output

def _h(value: Any) -> str:
    return html.escape(str(value))

def _json(value: Any) -> str:
    return html.escape(json.dumps(value, indent=2, ensure_ascii=False))
