# 역사 탐정 수첩 — 사회 5-2

초등 5학년 2학기 사회 차시별 복습 사이트.

<https://sikke12632.github.io/social5-2/>

개념을 카드로 훑고 확인 문제를 푸는 5분짜리 구성. 5차시마다 복습 관문이 있다.

## 페이지를 손으로 만들지 않는다

**차시 데이터(JSON) → 빌드 스크립트 → 사이트**

HTML은 건드리지 않는다. JSON을 고치고 다시 빌드한다.

```
python build_sahoe.py            # lessons/ → 저장소 루트
python build_sahoe.py --check    # 금지어 검사
```

파이썬 3만 있으면 된다. 설치할 패키지 없음.

## 구조

```
lessons/sahoe-5-2/units.json     단원·차시 목차 (정렬 순서, 도장 이름 포함)
lessons/sahoe-5-2/about.json     선생님 안내 페이지 내용
lessons/sahoe-5-2/u1/05.json     차시 하나 = 파일 하나
lessons/sahoe-5-2/u1/r01.json    복습 관문
build_sahoe.py                   빌드 스크립트 (CSS·JS도 여기 들어 있다)
schema.md                        JSON 필드 정의 — 새 차시 쓰기 전에 읽을 것
img/                             사진

index.html                       빌드 결과 · 홈 (진행률, 이어서 하기)
unit1.html                       빌드 결과 · 1단원 차시 목록
teacher.html                     빌드 결과 · 선생님 안내
u1/*.html                        빌드 결과 · 차시 페이지
```

빌드 결과 HTML은 커밋한다. GitHub Pages가 그대로 서빙한다.

## 차시 추가하기

1. `lessons/sahoe-5-2/units.json` 의 `lessons` 에 한 줄 추가
2. `lessons/sahoe-5-2/u1/<코드>.json` 을 만든다
3. `python build_sahoe.py`
4. 커밋 · 푸시

목차·홈·진행률은 전부 `units.json` 에서 다시 계산된다. 손으로 고칠 곳이 없다.

2·3단원은 `units.json` 에 단원을 추가하고 `lessons/sahoe-5-2/u2/` 를 만들면 된다.

## 도장 진도를 깨뜨리지 않으려면

아이들 진도는 브라우저에 `sahoe52-v1` 열쇠로, 차시마다 `slug` 이름으로 저장된다.

- `units.json` 의 `site.progress_key` 를 바꾸면 **전부 날아간다**
- `lessons[].slug` 를 바꾸면 **그 차시 도장이 날아간다**

파일 이름이 `5.html` → `u1/05.html` 로 바뀌어도 `slug` 가 `"5"` 로 남아 있으면
이미 찍힌 도장은 그대로다.

## 검사 도구

```
python tools/verify.py    옛 페이지와 내용이 같은지 대조
python tools/links.py     모든 링크·사진이 실제로 있는지
```

`tools/_original/` 은 개편 전 HTML 사본이다. 대조용이라 커밋하지 않는다.
되살릴 일이 있으면 태그 `backup-2026-08-23-before-rebuild` 를 보면 된다.

## 저장하지 않는 것

로그인, 이름 입력, 서버 전송 — 전부 없다. 진도는 각자 브라우저에만 남는다.

## 함께 있는 자매 사이트

국어: <https://sikke12632.github.io/5-2korean/> (`sikke12632/5-2korean`)
같은 방식(JSON → 빌드)으로 만든다. 조각 종류와 색만 다르다.
