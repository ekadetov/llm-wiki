#!/usr/bin/env python3
"""Deterministic wiki lint checks: dead links, orphans, missing source refs."""

import os
import re
import sys

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def find_md_files(wiki_dir):
    files = {}
    for root, _, filenames in os.walk(wiki_dir):
        for fn in filenames:
            if fn.endswith(".md"):
                rel = os.path.relpath(os.path.join(root, fn), wiki_dir)
                slug = os.path.splitext(fn)[0]
                files[slug] = rel
    return files


def extract_links(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return WIKILINK_RE.findall(f.read())


def check_frontmatter_section(filepath, section_name):
    with open(filepath, "r", encoding="utf-8") as f:
        return section_name.lower() in f.read().lower()


def lint(wiki_dir):
    if not os.path.isdir(wiki_dir):
        print(f"Error: {wiki_dir} is not a directory", file=sys.stderr)
        return 1

    files = find_md_files(wiki_dir)
    issues = []
    inbound = {slug: set() for slug in files}

    for slug, rel in files.items():
        filepath = os.path.join(wiki_dir, rel)
        links = extract_links(filepath)

        for target in links:
            target_slug = target.strip().lower()
            matching = [s for s in files if s.lower() == target_slug]
            if not matching:
                issues.append(f"DEAD_LINK: [[{target}]] in {rel}")
            else:
                for m in matching:
                    inbound[m].add(slug)

    skip = {"index", "log"}
    for slug in files:
        if slug in skip:
            continue
        if not inbound.get(slug):
            issues.append(f"ORPHAN: {files[slug]} has no inbound links")

    for slug, rel in files.items():
        if slug in skip:
            continue
        filepath = os.path.join(wiki_dir, rel)
        if not check_frontmatter_section(filepath, "Counter-Arguments and Gaps"):
            with open(filepath, "r") as f:
                content = f.read()
            if "type: concept" in content:
                issues.append(f"MISSING_SECTION: {rel} lacks 'Counter-Arguments and Gaps'")

    if not issues:
        print("OK: No issues found")
        return 0

    for issue in sorted(issues):
        print(issue)
    print(f"\nTotal: {len(issues)} issue(s)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <wiki-directory>", file=sys.stderr)
        sys.exit(1)
    sys.exit(lint(sys.argv[1]))
