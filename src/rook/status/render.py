"""HTML rendering for status reports."""

import html
from typing import Any
from urllib.parse import urlsplit


def render_html(report: dict[str, Any]) -> str:
    """Render the report model as a compact, standalone HTML overview."""
    rows = []
    for check in report["checks"]:
        details = ", ".join(
            f"{key.replace('_', ' ')}: {value}"
            for key, value in check.get("details", {}).items()
        )
        rows.append(
            "<tr>"
            f'<td><span class="state {html.escape(check["state"])}">'
            f'{html.escape(check["state"].upper())}</span></td>'
            f'<th scope="row">{html.escape(check["id"])}</th>'
            f'<td>{html.escape(check["message"])}</td>'
            f"<td>{html.escape(details)}</td>"
            "</tr>"
        )

    title = f'Rook {report["service"]["version"]} status'
    overall_state = html.escape(report["state"])
    measured_at = html.escape(report["measured_at"])
    schema_version = html.escape(report["schema_version"])
    identification = _render_identification(report["service"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
body {{
  color: #17202a; font: 16px system-ui, sans-serif; margin: 2rem auto;
  max-width: 75rem; padding: 0 1rem;
}}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{
  border-bottom: 1px solid #d5d8dc; padding: .65rem; text-align: left;
  vertical-align: top;
}}
.state {{
  border-radius: .3rem; color: white; display: inline-block; font-size: .75rem;
  font-weight: 700; padding: .2rem .45rem;
}}
.green {{ background: #18794e; }}
.yellow {{ background: #946800; }}
.red {{ background: #b42318; }}
small {{ color: #566573; }}
dl {{ display: grid; gap: .35rem 1rem; grid-template-columns: max-content 1fr; }}
dt {{ font-weight: 700; }}
dd {{ margin: 0; }}
</style>
</head>
<body>
<h1>{html.escape(title)}</h1>
<p>Overall state:
<span class="state {overall_state}">{overall_state.upper()}</span></p>
<p><small>Measured at {measured_at}; schema {schema_version}</small></p>
{identification}
<h2>Checks</h2>
<table><thead><tr>
<th>State</th><th>Check</th><th>Message</th><th>Details</th>
</tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</body>
</html>"""


def _render_identification(service):
    provider = service.get("provider", {})
    contact = service.get("contact", {})
    fields = (
        ("Provider", provider.get("name")),
        ("Provider URL", provider.get("url")),
        ("Contact", contact.get("name")),
        ("City", contact.get("city")),
        ("Country", contact.get("country")),
        ("Contact URL", contact.get("url")),
    )
    items = "".join(
        f"<dt>{html.escape(label)}</dt><dd>{_render_value(value)}</dd>"
        for label, value in fields
        if value
    )
    if not items:
        return ""
    return f"<h2>Service identification</h2><dl>{items}</dl>"


def _render_value(value):
    text = str(value)
    escaped = html.escape(text, quote=True)
    try:
        scheme = urlsplit(text).scheme
    except ValueError:
        scheme = ""
    if scheme in {"http", "https"}:
        return f'<a href="{escaped}">{escaped}</a>'
    return escaped
