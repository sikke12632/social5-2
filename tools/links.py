# -*- coding: utf-8 -*-
"""빌드된 사이트의 모든 링크와 이미지가 실제로 있는지 확인한다.

    python tools/links.py
"""

import pathlib
import sys
from urllib.parse import unquote

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dom import parse  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP = ("http://", "https://", "mailto:", "#")


def main():
    pages = [p for p in sorted(ROOT.rglob("*.html"))
             if "tools" not in p.parts and "BACKUP" not in str(p)]
    bad, checked = [], 0
    for page in pages:
        doc = parse(page.read_text(encoding="utf-8"))
        refs = [(a.attrs.get("href", ""), "링크") for a in doc.find_all("a")]
        refs += [(i.attrs.get("src", ""), "사진") for i in doc.find_all("img")]
        for href, kind in refs:
            if not href or href.startswith(SKIP):
                continue
            checked += 1
            target = (page.parent / unquote(href.split("#")[0])).resolve()
            if not target.exists():
                bad.append((page.relative_to(ROOT), kind, href))
    for p, kind, href in bad:
        print("  깨짐  %-22s %s  %s" % (p, kind, href))
    print("페이지 %d개 · 링크·사진 %d개 검사 · 깨진 것 %d개"
          % (len(pages), checked, len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
