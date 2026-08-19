# 역사 탐정 수첩 — 사회 5-2

초등 5학년 2학기 사회 차시별 복습 사이트.

## 배포 (GitHub Pages)

1. GitHub에서 새 저장소를 만든다 (Public).
2. 이 폴더의 파일을 전부 업로드한다. (폴더 구조 그대로)
3. 저장소 → Settings → Pages → Source를 `Deploy from a branch`, 브랜치 `main` / `/ (root)` 로 설정.
4. 1~2분 뒤 `https://<계정명>.github.io/<저장소명>/` 에서 열린다.

## 구조

```
index.html          홈 (진행률, 이어서 하기)
unit1.html          1단원 차시 목록
teacher.html        선생님용 안내
lesson/*.html       차시별 복습 (15개)
review/*.html       5차시마다 복습 관문 (4개)
assets/style.css    공통 디자인
assets/app.js       진도 저장, 퀴즈 동작
```

## 차시 추가하기

`lesson/` 에 파일을 넣고 `unit1.html` 목록에 한 줄 추가하면 된다.
2·3단원은 `unit2.html`, `unit3.html` 을 같은 형식으로 만들고 `index.html` 의 단원 목록에서 잠금을 푼다.

## 저장 방식

`localStorage` 키 `sahoe52-v1` 에 `{done, wrong, last}` 저장.
서버 전송 없음. 개인정보 수집 없음.
