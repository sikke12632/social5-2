# -*- coding: utf-8 -*-
"""원본 HTML과 (JSON→새 HTML) 을 내용만 뽑아 대조한다.

    python tools/verify.py

디자인·구조는 달라져도 되지만 **글자와 정답은 하나도 달라지면 안 된다.**
카드 앞뒷면, 문항, 보기, 정답 위치, 사진 파일명까지 전부 본다.
하나라도 어긋나면 실패하고 어디가 다른지 찍는다.
"""

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dom import parse, squash  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
OLD = ROOT / "tools" / "_original"
NEW = ROOT


def fingerprint(html_text):
    """페이지에서 '내용'만 뽑아 순서대로 늘어놓는다."""
    doc = parse(html_text)
    # 새 페이지는 <main> 안이 본문이다. 좌측 목차는 대조 대상이 아니다.
    root = doc.first("main") or doc.first("div", "wrap")
    out = []

    h1 = root.first("h1")
    if h1:
        out.append(("제목", squash(h1.text())))

    for eb in root.find_all("div", "eyebrow"):
        out.append(("머리말", squash(eb.text())))

    for sec in root.find_all("h2", "sec"):
        out.append(("섹션", squash(sec.text())))

    for lead in root.find_all("p", "lead"):
        t = squash(lead.text())
        if t:
            out.append(("안내", t))

    for c in root.find_all(cls="card"):
        tag = c.first("div", "tag")
        a = c.first("div", "a")
        out.append(("카드앞", squash(c.first("div", "q").text())))
        if tag:
            out.append(("카드표", squash(tag.text())))
        if a:
            out.append(("카드뒤", squash(a.text())))

    for img in root.find_all("img"):
        out.append(("사진", re.sub(r"^\.\./", "", img.attrs.get("src", ""))))

    for q in root.find_all(cls="quiz"):
        out.append(("문항", squash(q.first("div", "qtext").text())))
        out.append(("문항번호", q.attrs.get("data-qid", "")))
        for o in q.find_all("button", "opt"):
            out.append(("보기%s" % o.attrs.get("data-a", "0"), squash(o.text())))

    for cl in root.find_all("div", "closing"):
        out.append(("맺음말", squash(cl.text())))

    return out


def compare(name, old_html, new_html):
    a, b = fingerprint(old_html), fingerprint(new_html)
    if a == b:
        return True, len(a), []
    diffs = []
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else None
        y = b[i] if i < len(b) else None
        if x != y:
            diffs.append((i, x, y))
        if len(diffs) >= 4:
            break
    return False, len(a), diffs


PAIRS = []


def build_pairs():
    """원본 경로 -> 새 경로"""
    for p in sorted((OLD / "lesson").glob("*.html")):
        PAIRS.append((p, NEW / "u1" / ("%s.html" % pad(p.stem))))
    for p in sorted((OLD / "review").glob("*.html")):
        PAIRS.append((p, NEW / "u1" / ("r%s.html" % pad(p.stem))))


def pad(code):
    return "-".join("%02d" % int(x) for x in str(code).split("-"))


def main():
    if not OLD.is_dir():
        raise SystemExit("원본 사본이 없습니다: %s" % OLD)
    build_pairs()
    ok = bad = total_items = 0
    for old, new in PAIRS:
        if not new.is_file():
            print("  [없음] %s 가 만들어지지 않았습니다" % new.relative_to(ROOT))
            bad += 1
            continue
        same, n, diffs = compare(old.name,
                                 old.read_text(encoding="utf-8"),
                                 new.read_text(encoding="utf-8"))
        total_items += n
        if same:
            print("  OK   %-18s 내용 %3d조각 일치" % (old.name, n))
            ok += 1
        else:
            print("  다름 %-18s" % old.name)
            for i, x, y in diffs:
                print("        %d번째" % i)
                print("          원본: %s" % (x,))
                print("          변환: %s" % (y,))
            bad += 1
    print()
    print("일치 %d · 불일치 %d · 대조한 내용 조각 %d개" % (ok, bad, total_items))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
