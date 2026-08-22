# 차시 데이터 스키마 — 사회 5-2

「역사 탐정 수첩」의 차시 데이터 형식.
**JSON을 고치면 사이트가 바뀐다. HTML은 손대지 않는다.**

국어(「말과 글 수첩」)와 같은 뼈대를 쓴다. 다른 것은 조각 종류와 색뿐이다.

```
lessons/sahoe-5-2/units.json      단원·차시 목차
lessons/sahoe-5-2/about.json      선생님 안내 페이지
lessons/sahoe-5-2/u1/05.json      차시 하나 = 파일 하나
lessons/sahoe-5-2/u1/r01.json     복습 관문 (앞에 r)
```

**폴더 이름은 전부 ASCII로.** 한글 폴더명은 zip·드라이브 이동에서 깨진다.

---

## 1. `units.json`

```json
{
  "schema": "units/1",
  "site": {
    "title": "역사 탐정 **수첩**",
    "subtitle": "사회 5학년 2학기",
    "foot": "사회 5-2 · 역사 탐정 수첩",
    "nav_foot": "어느 차시든 눌러서 펼칠 수 있어요.\n예습도 복습도 자유롭게.",
    "teacher_page": true,
    "progress_key": "sahoe52-v1",
    "upcoming_units": ["2", "3"]
  },
  "units": [
    {
      "id": "u1", "order": 1, "label": "1",
      "title": "유적과 유물로 살펴본 옛 사람들의 생활",
      "lessons": [
        { "code": "05", "kind": "lesson", "slug": "5",
          "title": "고조선", "label": "5차시" },
        { "code": "01", "kind": "review", "slug": "review1",
          "title": "1~5차시 복습", "label": "다시 풀기" }
      ]
    }
  ]
}
```

| 필드 | 설명 |
|---|---|
| `site.title` | `**강조**` 는 노란 형광펜이 된다 |
| `site.progress_key` | 도장 저장 열쇠. **바꾸면 아이들 진도가 날아간다** |
| `site.upcoming_units` | 홈에 "아직 준비 중"으로만 띄울 단원 번호 |
| `units[].order` | 정렬 순서. **`label`로 정렬하지 않는다** |
| `lessons[].code` | 차시 코드. `05`, `07-08` |
| `lessons[].kind` | `lesson` 또는 `review` |
| `lessons[].slug` | **도장 저장 이름.** 옛 사이트와 같아야 진도가 이어진다 |
| `lessons[].title` | 목차에 뜨는 이름 |
| `lessons[].label` | 목록 화면의 작은 글씨 (`5차시`, `다시 풀기`) |

### `slug` 를 따로 두는 이유

도장은 브라우저에 `slug` 이름으로 저장돼 있다.
파일 이름을 `5.html` → `u1/05.html` 로 바꿔도 `slug` 가 `"5"` 로 남아 있으면
**이미 찍힌 도장이 그대로 살아 있다.** 절대 바꾸지 말 것.

### 차시 코드

| 코드 | 화면 |
|---|---|
| `05` | 5차시 |
| `07-08` | 7~8차시 |

두 자리로 0을 채운다. 정렬 키는 첫 숫자다. 문자열 정렬이 아니다.
복습은 차시 번호가 겹치므로 파일 이름 앞에 `r` 을 붙인다 (`r01.json` → `u1/r01.html`).

---

## 2. 차시 파일

```json
{
  "schema": "lesson/1",
  "unit": "u1",
  "code": "05",
  "kind": "lesson",
  "slug": "5",
  "eyebrow": "1단원 · 5차시",
  "title": "고조선 사람들은\n어떻게 **살았을까요?**",
  "progress_slug": "5",
  "quiz_total": 3,
  "sections": [ ... ],
  "done": { ... },
  "closing": "물건과 이야기와 법은,\n**그 시대를 이야기한다.**"
}
```

| 필드 | 필수 | 설명 |
|---|---|---|
| `title` | ● | 큰 제목. `\n` = 줄바꿈, `**...**` = 형광펜 |
| `eyebrow` | | 제목 위 작은 글씨 |
| `lead` | | 제목 아래 한 줄 |
| `sections` | ● | 본문 |
| `quiz_total` | | 도장을 찍는 데 필요한 정답 수. **실제 문항 수와 같아야 한다** (빌드가 검사) |
| `progress_slug` | | 도장 이름. 없으면 `slug` 를 쓴다 |
| `done` | | 다 맞혔을 때 뜨는 배너 |
| `closing` | | 맨 아래 맺음말 |

### `sections[]`

```json
{
  "num": "하나.",
  "heading": "이야기 속에 숨은 뜻",
  "lead": "단군 이야기는 옛사람들이 남긴 암호문이에요.",
  "cards": [ ... ],
  "quiz": [ ... ],
  "haspic": true
}
```

`num` 은 빨간 글씨로 앞에 붙는다. `haspic` 은 사진이 든 카드 묶음일 때 넓게 편다.

### `cards[]` — 눌러서 뒤집는 카드

```json
{
  "tag": "장면 ①",
  "q": "환웅은 하늘을 다스리는 환인의 아들이다",
  "a": "→ 우리는 하늘의 자손! 나라의 신성함을 내세우려 했어요.",
  "hint": "눌러서 확인",
  "figs": [ { "src": "img/goindol.jpg", "caption": "고인돌 (1900년대 초 촬영)" } ]
}
```

`q` 가 앞면, `a` 가 뒷면. `figs` 를 넣으면 뒷면에 사진이 나온다.
사진만 있는 카드는 `a` 를 빼고 `hint` 를 `"눌러서 사진 보기"` 로 한다.

사진은 `img/` 폴더에 두고 `src` 에 `img/파일이름` 으로 적는다.

### `quiz[]` — 3지선다

```json
{
  "qid": "5-1",
  "label": "문제 1",
  "text": "환웅과 웅녀가 혼인했다는 장면은 무엇을 뜻할까요?",
  "options": [
    { "t": "곰이 진짜 사람이 되었다", "a": 0 },
    { "t": "두 부족이 하나로 합쳐졌다", "a": 1 },
    { "t": "결혼식을 좋아했다", "a": 0 }
  ]
}
```

`a: 1` 이 정답이다. **정답은 정확히 하나여야 한다** (빌드가 검사).
`qid` 는 틀린 문제를 기억하는 열쇠다. 복습 관문에서 이 번호로 ★를 찾는다.

복습 관문의 문항에는 `"src": "5-1"` 을 넣는다.
그 문제를 예전에 틀렸으면 ★가 붙는다.

### `done` — 완료 배너

```json
{
  "stamp": "해결!",
  "title": "5차시 해결!",
  "sub": "문제를 모두 맞혔어요. 수첩에 도장을 찍었습니다.",
  "buttons": [
    { "label": "1~5차시 복습 풀러 가기", "href": "r01.html" },
    { "label": "차시 목록", "href": "../unit1.html", "ghost": true }
  ]
}
```

`href` 는 차시 페이지(`u1/`) 기준이다. 옆 차시는 `05.html`, 루트는 `../unit1.html`.

---

## 3. 데이터에 넣지 않는 것

| | 어디에 있나 |
|---|---|
| CSS · JavaScript | `build_sahoe.py` 의 `STYLE` / `SCRIPT` |
| 홈 화면·차시 목록 | `units.json` 에서 만들어진다 |
| 진도 계산 순서(SEQ) | `units.json` 순서에서 계산 |
| 도장 로직 | `SCRIPT` |

---

## 4. 빌드

```
python build_sahoe.py            # lessons/ → 저장소 루트
python build_sahoe.py --check    # 금지어 검사
```

만들어지는 것: `index.html`, `unit1.html`, `teacher.html`, `u1/*.html`

빌드는 아래를 검사하고 하나라도 걸리면 **멈춘다**.

- `schema` · `unit` · `code` · `kind` 가 파일 위치와 맞는지
- `units.json` 차시 목록에 있는 차시인지
- `quiz_total` 이 실제 문항 수와 같은지
- 문항마다 정답이 정확히 하나인지

### 검사 도구

```
python tools/verify.py    옛 페이지와 내용이 같은지 대조 (974조각)
python tools/links.py     모든 링크·사진이 실제로 있는지
```

`tools/_original/` 은 옛 HTML 사본이다. 대조용이라 저장소에 올리지 않는다.
