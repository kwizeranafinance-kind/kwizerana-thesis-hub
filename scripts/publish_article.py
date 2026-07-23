#!/usr/bin/env python3
"""Add a standalone HTML article to the Kwizerana Thesis Hub."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path


NAV_START = "<!-- KWIZERANA_THESIS_NAV_START -->"
NAV_END = "<!-- KWIZERANA_THESIS_NAV_END -->"


def extract_title(raw: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", raw, flags=re.I | re.S)
    if not match:
        return "Untitled Kwizerana Thesis"
    return html.unescape(re.sub(r"\s+", " ", match.group(1))).split("|")[0].strip()


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

    article_dir = repo_root / "articles" / args.slug
    article_dir.mkdir(parents=True, exist_ok=True)
    (article_dir / "index.html").write_text(inject_nav(raw, "../../"), encoding="utf-8")

    entries = [entry for entry in load_manifest(repo_root) if entry.get("slug") != args.slug]
    entries.append(
        {
            "date": args.date,
            "label": args.date,
            "title": title,
            "topic": args.topic,
            "slug": args.slug,
            "url": f"../articles/{args.slug}/",
        }
    )
    entries.sort(key=lambda entry: entry["date"], reverse=True)
    write_manifest(repo_root, entries)

    print(f"Published article: {title}")
    print(f"Slug: {args.slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
