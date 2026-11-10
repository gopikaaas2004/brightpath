#!/usr/bin/env python3
"""
Rebrand the website by swapping one set of brand details for another.

Usage (from the project folder):
    python3 tools/rebrand.py            # applies brand.json to every page

How it works:
    brand.json            -> the brand you WANT (edit this file)
    tools/.applied.json   -> the brand currently in the pages (don't edit)

The script replaces every "applied" value with the matching "wanted" value
in all .html/.css/.js files, then records brand.json as the new applied state.
Run it as many times as you like.
"""
import json
import pathlib
import re
import sys

FIELDS = [
    # order matters: longer / more specific strings first
    "legal_name", "email", "domain", "phone", "address",
    "tracking_prefix", "name_upper", "name", "slug",
]


def derive(b):
    b = dict(b)
    b.setdefault("name_upper", b["name"].upper())
    b.setdefault("slug", re.sub(r"[^a-z0-9]+", "-", b["name"].lower()).strip("-"))
    return b


def rebrand_text(text, old, new):
    # 1. logo: Old<span class="dot" ...>part2</span>
    logo_re = re.compile(
        re.escape(old["logo_part1"]) + r'(<span class="dot"[^>]*>)' + re.escape(old["logo_part2"]) + r"</span>"
    )
    text = logo_re.sub(lambda m: "\x00LOGO1\x00" + m.group(1) + "\x00LOGO2\x00</span>", text)
    # 2. plain fields via placeholder tokens (safe even if new contains old)
    for i, f in enumerate(FIELDS):
        if old.get(f) and old[f] != new.get(f):
            text = text.replace(old[f], f"\x00F{i}\x00")
    for i, f in enumerate(FIELDS):
        text = text.replace(f"\x00F{i}\x00", new[f])
    return text.replace("\x00LOGO1\x00", new["logo_part1"]).replace("\x00LOGO2\x00", new["logo_part2"])


def main(root):
    root = pathlib.Path(root)
    applied_path = root / "tools" / ".applied.json"
    new = derive(json.loads((root / "brand.json").read_text()))
    old = derive(json.loads(applied_path.read_text()))
    changed = 0
    for p in root.rglob("*"):
        if p.suffix not in {".html", ".css", ".js"} or "tools" in p.parts or p.name.endswith(".min.js") or p.name.endswith(".min.css"):
            continue
        t = p.read_text(encoding="utf-8")
        nt = rebrand_text(t, old, new)
        if nt != t:
            p.write_text(nt, encoding="utf-8")
            changed += 1
    applied_path.write_text((root / "brand.json").read_text())
    print(f"Rebranded {changed} files: {old['name']} -> {new['name']}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent)
