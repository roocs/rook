"""HTML rendering for status reports."""

import html
from typing import Any


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
</style>
</head>
<body>
<h1>{html.escape(title)}</h1>
<p>Overall state:
<span class="state {overall_state}">{overall_state.upper()}</span></p>
<p><small>Measured at {measured_at}; schema {schema_version}</small></p>
<table><thead><tr>
<th>State</th><th>Check</th><th>Message</th><th>Details</th>
</tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</body>
</html>"""
