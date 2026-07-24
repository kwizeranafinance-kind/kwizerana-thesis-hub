#!/usr/bin/env python3
"""Add a standalone HTML article to the Kwizerana Thesis Hub."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
from pathlib import Path


NAV_START = "<!-- KWIZERANA_THESIS_NAV_START -->"
NAV_END = "<!-- KWIZERANA_THESIS_NAV_END -->"


def extract_title(raw: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", raw, flags=re.I | re.S)
    if not match:
        return "Untitled Kwizerana Thesis"
    return html.unescape(re.sub(r"\s+", " ", match.group(1))).split("|")[0].strip()


def clean_text(raw: str) -> str:
    raw = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style\b[^>]*>.*?</style>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def extract_summary(raw: str) -> str:
    meta = re.search(
        r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"'](.*?)[\"']",
        raw,
        flags=re.I | re.S,
    )
    if meta:
        return clean_text(meta.group(1))

    for class_name in ("sub", "lede"):
        match = re.search(
            rf"<p[^>]+class=[\"'][^\"']*\b{class_name}\b[^\"']*[\"'][^>]*>(.*?)</p>",
            raw,
            flags=re.I | re.S,
        )
        if match:
            return clean_text(match.group(1))

    paragraph = re.search(r"<p\b[^>]*>(.*?)</p>", raw, flags=re.I | re.S)
    if paragraph:
        return clean_text(paragraph.group(1))

    return "Read the full Kwizerana thesis in the archive."


def date_label(date_iso: str) -> str:
    try:
        value = dt.date.fromisoformat(date_iso)
    except ValueError:
        return date_iso
    return f"{value.strftime('%B')} {value.day}, {value.year}"


def inject_nav(raw: str, root_prefix: str) -> str:
    raw = re.sub(rf"\s*{re.escape(NAV_START)}.*?{re.escape(NAV_END)}\s*", "\n", raw, flags=re.S)
    nav = f"""
{NAV_START}
<div style="position:sticky;top:0;z-index:9999;background:#FBF9FF;border-bottom:1px solid rgba(101,45,144,.16);font-family:Instrument Sans,Arial,Helvetica,sans-serif;">
  <div style="max-width:1120px;margin:0 auto;padding:10px 24px;display:flex;gap:14px;align-items:center;justify-content:space-between;color:#5B4C6B;font-size:13px;">
    <a href="{root_prefix}" style="color:#190B24;text-decoration:none;font-weight:800;letter-spacing:.12em;text-transform:uppercase;">Kwizerana Thesis Hub</a>
    <span style="display:flex;gap:12px;align-items:center;">
      <a href="{root_prefix}" style="color:#652D90;text-decoration:none;font-weight:800;">Latest</a>
      <a href="{root_prefix}archive/" style="color:#5B4C6B;text-decoration:none;">Archive</a>
    </span>
  </div>
</div>
{NAV_END}
"""
    body = re.search(r"<body\b[^>]*>", raw, flags=re.I)
    if body:
        return raw[: body.end()] + nav + raw[body.end() :]
    return nav + raw


def write_manifest(repo_root: Path, entries: list[dict[str, str]]) -> None:
    archive = repo_root / "archive"
    archive.mkdir(exist_ok=True)
    (archive / "manifest.json").write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def load_manifest(repo_root: Path) -> list[dict[str, str]]:
    manifest = repo_root / "archive" / "manifest.json"
    if not manifest.exists():
        return []
    return json.loads(manifest.read_text(encoding="utf-8"))


def root_href(entry: dict[str, str]) -> str:
    return f"articles/{entry['slug']}/"


def archive_href(entry: dict[str, str]) -> str:
    return f"../articles/{entry['slug']}/"


def render_archive_items(entries: list[dict[str, str]], href_builder) -> str:
    return "\n".join(
        f"""        <a class="archive-item" href="{href_builder(entry)}">
          <span class="date">{html.escape(entry.get('label') or date_label(entry['date']))}</span>
          <strong>{html.escape(entry['title'])}</strong>
          <span class="type">{html.escape(entry.get('topic', 'Thesis'))}</span>
        </a>"""
        for entry in entries
    )


def render_home(entries: list[dict[str, str]]) -> str:
    latest = entries[0]
    archive_items = render_archive_items(entries, root_href)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kwizerana Thesis Hub</title>
<meta name="description" content="A living archive of Kwizerana theses, briefs, and special reports.">
<style>
:root {{
  --paper: oklch(98% 0.012 306);
  --mist: oklch(94% 0.028 304);
  --ink: oklch(20% 0.045 307);
  --soft: oklch(43% 0.045 303);
  --line: oklch(82% 0.045 303);
  --plum: oklch(31% 0.12 313);
  --violet: oklch(46% 0.17 309);
  --ember: oklch(62% 0.15 43);
  --green: oklch(61% 0.12 157);
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background:
    linear-gradient(180deg, oklch(95% 0.035 306), var(--paper) 360px),
    var(--paper);
  color: var(--ink);
  font-family: "Instrument Sans", Arial, Helvetica, sans-serif;
}}
a {{ color: inherit; }}
.nav {{
  border-bottom: 1px solid color-mix(in oklch, var(--line), transparent 40%);
  background: color-mix(in oklch, var(--paper), transparent 8%);
  position: sticky;
  top: 0;
  z-index: 20;
}}
.nav-inner {{
  width: min(1120px, calc(100% - 36px));
  min-height: 60px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}}
.brand {{
  color: var(--plum);
  text-decoration: none;
  font-weight: 900;
  letter-spacing: .16em;
  text-transform: uppercase;
  font-size: 13px;
}}
.nav-links {{ display: flex; align-items: center; gap: 16px; }}
.nav-links a {{
  color: var(--soft);
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
}}
.nav-links a:first-child {{ color: var(--violet); }}
main {{ width: min(1120px, calc(100% - 36px)); margin: 0 auto; }}
.hero {{
  padding: 78px 0 44px;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(280px, .72fr);
  gap: 48px;
  align-items: end;
}}
.eyebrow {{
  color: var(--ember);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .22em;
  text-transform: uppercase;
}}
h1 {{
  margin: 16px 0;
  max-width: 760px;
  font-size: clamp(44px, 8vw, 92px);
  line-height: .9;
  letter-spacing: 0;
}}
.dek {{
  max-width: 66ch;
  color: var(--soft);
  font-size: 18px;
  line-height: 1.7;
  margin: 0;
}}
.signal {{
  border: 1px solid var(--line);
  background: color-mix(in oklch, var(--mist), transparent 18%);
  border-radius: 8px;
  padding: 22px;
}}
.signal span {{
  color: var(--violet);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .15em;
  text-transform: uppercase;
}}
.signal p {{
  margin: 14px 0 0;
  color: var(--soft);
  line-height: 1.65;
}}
.featured {{ padding: 24px 0 70px; }}
.section-label {{
  margin: 0 0 14px;
  color: var(--plum);
  font-size: 13px;
  font-weight: 900;
  letter-spacing: .16em;
  text-transform: uppercase;
}}
.feature-link {{
  display: grid;
  grid-template-columns: minmax(0, 1fr) 190px;
  gap: 26px;
  min-height: 260px;
  padding: 30px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: oklch(97% 0.018 306);
  text-decoration: none;
}}
.feature-link:hover {{ border-color: color-mix(in oklch, var(--violet), var(--line)); }}
.topic {{
  display: inline-flex;
  align-items: center;
  color: var(--ember);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .14em;
  text-transform: uppercase;
}}
.feature-link h2 {{
  margin: 18px 0 14px;
  max-width: 760px;
  color: var(--plum);
  font-size: clamp(28px, 4vw, 52px);
  line-height: 1.02;
}}
.feature-link p {{
  max-width: 70ch;
  margin: 0;
  color: var(--soft);
  line-height: 1.7;
}}
.meta {{
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: var(--soft);
  font-size: 13px;
  line-height: 1.6;
}}
.cta {{ color: var(--violet); font-weight: 900; }}
.archive {{ padding: 0 0 76px; }}
.archive-list {{ display: grid; gap: 12px; }}
.archive-item {{
  display: grid;
  grid-template-columns: 170px minmax(0, 1fr) 140px;
  gap: 18px;
  align-items: center;
  padding: 18px 0;
  border-top: 1px solid var(--line);
  text-decoration: none;
}}
.archive-item:last-child {{ border-bottom: 1px solid var(--line); }}
.date, .type {{
  color: var(--soft);
  font-size: 13px;
}}
.archive-item strong {{
  color: var(--ink);
  font-size: 18px;
  line-height: 1.35;
}}
.type {{ text-align: right; color: var(--green); font-weight: 800; }}
footer {{
  width: min(1120px, calc(100% - 36px));
  margin: 0 auto;
  padding: 36px 0 58px;
  border-top: 1px solid var(--line);
  color: var(--soft);
  font-size: 13px;
}}
@media (max-width: 780px) {{
  .hero, .feature-link {{ grid-template-columns: 1fr; }}
  .archive-item {{ grid-template-columns: 1fr; gap: 6px; }}
  .type {{ text-align: left; }}
}}
</style>
</head>
<body>
  <nav class="nav">
    <div class="nav-inner">
      <a class="brand" href="./">Kwizerana Thesis Hub</a>
      <div class="nav-links">
        <a href="./">Latest</a>
        <a href="archive/">Archive</a>
      </div>
    </div>
  </nav>
  <main>
    <section class="hero">
      <div>
        <div class="eyebrow">Thesis Archive</div>
        <h1>Research notes with a spine.</h1>
        <p class="dek">A living shelf for Kwizerana thesis work: market reads, company briefs, protocol memos, and special reports that deserve a permanent home.</p>
      </div>
      <aside class="signal">
        <span>Editorial Rule</span>
        <p>Each thesis gets its own URL, the latest piece gets front-page weight, and the archive stays readable as the body of work compounds.</p>
      </aside>
    </section>
    <section class="featured">
      <p class="section-label">Latest Thesis</p>
      <a class="feature-link" href="{root_href(latest)}">
        <div>
          <span class="topic">{html.escape(latest.get('topic', 'Thesis'))}</span>
          <h2>{html.escape(latest['title'])}</h2>
          <p>{html.escape(latest.get('summary', 'Read the full Kwizerana thesis in the archive.'))}</p>
        </div>
        <div class="meta">
          <span>{html.escape(latest.get('label') or date_label(latest['date']))}</span>
          <span class="cta">Read thesis</span>
        </div>
      </a>
    </section>
    <section class="archive">
      <p class="section-label">Archive</p>
      <div class="archive-list">
{archive_items}
      </div>
    </section>
  </main>
  <footer>Kwizerana Thesis Hub. Built for permanent article URLs and a clean public archive.</footer>
</body>
</html>
"""


def render_archive(entries: list[dict[str, str]]) -> str:
    archive_items = render_archive_items(entries, archive_href)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kwizerana Thesis Archive</title>
<meta name="description" content="Archive of Kwizerana thesis articles and special reports.">
<style>
:root {{
  --paper: oklch(98% 0.012 306);
  --mist: oklch(94% 0.028 304);
  --ink: oklch(20% 0.045 307);
  --soft: oklch(43% 0.045 303);
  --line: oklch(82% 0.045 303);
  --plum: oklch(31% 0.12 313);
  --violet: oklch(46% 0.17 309);
  --ember: oklch(62% 0.15 43);
  --green: oklch(61% 0.12 157);
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: "Instrument Sans", Arial, Helvetica, sans-serif;
}}
.nav {{
  border-bottom: 1px solid color-mix(in oklch, var(--line), transparent 40%);
  background: var(--paper);
}}
.nav-inner, main, footer {{
  width: min(1120px, calc(100% - 36px));
  margin: 0 auto;
}}
.nav-inner {{
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}}
.brand {{
  color: var(--plum);
  text-decoration: none;
  font-weight: 900;
  letter-spacing: .16em;
  text-transform: uppercase;
  font-size: 13px;
}}
.nav-links {{ display: flex; gap: 16px; }}
.nav-links a {{
  color: var(--soft);
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
}}
.nav-links a:last-child {{ color: var(--violet); }}
.hero {{ padding: 72px 0 34px; }}
.eyebrow {{
  color: var(--ember);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .22em;
  text-transform: uppercase;
}}
h1 {{
  margin: 14px 0 12px;
  max-width: 820px;
  font-size: clamp(42px, 7vw, 84px);
  line-height: .94;
}}
.dek {{
  max-width: 68ch;
  color: var(--soft);
  font-size: 18px;
  line-height: 1.7;
}}
.archive-list {{
  padding: 24px 0 80px;
  display: grid;
  gap: 12px;
}}
.archive-item {{
  display: grid;
  grid-template-columns: 170px minmax(0, 1fr) 140px;
  gap: 18px;
  align-items: center;
  padding: 18px 0;
  border-top: 1px solid var(--line);
  color: inherit;
  text-decoration: none;
}}
.archive-item:last-child {{ border-bottom: 1px solid var(--line); }}
.date, .type {{ color: var(--soft); font-size: 13px; }}
.archive-item strong {{ color: var(--ink); font-size: 18px; line-height: 1.35; }}
.type {{ color: var(--green); font-weight: 800; text-align: right; }}
footer {{
  padding: 34px 0 56px;
  border-top: 1px solid var(--line);
  color: var(--soft);
  font-size: 13px;
}}
@media (max-width: 760px) {{
  .archive-item {{ grid-template-columns: 1fr; gap: 6px; }}
  .type {{ text-align: left; }}
}}
</style>
</head>
<body>
  <nav class="nav">
    <div class="nav-inner">
      <a class="brand" href="../">Kwizerana Thesis Hub</a>
      <div class="nav-links">
        <a href="../">Latest</a>
        <a href="./">Archive</a>
      </div>
    </div>
  </nav>
  <main>
    <section class="hero">
      <div class="eyebrow">Article Archive</div>
      <h1>Every thesis, preserved.</h1>
      <p class="dek">A chronological archive for Kwizerana company reads, protocol theses, market structure notes, and special reports.</p>
    </section>
    <section class="archive-list">
{archive_items}
    </section>
  </main>
  <footer>Kwizerana Thesis Hub archive.</footer>
</body>
</html>
"""


def rebuild_pages(repo_root: Path, entries: list[dict[str, str]]) -> None:
    if not entries:
        return
    (repo_root / "index.html").write_text(render_home(entries), encoding="utf-8")
    archive_dir = repo_root / "archive"
    archive_dir.mkdir(exist_ok=True)
    (archive_dir / "index.html").write_text(render_archive(entries), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--topic", default="Thesis")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    raw = args.source.read_text(encoding="utf-8", errors="replace")
    title = extract_title(raw)
    summary = extract_summary(raw)

    article_dir = repo_root / "articles" / args.slug
    article_dir.mkdir(parents=True, exist_ok=True)
    (article_dir / "index.html").write_text(inject_nav(raw, "../../"), encoding="utf-8")

    entries = [entry for entry in load_manifest(repo_root) if entry.get("slug") != args.slug]
    entries.insert(
        0,
        {
            "date": args.date,
            "label": date_label(args.date),
            "title": title,
            "summary": summary,
            "topic": args.topic,
            "slug": args.slug,
            "url": f"../articles/{args.slug}/",
        }
    )
    entries.sort(key=lambda entry: entry["date"], reverse=True)
    write_manifest(repo_root, entries)
    rebuild_pages(repo_root, entries)

    print(f"Published article: {title}")
    print(f"Slug: {args.slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
