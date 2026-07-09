#!/usr/bin/env python3
"""Gather PX4 docs text and optional local codebase evidence."""

from __future__ import annotations

import argparse
import html
import os
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


DEFAULT_INCLUDE_DIRS = ("docs/en", "boards", "cmake", "Tools")


class DocHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._link_text: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        attrs_dict = dict(attrs)
        if tag in {"h1", "h2", "h3"}:
            self.parts.append("\n")
        elif tag in {"p", "div", "section", "article", "li", "tr", "pre", "blockquote"}:
            self.parts.append("\n")
        elif tag == "br":
            self.parts.append("\n")
        elif tag == "a":
            self._href = attrs_dict.get("href")
            self._link_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == "a" and self._href:
            text = clean_text(" ".join(self._link_text))
            if text:
                self.links.append((text, self._href))
            self._href = None
            self._link_text = []
        elif tag in {"h1", "h2", "h3", "p", "li", "pre"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._href:
            self._link_text.append(data)
        self.parts.append(data)


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def repo_root(start: Path) -> Path:
    current = start.resolve()
    for path in (current, *current.parents):
        if (path / ".git").exists() or (path / "boards").exists():
            return path
    return current


def local_doc_for_url(url: str, root: Path) -> Path | None:
    parsed = urlparse(url)
    if parsed.netloc != "docs.px4.io":
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        return None
    # docs.px4.io/main/en/hardware/file.html -> docs/en/hardware/file.md
    if parts[1] != "en":
        return None
    rel_parts = ["docs", "en", *parts[2:]]
    if not rel_parts[-1].endswith(".md"):
        rel_parts[-1] = rel_parts[-1].removesuffix(".html") + ".md"
    path = root.joinpath(*rel_parts)
    return path if path.exists() else None


def fetch_url(url: str) -> tuple[str, list[tuple[str, str]]]:
    request = Request(url, headers={"User-Agent": "px4-docs-answer/1.0"})
    with urlopen(request, timeout=20) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
    parser = DocHTMLParser()
    parser.feed(raw.decode(charset, errors="replace"))
    return clean_text("\n".join(parser.parts)), parser.links


def markdown_links(text: str) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
        label = clean_text(match.group(1))
        href = match.group(2).strip()
        if label and href and not href.startswith("#"):
            links.append((label, href))
    for match in re.finditer(r"^\s*\[([^\]]+)\]:\s*(\S+)", text, re.MULTILINE):
        label = clean_text(match.group(1))
        href = match.group(2).strip()
        if label and href and not href.startswith("#"):
            links.append((label, href))
    for match in re.finditer(r"<a\s+[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", text, re.I | re.S):
        href = match.group(1).strip()
        label = clean_text(re.sub(r"<[^>]+>", " ", match.group(2)))
        if label and href and not href.startswith("#"):
            links.append((label, href))
    return links


def read_doc(source: str, root: Path, prefer_local: bool) -> tuple[str, str, list[tuple[str, str]]]:
    if prefer_local:
        local = local_doc_for_url(source, root)
        if local:
            text = local.read_text(encoding="utf-8")
            return text, str(local), markdown_links(text)

    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"}:
        text, links = fetch_url(source)
        return text, source, links

    path = Path(source)
    if not path.is_absolute():
        path = root / path
    text = path.read_text(encoding="utf-8")
    return text, str(path), markdown_links(text)


def in_crawl_scope(base_url: str, candidate: str, scope: str) -> bool:
    base = urlparse(base_url)
    cand = urlparse(candidate)
    if scope == "any":
        return True
    if cand.netloc and cand.netloc != base.netloc:
        return False
    if scope == "same-host":
        return True
    base_parts = [p for p in base.path.split("/") if p]
    cand_parts = [p for p in cand.path.split("/") if p]
    if scope == "section":
        return len(cand_parts) >= 3 and cand_parts[:3] == base_parts[:3]
    # For docs.px4.io/main/en/... follow all pages in the same docs version and language.
    if scope == "docs-site":
        return len(base_parts) >= 2 and len(cand_parts) >= 2 and cand_parts[:2] == base_parts[:2]
    raise ValueError(f"unknown crawl scope: {scope}")


def canonical_source(source: str) -> str:
    parsed = urlparse(source)
    if parsed.scheme not in {"http", "https"}:
        return str(Path(source).resolve()) if os.path.exists(source) else source
    path = parsed.path.rstrip("/")
    path = path.removesuffix(".html").removesuffix(".md")
    return parsed._replace(path=path, fragment="", query="").geturl()


def score_link(query: str, label: str, url: str) -> int:
    if not query:
        return 0
    haystack = f"{label} {url}".lower()
    terms = [term for term in re.split(r"\W+", query.lower()) if len(term) > 2]
    return sum(1 for term in terms if term in haystack)


def crawl_urls(seed: str, links: list[tuple[str, str]], max_pages: int, query: str, scope: str) -> list[str]:
    ranked_links = sorted(
        links,
        key=lambda item: score_link(query, item[0], item[1]),
        reverse=True,
    )
    urls: list[str] = []
    seen = {canonical_source(seed)}
    for _text, href in ranked_links:
        absolute = urljoin(seed, href).split("#", 1)[0]
        canonical = canonical_source(absolute)
        if canonical in seen or not in_crawl_scope(seed, absolute, scope):
            continue
        seen.add(canonical)
        urls.append(absolute)
        if len(urls) >= max_pages:
            break
    return urls


def print_doc(source_label: str, text: str, limit: int) -> None:
    print(f"\n## Documentation: {source_label}\n")
    print(text[:limit].rstrip())
    if len(text) > limit:
        print(f"\n[truncated to {limit} characters]")


def run_rg(root: Path, query: str, includes: list[str], limit: int) -> None:
    cmd = ["rg", "-n", "-S", "--glob", "!build/**", query, *includes]
    print(f"\n## Codebase search: {query}\n")
    try:
        result = subprocess.run(
            cmd,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError:
        print("rg is not installed; run the search manually with grep or install ripgrep.")
        return
    output = result.stdout.strip() or result.stderr.strip() or "(no matches)"
    print(output[:limit])
    if len(output) > limit:
        print(f"\n[truncated to {limit} characters]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", help="Docs URLs or local documentation files")
    parser.add_argument("--repo", default=".", help="PX4-Autopilot checkout root or subdirectory")
    parser.add_argument("--no-prefer-local", action="store_true", help="Always fetch URLs instead of using local docs/en files")
    parser.add_argument("--crawl-depth", type=int, default=0, help="Follow same docs-area links this many levels")
    parser.add_argument(
        "--crawl-scope",
        choices=("section", "docs-site", "same-host", "any"),
        default="docs-site",
        help="Which links may be followed during recursive crawl",
    )
    parser.add_argument("--max-pages", type=int, default=6, help="Maximum additional pages to crawl")
    parser.add_argument("--query", default="", help="User question or keywords used to prioritize links while crawling")
    parser.add_argument("--doc-limit", type=int, default=12000, help="Characters to print per documentation page")
    parser.add_argument("--code-limit", type=int, default=12000, help="Characters to print per codebase query")
    parser.add_argument("--codebase-query", action="append", default=[], help="Run rg for this query in the checkout")
    parser.add_argument("--include", action="append", default=[], help="Directory or glob to include in rg searches")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root(Path(args.repo))
    prefer_local = not args.no_prefer_local
    include_paths = args.include or list(DEFAULT_INCLUDE_DIRS)

    queue: list[tuple[str, int]] = [(source, 0) for source in args.sources]
    seen: set[str] = set()
    crawled = 0

    while queue:
        source, depth = queue.pop(0)
        canonical = canonical_source(source)
        if canonical in seen:
            continue
        seen.add(canonical)
        try:
            text, label, links = read_doc(source, root, prefer_local)
        except Exception as exc:  # noqa: BLE001 - useful for support workflow output
            print(f"\n## Documentation: {source}\n\nERROR: {exc}", file=sys.stderr)
            continue
        print_doc(label, text, args.doc_limit)
        if depth < args.crawl_depth and urlparse(source).scheme in {"http", "https"} and crawled < args.max_pages:
            for url in crawl_urls(source, links, args.max_pages - crawled, args.query, args.crawl_scope):
                queue.append((url, depth + 1))
                crawled += 1

    for query in args.codebase_query:
        run_rg(root, query, include_paths, args.code_limit)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
