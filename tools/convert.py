# -*- coding: utf-8 -*-
"""기존 사회 HTML을 차시 JSON으로 옮긴다. 한 번 쓰고 버리는 도구다.

    python tools/convert.py

읽는 것 : lesson/*.html, review/*.html, unit1.html, index.html
쓰는 것 : lessons/sahoe-5-2/units.json, lessons/sahoe-5-2/u1/*.json

변환이 맞는지는 tools/verify.py 가 원본과 대조해 증명한다.
"""

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dom import parse, squash  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "lessons" / "sahoe-5-2"
# 원본은 tools/_original 에 떠 두고 거기서만 읽는다.
# 빌드가 저장소 루트를 덮어쓰기 때문에 원본을 루트에서 읽으면 안 된다.
SRC = ROOT / "tools" / "_original"


def pad(code):
    return "-".join("%02d" % int(p) for p in str(code).split("-"))


def remap_href(href):
    """옛 경로를 새 파일 이름으로. 새 차시 페이지는 전부 u1/ 안에 있다."""
    h = re.sub(r"^\.\./", "", href)
    m = re.match(r"^review/([0-9\-]+)\.html$", h)
    if m:
        return "r%s.html" % pad(m.group(1))
    m = re.match(r"^([0-9][0-9\-]*)\.html$", h)
    if m:
        return "%s.html" % pad(m.group(1))
    return "../%s" % h


def read(p):
    return parse(p.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# index.html 의 SEQ 배열 = 차시 순서의 정본
# --------------------------------------------------------------------------

def read_seq():
    s = (SRC / "index.html").read_text(encoding="utf-8")
    m = re.search(r"var SEQ=(\[.*?\]);", s, re.S)
    if not m:
        raise SystemExit("index.html 에서 SEQ 를 못 찾았습니다")
    return json.loads(m.group(1))


# --------------------------------------------------------------------------
# 차시 페이지
# --------------------------------------------------------------------------

def figs_of(node):
    out = []
    for fig in node.find_all("figure"):
        img = fig.first("img")
        cap = fig.first("figcaption")
        out.append({
            "src": re.sub(r"^\.\./", "", img.attrs.get("src", "")),
            "caption": squash(cap.text()) if cap else squash(img.attrs.get("alt", "")),
        })
    return out


def card_of(btn):
    a = btn.first("div", "a")
    hint = btn.first("div", "hint")
    card = {
        "tag": squash(btn.first("div", "tag").text()) if btn.first("div", "tag") else "",
        "q": squash(btn.first("div", "q").text()),
    }
    if a:
        # figs 안의 글자는 본문이 아니므로 빼고 센다
        body = "".join(k if isinstance(k, str) else ("" if getattr(k, "has", None)
                       and k.has("figs") else k.text()) for k in a.kids)
        body = squash(body)
        if body:
            card["a"] = body
        f = figs_of(a)
        if f:
            card["figs"] = f
    if hint:
        card["hint"] = squash(hint.text())
    return card


def quiz_of(q):
    qnum = q.first("div", "qnum")
    item = {
        "qid": q.attrs.get("data-qid", ""),
        "label": squash(qnum.text()) if qnum else "",
        "text": squash(q.first("div", "qtext").text()),
        "options": [{"t": squash(o.text()), "a": int(o.attrs.get("data-a", "0"))}
                    for o in q.find_all("button", "opt")],
    }
    if q.attrs.get("data-src"):
        item["src"] = q.attrs["data-src"]
    return item


def sections_of(root):
    """h2.sec 를 만날 때마다 새 묶음. 그 뒤의 lead/grid/quiz 를 담는다."""
    body = root.first("div", "wrap")
    secs, cur = [], None
    for k in body.kids:
        if not hasattr(k, "tag"):
            continue
        if k.tag == "h2" and k.has("sec"):
            num = k.first("span", "num")
            cur = {
                "num": squash(num.text()) if num else "",
                "heading": squash("".join(
                    x if isinstance(x, str) else ("" if getattr(x, "has", None)
                    and x.has("num") else x.text()) for x in k.kids)),
                "cards": [], "quiz": [],
            }
            secs.append(cur)
        elif cur is None:
            continue
        elif k.tag == "p" and k.has("lead"):
            cur["lead"] = squash(k.text())
        elif k.tag == "div" and k.has("grid"):
            cur["cards"].extend(card_of(b) for b in k.children("button", "card"))
            if k.has("haspic"):
                cur["haspic"] = True
        elif k.tag == "div" and k.has("quiz"):
            cur["quiz"].append(quiz_of(k))
    for s in secs:
        if not s["cards"]:
            del s["cards"]
        if not s["quiz"]:
            del s["quiz"]
    return secs


def convert_page(path, code, kind):
    root = read(path)
    body = root.first("div", "wrap")
    head = body.first("header")
    h1 = head.first("h1")
    eyebrow = head.first("div", "eyebrow")
    lead = head.first("p", "lead")
    banner = body.first("div", "done-banner")
    closing = body.first("div", "closing")

    src = path.read_text(encoding="utf-8")
    m = re.search(r'initQuiz\("([^"]*)",\s*(\d+)\)', src)

    data = {
        "schema": "lesson/1",
        "unit": "u1",
        "code": code,
        "kind": kind,
        "eyebrow": squash(eyebrow.text()) if eyebrow else "",
        "title": h1.marked().strip(),
        "sections": sections_of(root),
    }
    if lead:
        data["lead"] = squash(lead.text())
    if m:
        data["progress_slug"] = m.group(1)
        data["quiz_total"] = int(m.group(2))
    if banner:
        t = banner.first("div", "t")
        s = banner.first("div", "s")
        data["done"] = {
            "stamp": squash(banner.first("div", "bigstamp").text()),
            "title": squash(t.text()) if t else "",
            "sub": squash(s.text()) if s else "",
            "buttons": [{"label": squash(a.text()),
                         "href": remap_href(a.attrs.get("href", "")),
                         "ghost": a.has("ghost")}
                        for a in banner.find_all("a", "btn")],
        }
    if closing:
        p = closing.first("p")
        data["closing"] = p.marked().strip()
    return data


# --------------------------------------------------------------------------
# unit1.html -> 목차
# --------------------------------------------------------------------------

def convert_units(seq):
    lessons = []
    root = read(SRC / "unit1.html")
    for a in root.find_all("a", "item"):
        slug = a.attrs.get("data-slug", "")
        label = a.first("div", "it-label")
        title = a.first("div", "it-title")
        href = a.attrs.get("href", "")
        kind = "review" if href.startswith("review/") else "lesson"
        lessons.append({
            "code": pad(slug.replace("review", "")) if kind == "review" else pad(slug),
            "kind": kind,
            "slug": slug,
            "title": squash(title.text()),
            "label": squash(label.text()),
        })
    idx = read(SRC / "index.html")
    h1 = idx.first("header").first("h1")
    unit_a = idx.first("a", "item")
    unit_title = squash(unit_a.first("div", "it-title").text())
    return {
        "schema": "units/1",
        "site": {
            "title": h1.marked().strip(),
            "subtitle": squash(idx.first("div", "eyebrow").text()),
            "nav_foot": "어느 차시든 눌러서 펼칠 수 있어요.\n예습도 복습도 자유롭게.",
            "teacher_page": True,
            "progress_key": "sahoe52-v1",
        },
        "units": [{
            "id": "u1", "order": 1, "label": "1", "title": unit_title,
            "lessons": lessons,
        }],
    }


def main():
    seq = read_seq()
    units = convert_units(seq)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "units.json").write_text(
        json.dumps(units, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (OUT / "u1").mkdir(parents=True, exist_ok=True)
    n = 0
    for les in units["units"][0]["lessons"]:
        slug, kind = les["slug"], les["kind"]
        path = SRC / ("review/%s.html" % slug.replace("review", "")
                       if kind == "review" else "lesson/%s.html" % slug)
        name = ("r%s" % les["code"]) if kind == "review" else les["code"]
        data = convert_page(path, les["code"], kind)
        data["slug"] = slug
        (OUT / "u1" / ("%s.json" % name)).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        n += 1
        print("  %-18s -> u1/%s.json" % (path.relative_to(SRC), name))
    print("차시 %d개 변환" % n)


if __name__ == "__main__":
    main()
