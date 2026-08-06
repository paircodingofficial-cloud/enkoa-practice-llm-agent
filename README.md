# LLM·에이전트 실습자료

엔코아 AI캠퍼스 「데이터 분석 & AI 머신러닝 캠프」 **LLM 활용** 실습용 주피터 노트북입니다.
수업 진도에 맞춰 자료가 추가됩니다.

### 수록 자료

| 일차 | 주제 | 배우는 것 |
|---|---|---|
| **day14** | OpenAI API 활용 | 답변 생성 원리·Chat/Responses API·파라미터·사고모드·스트리밍, 프롬프트 엔지니어링·Function Calling·구조화된 출력, 텍스트 정형화(문의 분류·개인정보 마스킹·설문 표준화), 이미지 이해·정형화(패션·영수증 OCR) |
| **day15** | RAG·벡터 검색 | RAG 아키텍처(질문→검색기→생성기)·환각과 최신성·인덱싱 타임 vs 쿼리 타임, 직접 만드는 코사인 Top-K 검색기와 선형 스캔의 한계, ChromaDB 구축·적재·Top-K 검색·메타데이터 필터(`$in`·`$and`·범위·`where_document`), 근사 최근접 탐색(ANN)·HNSW, Qdrant 로 재현·솔루션 비교, **검색 결과를 근거로 LLM 이 답을 쓰게 해 RAG 완성** |

---

## ⚠️ 딱 하나만 기억하세요

> ### 배포된 자료는 **읽기 전용**입니다.
> ### 실습은 **`내작업/` 폴더에 복사해서** 하세요.

셀을 실행만 해도 파일이 바뀔 수 있으니, 원본은 건드리지 마세요.

```bash
mkdir -p 내작업
cp -r day15_RAG_벡터검색 내작업/
```

자료가 업데이트되면 `git pull` 로 받습니다. 원본을 고쳐 두면 `pull` 이 충돌로 막힙니다.

---

## 시작하기

### 1. 환경 만들기 — uv

이 저장소는 [uv](https://docs.astral.sh/uv/) 로 파이썬 환경을 관리합니다. `pyproject.toml`·`uv.lock` 이
들어 있으므로 **명령 한 줄이면 수업과 똑같은 환경**이 만들어집니다.

```bash
# uv 가 없다면 먼저 설치 (macOS·Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 저장소를 받은 폴더에서
uv sync            # .venv 생성 + 잠긴 버전 그대로 설치
```

### 2. API 키 넣기

일부 노트북은 실제 OpenAI API 를 호출합니다. 일차 폴더 안에서:

```bash
cp .env.example .env      # 그리고 .env 를 열어 OPENAI_API_KEY 를 채웁니다
```

준비 셀을 실행해 **`키 확인됨`** 이 뜨면 준비가 끝난 것입니다. 이후 셀은 실제 호출이라 요금이 부과됩니다.

> **어디에 필요한가** — day14 는 전부, day15 는 **생성 부분만**입니다(교안_03 · 과제 LV2 11번 · LV3 4번).
> day15 의 검색 부분(교안_01·02 와 나머지 과제)은 임베딩 모델을 내려받아 로컬에서 돌리고 벡터 DB 도
> 메모리 모드라 **키 없이 그대로 풀립니다.**

> 🔐 **`.env` 는 절대 커밋하지 마세요.** `.gitignore` 에 이미 들어 있습니다.
> 키가 새어 나가면 즉시 발급처에서 폐기(rotate)하세요.

---

## 실습 진행 순서

각 일차 폴더의 **`실습_가이드.md`** 를 위에서부터 따라가면 빠짐없이 완주할 수 있습니다.

1. **교안**(`교안_01` 부터 번호 순서대로)을 실행하며 읽습니다.
   - 🖐️ **함께 따라하기** 셀은 **직접 코드를 작성**하는 자리입니다(주석이 순서를 알려 줍니다).
   - ✅ **바로 확인 퀴즈**는 답을 먼저 생각한 뒤 펼쳐 보세요.
2. **과제**를 LV1 → LV2 → LV3 순서로 풉니다.
   - `# 여기에 코드를 작성하세요` 셀을 채우고, 바로 아래 **`# [자가채점]`** 셀을 실행해
     `✅ 통과!` 를 확인합니다.
   - 막히면 지문 아래 **`힌트`** 를 펼치세요.
3. 다 풀었으면 `실습_가이드.md` 맨 아래 **완주 기준**을 체크합니다.

> 과제의 **정답 노트북은 이 저장소에 없습니다**(강사용 저장소에 있습니다).
> 스스로 풀어 본 뒤 수업 시간에 확인하세요.

---

## 폴더 구조

```
day14_OpenAI_API_활용/     OpenAI API 활용
day15_RAG_벡터검색/        RAG·벡터 검색
```

각 일차 폴더 안에 교안·과제 노트북과 `data/`·`images/`·`실습_가이드.md` 가 들어 있습니다.

---

## 참고 — 공식 문서

- 가격표 — https://developers.openai.com/api/docs/pricing
- 모델 목록·사양 — https://developers.openai.com/api/docs/models
- 텍스트 생성 가이드 — https://developers.openai.com/api/docs/guides/text
- Function calling — https://developers.openai.com/api/docs/guides/function-calling
- 구조화된 출력 — https://developers.openai.com/api/docs/guides/structured-outputs
