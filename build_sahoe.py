# -*- coding: utf-8 -*-
"""역사 탐정 수첩 — 차시 JSON을 정적 HTML로 빌드한다.

    python build_sahoe.py            lessons/ -> 저장소 루트
    python build_sahoe.py --check    화면 텍스트 금지어 검사

표준 라이브러리만 쓴다. 스키마는 schema.md 참고.
국어(말과 글 수첩)와 같은 엔진이되 블록 타입과 색이 다르다.
"""

import html
import json
import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent
LESSONS = ROOT / "lessons"
OUTPUT = "."
SITE = (ROOT / OUTPUT).resolve()

FORBIDDEN = ["지도서"]
NOT_STUDENT_FACING = {"teacher.html"}


# --------------------------------------------------------------------------
# 차시 코드
# --------------------------------------------------------------------------

def code_numbers(code):
    parts = [int(p) for p in str(code).split("-")]
    if len(parts) == 1:
        return parts
    if len(parts) != 2:
        raise ValueError("차시 코드 형식이 아닙니다: %r" % code)
    lo, hi = parts
    if hi < lo:
        raise ValueError("차시 범위가 거꾸로입니다: %r" % code)
    return list(range(lo, hi + 1))


def code_label(code):
    ns = code_numbers(code)
    return "%d차시" % ns[0] if len(ns) == 1 else "%d~%d차시" % (ns[0], ns[-1])


def code_sort_key(code):
    return code_numbers(code)[0]


def code_normalize(code):
    return "-".join("%02d" % int(p) for p in str(code).split("-"))


def lesson_sort_key(lesson):
    """차시는 첫 번호로, 복습은 다루는 범위의 마지막 번호로 정렬한다.

    '1~5차시 복습'은 5차시 **뒤에** 와야 하므로 첫 번호(1)로 정렬하면 안 된다.
    """
    ns = code_numbers(lesson["code"])
    return (ns[-1], 1) if lesson.get("kind") == "review" else (ns[0], 0)


def file_stem(lesson):
    """복습은 같은 차시 번호를 쓰므로 앞에 r 을 붙여 구분한다."""
    c = code_normalize(lesson["code"])
    return ("r%s" % c) if lesson.get("kind") == "review" else c


# --------------------------------------------------------------------------
# 인라인 서식 — **강조** 하나만, 나머지는 이스케이프
# --------------------------------------------------------------------------

_EM = re.compile(r"\*\*(.+?)\*\*", re.S)
NL = chr(10)


def inline(text):
    return _EM.sub(r'<span class="em">\1</span>', html.escape(str(text)))


def plain(text):
    return html.escape(str(text))


def lines(text):
    return "<br>".join(inline(t) for t in str(text).split(NL))


# --------------------------------------------------------------------------
# 조각 렌더러
# --------------------------------------------------------------------------

def render_card(c):
    out = ['<button class="card" type="button">']
    if c.get("tag"):
        out.append('<div class="tag">%s</div>' % plain(c["tag"]))
    out.append('<div class="q">%s</div>' % plain(c["q"]))
    body = []
    if c.get("a"):
        body.append(plain(c["a"]))
    if c.get("figs"):
        figs = "".join(
            '<figure><img src="../%s" alt="%s" loading="lazy">'
            '<figcaption>%s</figcaption></figure>'
            % (plain(f["src"]), plain(f["caption"]), plain(f["caption"]))
            for f in c["figs"])
        body.append('<div class="figs">%s</div>' % figs)
    if body:
        out.append('<div class="a">%s</div>' % "".join(body))
    out.append('<div class="hint">%s</div>' % plain(c.get("hint", "눌러서 확인")))
    out.append("</button>")
    return "".join(out)


def render_quiz(q):
    opts = "".join('<button class="opt" type="button" data-a="%d">%s</button>'
                   % (int(o["a"]), plain(o["t"])) for o in q["options"])
    star = '<span class="star" data-star></span>' if q.get("src") else ""
    src = ' data-src="%s"' % plain(q["src"]) if q.get("src") else ""
    return ('<div class="quiz" data-qid="%s"%s>'
            '<div class="qnum">%s%s</div>'
            '<div class="qtext">%s</div>'
            '<div class="opts">%s</div><div class="fb"></div></div>'
            % (plain(q["qid"]), src, plain(q.get("label", "")), star,
               plain(q["text"]), opts))


def render_section(sec):
    out = []
    head = plain(sec["heading"])
    if sec.get("num"):
        head = '<span class="num">%s</span> %s' % (plain(sec["num"]), head)
    out.append('      <h2 class="sec">%s</h2>' % head)
    if sec.get("lead"):
        out.append('      <p class="lead">%s</p>' % inline(sec["lead"]))
    if sec.get("cards"):
        cls = "grid haspic" if sec.get("haspic") else "grid"
        out.append('      <div class="%s">%s</div>'
                   % (cls, "".join(render_card(c) for c in sec["cards"])))
    for q in sec.get("quiz", []):
        out.append("      %s" % render_quiz(q))
    return NL.join(out)


# --------------------------------------------------------------------------
# 목차 — 국어와 같은 문법
# --------------------------------------------------------------------------

def unit_nav_title(unit):
    label = str(unit["label"])
    return "%s. %s" % (label, unit["title"]) if label.isdigit() else unit["title"]


def nav_label(lesson):
    if lesson.get("kind") == "review":
        return "★ %s" % lesson["title"]
    return "%s · %s" % (code_label(lesson["code"]), lesson["title"])


def render_nav(site, units, built, cur_unit, cur_stem):
    out = ['<nav class="nav" id="nav">',
           '    <div class="brand">',
           "      <h1>%s</h1>" % inline(site["title"])]
    if site.get("subtitle"):
        out.append("      <p>%s</p>" % plain(site["subtitle"]))
    out.append("    </div>")

    for unit in sorted(units, key=lambda u: u["order"]):
        is_cur = unit["id"] == cur_unit
        out.append('    <div class="unit%s">' % (" open" if is_cur else ""))
        out.append('      <button><span class="caret">▶</span>%s</button>'
                   % plain(unit_nav_title(unit)))
        out.append('      <div class="lessons">')
        for les in sorted(unit["lessons"], key=lesson_sort_key):
            stem = file_stem(les)
            label = nav_label(les)
            extra = " review" if les.get("kind") == "review" else ""
            if (unit["id"], stem) not in built:
                out.append('        <span class="soon">%s</span>' % plain(label))
            else:
                on = " on" if (is_cur and stem == cur_stem) else ""
                out.append('        <a class="lk%s%s" href="../%s/%s.html" '
                           'data-slug="%s">%s</a>'
                           % (extra, on, unit["id"], stem,
                              plain(les.get("slug", stem)), plain(label)))
        out.append("      </div>")
        out.append("    </div>")

    if site.get("nav_foot"):
        out.append('    <p class="navfoot">%s</p>' % lines(site["nav_foot"]))
    if site.get("teacher_page"):
        out.append('    <p class="navfoot"><a class="teach" href="../teacher.html">'
                   '선생님께 드리는 안내</a></p>')
    out.append("  </nav>")
    return NL.join(out)


# --------------------------------------------------------------------------
# 페이지
# --------------------------------------------------------------------------

PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{page_title}</title>
<link href="https://fonts.googleapis.com/css2?family=Gaegu:wght@400;700&family=Gowun+Dodum&family=Jua&family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet">
<style>
{style}</style>
</head>
<body>

<div class="topbar">
  <button id="open">☰</button>
  <span>{site_title}</span>
</div>
<div class="scrim" id="scrim"></div>

<div class="shell">
  {nav}

  <main class="main">
    <div class="col">
      <header class="center">
        <div class="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
{lead}      </header>

{sections}

{banner}
{closing}
      <div class="foot">{foot}</div>
    </div>
  </main>
</div>

<script>
{script}</script>
{page_script}
</body>
</html>
"""


def render_banner(d):
    if not d:
        return ""
    btns = "".join('<a class="btn%s" href="%s">%s</a>'
                   % (" ghost" if b.get("ghost") else "", plain(b["href"]),
                      plain(b["label"]))
                   for b in d.get("buttons", []))
    return ('      <div class="done-banner" id="doneBanner">'
            '<div class="bigstamp">%s</div>'
            '<div class="t">%s</div><div class="s">%s</div>'
            '<div class="row">%s</div></div>'
            % (plain(d.get("stamp", "해결!")), plain(d.get("title", "")),
               plain(d.get("sub", "")), btns))


def render_page(lesson, unit, site, units, built):
    stem = file_stem(lesson)
    nav_title = next((l["title"] for l in unit["lessons"]
                      if file_stem(l) == stem), "")
    quiz_total = lesson.get("quiz_total", 0)
    slug = lesson.get("progress_slug") or lesson.get("slug") or stem
    star_js = ""
    if any(q.get("src") for sec in lesson["sections"] for q in sec.get("quiz", [])):
        # 복습 페이지: 예전에 틀렸던 문제에 별을 붙인다
        star_js = ("document.querySelectorAll('.quiz').forEach(function(q){"
                   "if(q.dataset.src&&P.isWrong(q.dataset.src)){"
                   "q.classList.add('starred');"
                   "q.querySelector('[data-star]').textContent=' ★';}});")
    page_script = ('<script>%sP.touch("%s");initQuiz("%s",%d);</script>'
                   % (star_js, plain(slug), plain(slug), quiz_total)) if quiz_total else ""

    return PAGE.format(
        page_title=plain("%s · %s" % (nav_title, site["title"])),
        site_title=inline(site["title"]),
        style=STYLE,
        script=SCRIPT.replace("__KEY__", site.get("progress_key", "sahoe52-v1")),
        nav=render_nav(site, units, built, unit["id"], stem),
        eyebrow=plain(lesson.get("eyebrow", "")),
        title=lines(lesson["title"]),
        lead=('        <p class="lead">%s</p>\n' % inline(lesson["lead"])
              if lesson.get("lead") else ""),
        sections=(NL * 2).join(render_section(s) for s in lesson["sections"]),
        banner=render_banner(lesson.get("done")),
        closing=('      <div class="closing"><p>%s</p></div>' % lines(lesson["closing"])
                 if lesson.get("closing") else ""),
        foot=plain(site.get("foot", "사회 5-2 · 역사 탐정 수첩")),
        page_script=page_script,
    )


# --------------------------------------------------------------------------
# 검증
# --------------------------------------------------------------------------

def validate(lesson, unit, stem, path):
    def bad(msg):
        raise SystemExit("[%s] %s" % (path, msg))

    if lesson.get("schema") != "lesson/1":
        bad("schema 가 'lesson/1' 이 아닙니다: %r" % lesson.get("schema"))
    if lesson.get("unit") != unit["id"]:
        bad("unit(%r)이 폴더(%s)와 다릅니다" % (lesson.get("unit"), unit["id"]))
    if file_stem(lesson) != stem:
        bad("code/kind 가 파일 이름(%s)과 맞지 않습니다" % stem)
    for f in ("title", "sections"):
        if not lesson.get(f):
            bad("필수 필드 %s 가 없습니다" % f)
    roster = {file_stem(l) for l in unit["lessons"]}
    if stem not in roster:
        bad("units.json 차시 목록에 %s 가 없습니다" % stem)
    counted = sum(len(s.get("quiz", [])) for s in lesson["sections"])
    if lesson.get("quiz_total") and counted != lesson["quiz_total"]:
        bad("문항 수가 안 맞습니다: quiz_total=%d 인데 실제 %d개"
            % (lesson["quiz_total"], counted))
    for s in lesson["sections"]:
        for q in s.get("quiz", []):
            if sum(int(o["a"]) for o in q["options"]) != 1:
                bad("문항 %s: 정답이 정확히 하나가 아닙니다" % q.get("qid"))


def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def check_forbidden(paths):
    hits = []
    for p in paths:
        if p.name in NOT_STUDENT_FACING:
            continue
        visible = strip_comments(p.read_text(encoding="utf-8"))
        for line_no, line in enumerate(visible.splitlines(), 1):
            for word in FORBIDDEN:
                if word in line:
                    hits.append((p, line_no, word, line.strip()[:90]))
    return hits


# --------------------------------------------------------------------------
# 빌드
# --------------------------------------------------------------------------

def build(site_id="sahoe-5-2"):
    base = LESSONS / site_id
    index = json.loads((base / "units.json").read_text(encoding="utf-8"))
    site, units = index["site"], index["units"]
    by_id = {u["id"]: u for u in units}

    found = []
    for unit in units:
        d = base / unit["id"]
        if d.is_dir():
            for f in sorted(d.glob("*.json")):
                found.append((unit, f.stem, f))
    order = {}
    for u in units:
        for i, l in enumerate(sorted(u["lessons"],
                                     key=lambda l: (code_sort_key(l["code"]),
                                                    l.get("kind") == "review"))):
            order[(u["id"], file_stem(l))] = i
    found.sort(key=lambda t: (t[0]["order"], order.get((t[0]["id"], t[1]), 999)))
    built = {(u["id"], s) for u, s, _ in found}

    written = []
    for unit, stem, f in found:
        lesson = json.loads(f.read_text(encoding="utf-8"))
        validate(lesson, unit, stem, f)
        target = SITE / unit["id"] / ("%s.html" % stem)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_page(lesson, by_id[lesson["unit"]], site, units, built),
                          encoding="utf-8")
        written.append(target)

    # 이름이 바뀐 차시의 옛 HTML이 남아 떠돌지 않게 치운다
    for unit in units:
        d = SITE / unit["id"]
        if not d.is_dir():
            continue
        keep = {"%s.html" % st for u, st, _ in found if u["id"] == unit["id"]}
        for old_page in d.glob("*.html"):
            if old_page.name not in keep:
                print("  지움 %s (더 이상 만들어지지 않는 파일)"
                      % old_page.relative_to(ROOT))
                old_page.unlink()

    about = base / "about.json"
    if about.is_file():
        t = SITE / "teacher.html"
        t.write_text(render_about(json.loads(about.read_text(encoding="utf-8")), site),
                     encoding="utf-8")
        written.append(t)

    if found:
        h = SITE / "index.html"
        h.write_text(render_home(site, units, built), encoding="utf-8")
        written.append(h)
        for unit in units:
            if any((unit["id"], st) in built for _, st, _ in found):
                t = SITE / unit_list_name(unit)
                t.write_text(render_unit_list(unit, site, built), encoding="utf-8")
                written.append(t)

    return written, len(units), sum(len(u["lessons"]) for u in units)


ABOUT_PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{page_title}</title>
<link href="https://fonts.googleapis.com/css2?family=Gaegu:wght@400;700&family=Gowun+Dodum&family=Jua&family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet">
<style>
{style}
.about{{max-width:660px;margin:0 auto;padding:44px 22px 90px}}
.about .back{{font-size:13px;color:var(--faint);text-decoration:underline}}
.about h1{{font-family:'Jua',sans-serif;font-size:30px;line-height:1.35;margin:12px 0 6px}}
.about .sub{{font-size:14px;color:var(--faint);margin-bottom:30px}}
.about h2{{font-family:'Jua',sans-serif;font-size:21px;margin:32px 0 10px;padding-top:18px;border-top:1px solid var(--edge)}}
.about p{{margin-bottom:11px;line-height:1.8}}
.about ul{{margin:0 0 12px;padding-left:18px}}
.about li{{margin-bottom:5px}}
.about .foot{{margin-top:44px;font-size:12.5px;color:var(--faint)}}
</style>
</head>
<body>
<div class="about">
  <a class="back" href="index.html">← {site_title}</a>
  <h1>{title}</h1>
  <p class="sub">{subtitle}</p>
{sections}
  <p class="foot">{foot}</p>
</div>
</body>
</html>
"""

SECTION_SEP = NL


def render_about(about, site):
    out = []
    for sec in about.get("sections", []):
        if sec.get("heading"):
            out.append("  <h2>%s</h2>" % plain(sec["heading"]))
        for b in sec.get("blocks", []):
            if b.get("type") == "list":
                out.append("  <ul>%s</ul>"
                           % "".join("<li>%s</li>" % inline(x) for x in b["items"]))
            else:
                out.append("  <p>%s</p>" % inline(b["text"]))
    return ABOUT_PAGE.format(
        page_title=plain("%s · %s" % (about["title"], re.sub(r"\*\*", "", site["title"]))),
        site_title=inline(site["title"]),
        style=STYLE,
        title=lines(about["title"]),
        subtitle=plain(about.get("subtitle", "")),
        sections=SECTION_SEP.join(out),
        foot=plain(about.get("foot", "")),
    )


STYLE = r""":root{
  --paper:#F6F3E9; --grid:#E8E3D3; --card:#FFFDF6; --edge:#DCD5C0;
  --ink:#33312C; --ink2:#5C574B; --faint:#8C8470;
  --marker:#FFE066; --red:#C0392B; --blue:#2B6CB0; --green:#2F7D5D;
  --tap:56px;
}
*{margin:0;padding:0;box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  background:var(--paper); color:var(--ink);
  font-family:'Noto Sans KR',sans-serif; font-size:18.5px; font-weight:500; line-height:1.8;
  background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px);
  background-size:26px 26px;
}
.wrap{max-width:1000px;margin:0 auto;padding:26px 18px 100px}
a{color:inherit;text-decoration:none}

/* 상단 바 */
.bar{display:flex;align-items:center;gap:12px;margin-bottom:26px;flex-wrap:wrap}
.back{display:inline-flex;align-items:center;min-height:46px;padding:0 20px;background:var(--card);
  border:1.5px solid var(--edge);border-radius:999px;color:var(--ink2);font-family:'Jua',sans-serif;
  font-size:1.05rem;box-shadow:1px 2px 4px rgba(60,50,20,.07)}
.back:hover,.back:focus-visible{background:var(--marker);border-color:var(--ink);outline:none}
.crumb{color:var(--faint);font-family:'Jua',sans-serif;font-size:1rem}

/* 제목 */
h1{font-family:'Jua',sans-serif;font-size:clamp(2.15rem,5.8vw,3.2rem);line-height:1.38}
h1 .em{background:linear-gradient(transparent 58%,var(--marker) 58%);padding:0 4px}
.eyebrow{font-family:'Jua',sans-serif;color:var(--faint);font-size:1.05rem;margin-bottom:8px}
.center{text-align:center}

/* 종이 */
.paper{background:var(--card);border:1px solid var(--edge);border-radius:4px;
  box-shadow:2px 3px 10px rgba(60,50,20,.09)}
.tape{position:absolute;top:-12px;left:50%;transform:translateX(-50%) rotate(-2deg);width:104px;height:26px;
  background:rgba(255,224,102,.65);border-left:1px dashed rgba(0,0,0,.09);border-right:1px dashed rgba(0,0,0,.09)}

/* 홈 히어로 */
.hero{position:relative;background:var(--card);border:1px solid var(--edge);border-radius:4px;
  padding:34px 24px 30px;margin:26px 0 20px;text-align:center;box-shadow:2px 3px 12px rgba(60,50,20,.10)}
.ring{width:126px;height:126px;margin:0 auto 16px;position:relative}
.ring .val{position:absolute;inset:0;display:grid;place-items:center}
.ring .big{font-family:'Jua',sans-serif;font-size:2.45rem;color:var(--blue);line-height:1}
.ring .sub{font-family:'Jua',sans-serif;font-size:.92rem;color:var(--faint)}
.hero h2{font-family:'Jua',sans-serif;font-size:1.72rem;margin-bottom:2px}
.hero p{color:var(--ink2);font-size:1.06rem;font-weight:500;margin-bottom:20px}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:60px;padding:0 34px;
  background:var(--marker);border:2px solid var(--ink);border-radius:999px;color:var(--ink);
  font-family:'Jua',sans-serif;font-size:1.38rem;cursor:pointer}
.btn:hover,.btn:focus-visible{background:#FFD93D;outline:none}
.btn.ghost{background:var(--card);border-color:var(--edge);color:var(--ink2)}

/* 목록 */
h2.sec{font-family:'Jua',sans-serif;font-size:1.82rem;margin:44px 0 2px}
h2.sec .num{color:var(--red)}
.lead{color:var(--ink2);margin-bottom:18px;font-size:1.08rem;font-weight:500}

.list{display:grid;gap:11px}
.item{display:flex;align-items:center;gap:15px;background:var(--card);border:1px solid var(--edge);
  border-radius:4px;padding:14px 18px;min-height:74px;box-shadow:1px 2px 6px rgba(60,50,20,.07);
  transition:transform .12s,box-shadow .12s}
.item:hover,.item:focus-visible{transform:translate(-1px,-1px);box-shadow:3px 4px 9px rgba(60,50,20,.13);outline:none}
.item:active{transform:none}
.stamp{flex:0 0 46px;width:46px;height:46px;border:2px dashed #C9C0A8;border-radius:50%;display:grid;
  place-items:center;font-family:'Jua',sans-serif;color:#A79E86;font-size:1.05rem}
.item.done .stamp{border:2.5px solid var(--red);color:var(--red);background:rgba(192,57,43,.06);
  transform:rotate(-11deg);font-family:'Gaegu',cursive;font-weight:700;font-size:1.15rem}
.item.done .stamp span{display:none}
.item.done .stamp::after{content:"해결!"}
.it-body{flex:1;min-width:0}
.it-label{font-family:'Jua',sans-serif;font-size:1rem;color:var(--faint)}
.it-title{font-size:1.24rem;font-weight:700;margin-top:0}
.it-go{color:#B8B09A;font-size:1.4rem;flex:0 0 auto}
.item.review{background:linear-gradient(105deg,rgba(255,224,102,.30),var(--card))}
.item.review .stamp{border-style:solid;border-color:var(--ink);color:var(--ink)}
.item.review .it-label{color:var(--ink2)}

/* 학습 카드 */
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:13px}
.grid.g2{grid-template-columns:repeat(2,1fr)}
@media(max-width:820px){.grid,.grid.g2{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--edge);border-radius:4px;padding:20px 18px;text-align:left;
  cursor:pointer;color:var(--ink);font-family:inherit;font-size:1rem;min-height:var(--tap);
  box-shadow:1px 2px 6px rgba(60,50,20,.07);transition:transform .12s,box-shadow .12s}
.card:hover,.card:focus-visible{transform:translate(-1px,-1px);box-shadow:3px 4px 9px rgba(60,50,20,.13);outline:none}
.card .tag{font-family:'Jua',sans-serif;color:var(--red);font-size:1.06rem;margin-bottom:6px}
.card .q{font-weight:700;font-size:1.14rem;min-height:2.4em;line-height:1.7}
.card .a{display:none;margin-top:13px;padding-top:13px;border-top:1px dashed var(--edge);color:var(--blue);font-size:1.1rem;font-weight:500;line-height:1.7}
.card .hint{margin-top:13px;font-family:'Jua',sans-serif;font-size:.95rem;color:#A79E86}
.card.open .a{display:block}
.card.open .hint{display:none}
.card.open{box-shadow:3px 4px 9px rgba(60,50,20,.13)}

/* 퀴즈 */
.quiz{background:var(--card);border:1px solid var(--edge);border-radius:4px;padding:24px 22px;margin-bottom:13px;
  box-shadow:1px 2px 7px rgba(60,50,20,.08)}
.quiz.starred{border-color:var(--red);border-width:1.5px}
.qnum{font-family:'Jua',sans-serif;font-size:1.06rem;color:var(--faint);margin-bottom:6px}
.qnum .star{color:var(--red)}
.qtext{font-family:'Jua',sans-serif;font-size:1.56rem;line-height:1.55;margin-bottom:15px}
.opts{display:grid;gap:9px}
.opt{background:var(--card);border:1.5px solid var(--edge);border-radius:4px;padding:15px 18px;text-align:left;
  color:var(--ink);font-family:inherit;font-size:1.16rem;font-weight:700;cursor:pointer;min-height:var(--tap);transition:background .14s}
.opt:hover:not(:disabled),.opt:focus-visible{background:rgba(255,224,102,.28);border-color:var(--ink);outline:none}
.opt.ok{border-color:var(--green);color:var(--green);font-weight:700;background:rgba(47,125,93,.09)}
.opt.no{border-color:var(--red);color:var(--red);background:rgba(192,57,43,.06)}
.opt:disabled{opacity:.45;cursor:default}
.fb{font-family:'Jua',sans-serif;font-size:1.18rem;margin-top:10px;min-height:1.5em}
.fb.ok{color:var(--green)}.fb.no{color:var(--red)}

/* 완료 배너 */
.done-banner{display:none;position:relative;background:var(--card);border:1px solid var(--edge);border-radius:4px;
  padding:32px 24px 26px;text-align:center;margin-top:26px;box-shadow:2px 3px 12px rgba(60,50,20,.11)}
.done-banner.show{display:block}
.done-banner .t{font-family:'Jua',sans-serif;font-size:1.92rem;margin-bottom:4px}
.done-banner .s{color:var(--ink2);font-size:1.08rem;font-weight:500;margin-bottom:20px}
.row{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}
.bigstamp{display:inline-grid;place-items:center;width:78px;height:78px;border:3px solid var(--red);
  border-radius:50%;color:var(--red);font-family:'Gaegu',cursive;font-weight:700;font-size:1.85rem;
  transform:rotate(-11deg);background:rgba(192,57,43,.06);margin-bottom:14px}

/* 마무리 */
.closing{margin-top:56px;border-top:1px dashed var(--edge);padding-top:26px;text-align:center}
.closing p{font-family:'Jua',sans-serif;font-size:1.66rem;line-height:1.6}
.closing .em{background:linear-gradient(transparent 58%,var(--marker) 58%);padding:0 3px}
.foot{margin-top:48px;text-align:center;color:var(--faint);font-family:'Jua',sans-serif;
  font-size:.98rem;line-height:2}

/* 교사용 */
.tcard{background:var(--card);border:1px solid var(--edge);border-radius:4px;padding:22px;margin-bottom:12px;
  box-shadow:1px 2px 6px rgba(60,50,20,.07)}
.tcard h3{font-family:'Jua',sans-serif;font-size:1.44rem;margin-bottom:6px;color:var(--red)}
.tcard p{color:var(--ink2);font-size:1.08rem;font-weight:500}
.tcard ol{margin:10px 0 0 20px;color:var(--ink2);font-size:1.04rem;font-weight:500}
.tcard li{margin-bottom:6px}

@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}

/* ── 유물 사진 (카드 펼침 시) */
.figs{display:grid;gap:12px;margin-top:14px}
.figs:has(figure:nth-child(2)){grid-template-columns:1fr 1fr}
@media(max-width:520px){.figs:has(figure:nth-child(2)){grid-template-columns:1fr}}
.figs figure{margin:0}
.figs img{display:block;width:100%;height:auto;border-radius:3px;background:#2E2C27;
  border:1px solid #2E2C27;box-shadow:0 2px 8px rgba(60,50,20,.22)}
.figs figcaption{margin-top:7px;font-family:'Jua',sans-serif;font-size:.88rem;color:var(--faint);
  line-height:1.45;text-align:center}
.card.haspic .hint{color:var(--red)}

/* ================= 좌측 목차 — build_sahoe.py 가 덧붙인 부분 ================= */
.shell{display:flex;min-height:100vh;align-items:flex-start}
.main{flex:1;min-width:0;display:flex;justify-content:center;padding:26px 18px 100px}
.col{width:100%;max-width:1000px}

.nav{
  width:270px;flex:0 0 270px;background:var(--card);
  border-right:1.5px solid var(--edge);
  position:sticky;top:0;height:100vh;overflow-y:auto;padding:24px 0 40px;
}
.nav .brand{padding:0 20px 18px;border-bottom:1.5px solid var(--edge);margin-bottom:12px}
.nav .brand h1{font-family:'Jua',sans-serif;font-size:1.5rem;line-height:1.3}
.nav .brand h1 .em{background:linear-gradient(transparent 58%,var(--marker) 58%);padding:0 3px}
.nav .brand p{font-family:'Jua',sans-serif;font-size:.92rem;color:var(--faint);margin-top:2px}

.unit{border-bottom:1px solid rgba(0,0,0,.05)}
.unit>button{
  width:100%;background:none;border:0;cursor:pointer;color:var(--ink2);
  font-family:'Jua',sans-serif;font-size:1.05rem;
  display:flex;align-items:center;gap:9px;padding:12px 20px;text-align:left;
}
.unit>button:hover{color:var(--ink)}
.unit>button .caret{font-size:.6rem;color:var(--faint);transition:transform .18s;flex:0 0 9px}
.unit.open>button{color:var(--ink)}
.unit.open>button .caret{transform:rotate(90deg)}
.lessons{display:none;padding:2px 0 10px}
.unit.open .lessons{display:block}
.lessons a,.lessons .soon{
  display:block;padding:8px 18px 8px 34px;font-size:.97rem;font-weight:500;
  color:var(--ink2);position:relative;line-height:1.5;
}
.lessons a:hover{color:var(--ink);background:rgba(0,0,0,.025)}
.lessons .soon{color:var(--faint);opacity:.5}
.lessons a.review{color:var(--red)}
.lessons a.on{background:var(--marker);color:var(--ink)}
.lessons a.done::after{content:"✓";position:absolute;right:14px;color:var(--green);font-size:.9rem}
.navfoot{padding:14px 20px 0;font-size:.84rem;color:var(--faint);line-height:1.55}
.navfoot a.teach{color:var(--faint);text-decoration:underline;text-underline-offset:3px}
.navfoot a.teach:hover{color:var(--ink)}

/* 본문에서 첫 제목이 너무 붙지 않게 */
.col>header.center{margin-bottom:6px}
.col h2.sec:first-of-type{margin-top:34px}

/* 모바일 */
.topbar{display:none}
.scrim{display:none}
@media(max-width:900px){
  .topbar{
    display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:30;
    background:var(--card);border-bottom:1.5px solid var(--edge);padding:10px 14px;
  }
  .topbar button{background:none;border:0;font-size:1.5rem;cursor:pointer;color:var(--ink);line-height:1}
  .topbar span{font-family:'Jua',sans-serif;font-size:1.2rem}
  .topbar span .em{background:linear-gradient(transparent 58%,var(--marker) 58%);padding:0 3px}
  .shell{flex-direction:column}
  .nav{
    position:fixed;top:0;left:0;height:100vh;z-index:40;width:82vw;max-width:300px;
    transform:translateX(-100%);transition:transform .22s ease;
  }
  .nav.show{transform:translateX(0)}
  .scrim{position:fixed;inset:0;background:rgba(30,26,16,.4);z-index:35}
  .scrim.show{display:block}
  .main{padding:20px 14px 90px}
}
"""

SCRIPT = r"""(function(){
  var KEY='__KEY__';
  function load(){try{return JSON.parse(localStorage.getItem(KEY))||{}}catch(e){return{}}}
  function save(d){try{localStorage.setItem(KEY,JSON.stringify(d))}catch(e){}}
  window.P={
    get:load,
    isDone:function(s){return !!(load().done||{})[s]},
    markDone:function(s){var d=load();d.done=d.done||{};d.done[s]=1;d.last=s;save(d)},
    touch:function(s){var d=load();d.last=s;save(d)},
    last:function(){return load().last||null},
    doneCount:function(){return Object.keys(load().done||{}).length},
    wrong:function(qid){var d=load();d.wrong=d.wrong||{};d.wrong[qid]=1;save(d)},
    isWrong:function(qid){return !!(load().wrong||{})[qid]},
    reset:function(){try{localStorage.removeItem(KEY)}catch(e){}}
  };
  // 카드 펼치기
  document.addEventListener('click',function(e){
    var c=e.target.closest('.card'); if(c) c.classList.toggle('open');
  });
  // 퀴즈
  window.initQuiz=function(slug,total){
    var solved=0;
    document.querySelectorAll('.quiz').forEach(function(q){
      var fb=q.querySelector('.fb'), qid=q.dataset.qid;
      q.querySelectorAll('.opt').forEach(function(o){
        o.addEventListener('click',function(){
          if(q.dataset.done)return;
          if(o.dataset.a==='1'){
            o.classList.add('ok'); fb.textContent='정답입니다!'; fb.className='fb ok'; q.dataset.done='1';
            q.querySelectorAll('.opt').forEach(function(x){if(x!==o)x.disabled=true});
            solved++;
            if(total&&solved===total){
              if(slug)P.markDone(slug);
              var b=document.getElementById('doneBanner'); if(b){b.classList.add('show');b.scrollIntoView({behavior:'smooth',block:'center'});}
            }
          }else{
            o.classList.add('no'); o.disabled=true;
            fb.textContent='다시 한번 생각해 보세요.'; fb.className='fb no';
            if(qid)P.wrong(qid);
            setTimeout(function(){o.classList.remove('no')},800);
          }
        });
      });
    });
  };
})();

/* ---- 좌측 목차 — build_sahoe.py 가 덧붙인 부분 ---- */
document.querySelectorAll('.unit>button').forEach(function(b){
  b.onclick=function(){b.parentElement.classList.toggle('open')};
});
document.querySelectorAll('.lessons a.lk').forEach(function(a){
  if(a.dataset.slug && P.isDone(a.dataset.slug)) a.classList.add('done');
});
(function(){
  var nav=document.getElementById('nav'), scrim=document.getElementById('scrim'),
      op=document.getElementById('open');
  if(op) op.onclick=function(){nav.classList.add('show');scrim.classList.add('show')};
  if(scrim) scrim.onclick=function(){nav.classList.remove('show');scrim.classList.remove('show')};
  var on=document.querySelector('.lessons a.on');
  if(on && nav && nav.scrollHeight>nav.clientHeight) on.scrollIntoView({block:'center'});
})();
"""

# --------------------------------------------------------------------------
# 홈 · 차시 목록 — 옛 디자인 그대로, units.json 에서 만든다
# --------------------------------------------------------------------------

SHELL = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{page_title}</title>
<link href="https://fonts.googleapis.com/css2?family=Gaegu:wght@400;700&family=Gowun+Dodum&family=Jua&family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet">
<style>
{style}</style>
</head>
<body><div class="wrap">
{body}
</div>
<script>
{script}</script>
{page_script}
</body>
</html>
"""

HOME_JS = """var d=P.get(), done=d.done||{}, n=Object.keys(done).length, tot=SEQ.length;
document.getElementById('pct').textContent=n;
document.getElementById('prog').style.strokeDashoffset=327-327*(n/tot);
var nx=SEQ.find(function(x){return !done[x[1]]});
if(n===0){
  document.getElementById('heroTitle').textContent='\uc218\ucca9\uc744 \ud3bc\uccd0 \ubcfc\uae4c\uc694?';
  document.getElementById('heroSub').textContent='1\ucc28\uc2dc\ubd80\ud130 \ucc9c\ucc9c\ud788 \ud568\uaed8 \uac00\uc694.';
} else if(nx){
  document.getElementById('heroTitle').textContent=nx[2];
  document.getElementById('heroSub').textContent=(nx[0]==='r'?'\ub2e4\uc2dc \ud480\uae30\uac00 \uae30\ub2e4\ub9ac\uace0 \uc788\uc5b4\uc694.':'\uc774\uc5b4\uc11c \ud574 \ubcfc\uae4c\uc694?');
  document.getElementById('heroBtn').textContent='\uc774\uc5b4\uc11c \ud558\uae30';
  document.getElementById('heroBtn').href=nx[3];
} else {
  document.getElementById('heroTitle').textContent='1\ub2e8\uc6d0, \uc804\ubd80 \ud574\uacb0!';
  document.getElementById('heroSub').textContent='\uc218\ucca9\uc774 \ub3c4\uc7a5\uc73c\ub85c \uac00\ub4dd \ucc3c\uc5b4\uc694.';
  document.getElementById('heroBtn').textContent='\ub2e4\uc2dc \ub458\ub7ec\ubcf4\uae30';
  document.getElementById('heroBtn').href=SEQ[0][3];
}
document.getElementById('rst').addEventListener('click',function(e){
  e.preventDefault();
  if(confirm('\uc218\ucca9\uc5d0 \ucc0d\uc740 \ub3c4\uc7a5\uc744 \ubaa8\ub450 \uc9c0\uc6b8\uae4c\uc694?')){P.reset();location.reload();}
});"""

HOME_BODY = """<header class="center" style="margin-top:20px">
<div class="eyebrow">{sub}</div>
<h1>{title}</h1></header>

<div class="hero">
  <div class="tape"></div>
  <div class="ring">
    <svg width="126" height="126" viewBox="0 0 126 126">
      <circle cx="63" cy="63" r="52" fill="none" stroke="#E4DDC8" stroke-width="9"/>
      <circle id="prog" cx="63" cy="63" r="52" fill="none" stroke="#2B6CB0" stroke-width="9"
              stroke-linecap="round" stroke-dasharray="327" stroke-dashoffset="327"/>
    </svg>
    <div class="val"><div><div class="big" id="pct">0</div><div class="sub">개 해결</div></div></div>
  </div>
  <h2 id="heroTitle">오늘의 복습을 시작해요</h2>
  <p id="heroSub">5분이면 충분해요.</p>
  <a class="btn" id="heroBtn" href="{first}">시작하기</a>
</div>

<h2 class="sec"><span class="num">단원.</span> 수첩의 단원들</h2>
<p class="lead">아직 배우지 않은 곳도 미리 펼쳐 볼 수 있어요.</p>
<div class="list">{items}</div>

<div class="foot">{foot}<br>
<a href="teacher.html" style="color:var(--faint);text-decoration:underline">선생님께</a> &middot;
<a href="#" id="rst" style="color:var(--faint);text-decoration:underline">수첩 비우기</a></div>"""

UNIT_BODY = """<div class="bar"><a class="back" href="index.html">&larr; 처음으로</a>
<span class="crumb">{sub}</span></div>
<header class="center"><div class="eyebrow">{label}단원</div>
<h1>{title}</h1>
<p class="lead" style="margin-top:14px">어느 차시든 눌러서 펼칠 수 있어요. 예습도 복습도 자유롭게.</p></header>
<div class="list">{rows}</div>
<div class="foot">{foot}</div>"""


def unit_list_name(unit):
    return "unit%s.html" % unit["label"]


def seq_of(units, built):
    """진도 계산용 차시 순서. 옛 index.html 의 SEQ 배열을 대신한다."""
    out = []
    for u in sorted(units, key=lambda x: x["order"]):
        for l in sorted(u["lessons"], key=lesson_sort_key):
            stem = file_stem(l)
            if (u["id"], stem) not in built:
                continue
            out.append(["r" if l.get("kind") == "review" else "l",
                        l.get("slug", stem),
                        nav_label(l).lstrip("\u2605 "),
                        "%s/%s.html" % (u["id"], stem)])
    return out


def _unit_row(unit, ready):
    if ready:
        return ('<a class="item" href="%s"><div class="stamp"><span>%s</span></div>'
                '<div class="it-body"><div class="it-label">%s단원</div>'
                '<div class="it-title">%s</div></div><div class="it-go">&rsaquo;</div></a>'
                % (unit_list_name(unit), plain(unit["label"]), plain(unit["label"]),
                   plain(unit["title"])))
    return ('<div class="item" style="opacity:.45"><div class="stamp"><span>%s</span></div>'
            '<div class="it-body"><div class="it-label">%s단원</div>'
            '<div class="it-title">아직 준비 중</div></div></div>'
            % (plain(unit["label"]), plain(unit["label"])))


def render_home(site, units, built):
    seq = seq_of(units, built)
    items = [_unit_row(u, any((u["id"], file_stem(l)) in built for l in u["lessons"]))
             for u in sorted(units, key=lambda x: x["order"])]
    for extra in site.get("upcoming_units", []):
        items.append(_unit_row({"label": extra, "title": ""}, False))
    body = HOME_BODY.format(
        sub=plain(site.get("subtitle", "")),
        title=inline(site["title"]),
        first=seq[0][3] if seq else "index.html",
        items="".join(items),
        foot=plain(site.get("foot", "")))
    return SHELL.format(
        page_title=plain(re.sub(r"\*\*", "", site["title"])),
        style=STYLE,
        script=SCRIPT.replace("__KEY__", site.get("progress_key", "sahoe52-v1")),
        body=body,
        page_script="<script>var SEQ=%s;%s%s</script>"
                    % (json.dumps(seq, ensure_ascii=False), NL, HOME_JS))


def render_unit_list(unit, site, built):
    rows = []
    for l in sorted(unit["lessons"], key=lesson_sort_key):
        stem = file_stem(l)
        if (unit["id"], stem) not in built:
            continue
        review = l.get("kind") == "review"
        rows.append(
            '<a class="item%s" href="%s/%s.html" data-slug="%s">'
            '<div class="stamp"><span>%s</span></div>'
            '<div class="it-body"><div class="it-label">%s</div>'
            '<div class="it-title">%s</div></div><div class="it-go">&rsaquo;</div></a>'
            % (" review" if review else "", unit["id"], stem,
               plain(l.get("slug", stem)),
               "&#9733;" if review else code_numbers(l["code"])[0],
               plain(l["label"]), plain(l["title"])))
    body = UNIT_BODY.format(
        sub=plain(site.get("subtitle", "")), label=plain(unit["label"]),
        title=inline(unit["title"]), rows="".join(rows),
        foot=plain(site.get("foot", "")))
    return SHELL.format(
        page_title=plain("%s단원 · %s" % (unit["label"],
                                          re.sub(r"\*\*", "", site["title"]))),
        style=STYLE,
        script=SCRIPT.replace("__KEY__", site.get("progress_key", "sahoe52-v1")),
        body=body,
        page_script="<script>document.querySelectorAll('.list .item').forEach("
                    "function(a){if(a.dataset.slug&&P.isDone(a.dataset.slug))"
                    "a.classList.add('done')});</script>")


def main():
    written, n_units, n_lessons = build()
    for p in written:
        print("  %s" % p.relative_to(ROOT))
    pages = [p for p in written if p.parent != SITE]
    print("단원 %d · 차시 %d 중 %d개 빌드" % (n_units, n_lessons, len(pages)))
    hits = check_forbidden(written)
    if hits:
        print("\n화면 텍스트에 금지어가 남아 있습니다:")
        for p, ln, w, s in hits:
            print("  %s:%d  [%s]  %s" % (p.relative_to(ROOT), ln, w, s))
        return 1
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        files = sorted(SITE.rglob("*.html"))
        found = check_forbidden(files)
        for p, ln, w, s in found:
            print("%s:%d  [%s]  %s" % (p.relative_to(ROOT), ln, w, s))
        print("%d개 파일 검사 · 위반 %d건" % (len(files), len(found)))
        sys.exit(1 if found else 0)
    sys.exit(main())
