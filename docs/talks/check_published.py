"""Verify that the Sphinx site contains each talk's linked HTML and PDF."""

import argparse
from html.parser import HTMLParser
from pathlib import Path


class TalkLinks(HTMLParser):
    """Collect the presentation links from the generated Talks page."""

    def __init__(self):
        super().__init__()
        self.links = {}

    def handle_starttag(self, tag, attrs):
        """Record attributes for links into the published talks directory."""
        attributes = dict(attrs)
        if tag == "a" and attributes.get("href", "").startswith("talks/"):
            self.links[attributes["href"]] = attributes


def verify(site: Path, *, html_only: bool = False) -> None:
    """Reject missing decks, broken links and unintended published files."""
    sources = sorted(Path(__file__).parent.glob("*/slides.qmd"))
    if not sources:
        raise ValueError("No canonical talk sources found")
    links = TalkLinks()
    links.feed((site / "talks.html").read_text(encoding="utf-8"))
    expected = set()
    for source in sources:
        for filename in (("index.html",) if html_only else ("index.html", "slides.pdf")):
            relative = f"talks/{source.parent.name}/{filename}"
            expected.add(relative)
            path = site / relative
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError(f"Missing or empty published talk: {path}")
            link = links.links.get(relative, {})
            if link.get("target") != "_blank":
                raise ValueError(f"Missing new-tab link on Talks page: {relative}")
            if not {"noopener", "noreferrer"} <= set(link.get("rel", "").split()):
                raise ValueError(f"Missing link rel attributes: {relative}")
    actual = {p.relative_to(site).as_posix() for p in (site / "talks").rglob("*") if p.is_file()}
    if actual != expected:
        raise ValueError(f"Unexpected talk publication contents: {sorted(actual ^ expected)}")
    if set(links.links) != expected:
        raise ValueError(f"Unexpected talk links: {sorted(set(links.links) ^ expected)}")
    formats = "HTML" if html_only else "HTML/PDF"
    print(f"Verified {formats} files and links for {len(sources)} talks in {site}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path, help="Sphinx HTML output directory")
    parser.add_argument("--html-only", action="store_true", help="require HTML only, without PDF files or links")
    args = parser.parse_args()
    verify(args.site, html_only=args.html_only)
