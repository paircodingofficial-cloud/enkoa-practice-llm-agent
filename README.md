# LLM·에이전트 실습자료

엔코아 AI캠퍼스 「데이터 분석 & AI 머신러닝 캠프」 **LLM 활용** 실습용 주피터 노트북입니다.
수업 진도에 맞춰 자료가 추가됩니다.

### 수록 자료

| 일차 | 주제 | 배우는 것 |
|---|---|---|
| **day14** | OpenAI API 활용 | 답변 생성 원리·Chat/Responses API·파라미터·사고모드·스트리밍, 프롬프트 엔지니어링·Function Calling·구조화된 출력, 텍스트 정형화(문의 분류·개인정보 마스킹·설문 표준화), 이미지 이해·정형화(패션·영수증 OCR) |
| **day15** | RAG·벡터 검색 | RAG 아키텍처(질문→검색기→생성기)·환각과 최신성·인덱싱 타임 vs 쿼리 타임, 직접 만드는 코사인 Top-K 검색기와 선형 스캔의 한계, ChromaDB 구축·적재·Top-K 검색·메타데이터 필터(`$in`·`$and`·범위·`where_document`), 근사 최근접 탐색(ANN)·HNSW, Qdrant 로 재현·솔루션 비교, **검색 결과를 근거로 LLM 이 답을 쓰게 해 RAG 완성** |
| **day16** | RAG 파이프라인 | 텍스트 청킹 전략, 문서 로딩→임베딩→벡터 검색→생성 통합, 검색 근거로 답을 쓰게 하는 마지막 단계 완성, 기초 검색 품질 지표(Hit@K·Precision@K·Recall@K·MRR)로 파이프라인 점검 |
| **day17** | 데이터베이스·SQL | **sqlite** 로 배우는 관계형 DB — 데이터 타입·제약조건·PK/FK·1:1·1:N·M:N·ERD(까마귀발) 설계, `INSERT`·파라미터 바인딩(`executemany`)·`ALTER TABLE`, 조회/정렬/집계·`GROUP BY`·`HAVING`·적는 순서 vs 실행 순서, 트랜잭션(`BEGIN`·`COMMIT`·`ROLLBACK`)·`JOIN`/`LEFT JOIN`·인덱스·서브쿼리(상관 서브쿼리 포함), 그리고 **Supabase(PostgreSQL)+pgvector** 로 옮겨 가 임베딩 적재·HNSW 인덱스·`rpc` 로 의미 검색·분류 조건과 겹친 결합 검색까지 |
| **day18** | LangChain 기본 구조 | 부품 표준화(`ChatOpenAI`)·메시지(`SystemMessage`/`HumanMessage`)와 **이미지 입력**, 프롬프트 템플릿과 **프롬프트를 YAML 파일로 관리**, 출력 파서, **LCEL 체인**(`프롬프트 \| 모델 \| 파서`)·`invoke`/`batch`/`stream`, 작은 체인을 이어 큰 체인 만들기(다리 부품), `RunnableLambda`·`RunnableParallel`·`RunnablePassthrough`, **대화 기록(단기 기억)** 과 트리밍, **장기 기억**(벡터 저장소 저장·회상)과 무엇을 기억할지 모델이 판단하기, `while` 멀티턴 상담 워크플로우 |
| **day19** | LangChain 에이전트·도구 | 구조화된 출력(`with_structured_output`)으로 정형화를 한 줄로, **`@tool` 도구 정의**(docstring=명세·타입힌트=인자·모델에 넘어가는 JSON 명세), `create_agent` 와 **메시지 궤적**(사람→AI 도구호출→도구결과→AI 답)·`system_prompt`·`response_format`, 도구를 만들 때 지킬 것(**실패도 문자열로**·권한은 좁게)과 실무형 도구 3종(사내 조회·규칙 계산·외부 REST API), **RAG 를 LangChain 부품으로 재조립**(`Document`·`RecursiveCharacterTextSplitter`·`HuggingFaceEmbeddings`·`Chroma`·`as_retriever`)과 LCEL RAG 체인·근거 함께 반환(`RunnableParallel`), **Text-to-SQL**(스키마 설명이 모델의 눈·두 겹 가드=문자열 검사+읽기 전용 연결·구조화 출력으로 SQL+근거) |
| **day20** | ReAct·멀티툴 에이전트 | **ReAct 세 박자**(생각·행동·관찰)와 기록의 대응(AIMessage=생각+행동 / ToolMessage=관찰)·`agent.stream`, 답이 있는 곳이 서로 다른 도구 셋을 한 창구로 — **문서를 도구로**(조각 꼬리표의 번호로 **앞뒤 조각까지 이어 붙여** 문맥 복원·근거 제한·쪽 번호 출처 표기)·**표를 도구로**(Text-to-SQL·두 겹 가드)·**외부 REST API**(실패도 문자열로), `if` 없이 **설명으로 라우팅**·동시 호출·다단계 연쇄, 도구 선택이 어긋날 때의 **4증상**(안 부름·잘못 고름·조용한 실패·과다 호출) 진단과 처방, 저장소를 Supabase(pgvector)로 교체. 그리고 **만들었으면 잰다** — 평가셋 3요소·라벨은 **조각**에·`Hit@K`·`Precision@K`·`Recall@K`·`MRR` 손구현과 읽는 법·K 트레이드오프·**재고 나서 고칠 자리 찾기**, 마지막으로 **평가셋을 직접 만들기**(라벨링 4단계·전체 재라벨링·점검 7항목) |
| **day21** | MCP·계획 실행 자동화 | **MCP**(우리가 만들지 않은 도구를 규격으로 붙인다). 서버 설정 한 딕셔너리(`command`·`args`·`transport`)로 파일시스템·웹검색·브라우저·DB·코드 실행을 에이전트에 쥐여 주기, 도구 명세 읽기·직접 호출·**비동기 전용**(`ainvoke`), 권한은 말이 아니라 **넘기는 도구 목록**으로, 여러 서버를 한 클라이언트에(`tool_name_prefix` 로 이름 충돌 차단), 원격 HTTP 서버(Context7)로 **최신 문서 조회**. 그리고 **미들웨어**로 에이전트 루프를 확장한다. 여섯 메서드와 `before_`/`after_` 대 `wrap_` 의 차이, `TodoListMiddleware` 로 **Plan-and-Execute**(계획을 문서로 남기고 단계별 실행), `ModelCallLimitMiddleware` 로 반복 호출 상한, **프롬프트 한 문단이 도구 선택을 바꾸는 것**을 A/B 로 확인, 결과 정형화로 표·JSON 적재 |
| **day22** | 에이전트 품질·관측성 | **계획 실행 자동화**(`TodoListMiddleware` 로 계획을 세우고 MCP 도구로 조회·계산·그래프·리포트를 한 번에, 결과를 구조화된 출력으로 적재). **Self-reflection 루프**(생성 → 비평 → 수정을 임계 점수·최대 반복까지 돌려 품질을 올리기, 한 번에 쓴 글과 비교). **관측성**(무엇을 남기고 무엇에 답하는가, Langfuse 와 LangSmith 중 무엇을 왜 고르는가, trace·span·generation 계층, `CallbackHandler` 를 `config` 에 얹어 대시보드에서 확인, `usage_metadata` 로 토큰·비용 집계, 프롬프트를 서버에 **버전·라벨로** 올리고 불러와 실행에 쓰기). **운영 견고성**(예외 처리 → 재시도 → 폴백의 사다리, LiteLLM 으로 죽은 모델을 살아 있는 모델로 자동 전환). 마지막으로 **메시지 기록으로 라우팅 실패를 재현**하고 도구 설명(docstring)만 고쳐 호출이 달라지는 것을 확인 |

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

> **어디에 필요한가** — day14·day16·**day18** 은 전부, day15 는 **생성 부분만**입니다(교안_03 · 과제 LV2 11번 · LV3 4번).
> day15 의 검색 부분(교안_01·02 와 나머지 과제)은 임베딩 모델을 내려받아 로컬에서 돌리고 벡터 DB 도
> 메모리 모드라 **키 없이 그대로 풀립니다.**
> day17 은 **과제 LV3 의 답변 생성에서만** 이 키를 씁니다.
> day18 은 모든 노트북이 실제 호출을 하지만 짧은 문장 수십 건이라 비용은 아주 적습니다
> (장기 기억 절의 임베딩은 로컬 모델이라 요금이 들지 않습니다).

> **day19·day20 은 전부 실호출입니다.** 에이전트가 루프를 돌며 모델을 여러 번 부릅니다. day20 은 도구 하나가 **공휴일 REST API** 를 부르므로 인터넷 연결도 필요하고(키는 불필요), 과제 LV2 9번만 **SQL 단원에서 만든 Supabase 접속 정보**를 씁니다 — 없으면 그 문제만 건너뜁니다.
> 검색 평가 교안(day20 교안_02)은 **모델을 한 번도 부르지 않습니다** — 임베딩과 검색만 씁니다.
>
> **day21 은 MCP 서버를 그때그때 띄웁니다.** `npx`(Node.js)와 `uvx`(uv)가 필요하고, 첫 실행은 서버 패키지를 받느라 느립니다. 브라우저 실습(03)만 크로미움 설치가 한 번 필요합니다 (`npx playwright install chromium`). 원격 문서 조회(Context7)는 인터넷만 있으면 되고 키는 없습니다.

### 3. day17 만 — Supabase 프로젝트 (교안_03 · 과제 LV3)

day17 의 앞부분(교안_01·02, 과제 LV1·LV2)은 **sqlite** 라 가입도 설치도 필요 없습니다.
벡터를 다루는 뒷부분만 **Supabase(PostgreSQL)+pgvector** 를 씁니다.

1. [supabase.com](https://supabase.com) 가입 → **New project** (Region `ap-northeast-2 (Seoul)`)
2. **Project Settings → API** 에서 **Project URL** 과 **anon public key** 복사
3. `day17_데이터베이스_SQL/.env` 에 `SUPABASE_URL`·`SUPABASE_ANON_KEY` 를 채웁니다
4. **SQL Editor** 에서 준비 SQL 실행 — 교안_03 은 `data/setup_supabase.sql`, 과제 LV3 은 `data/setup_travel.sql`
   (**서로 다른 파일**이고, 같은 프로젝트에 표만 새로 만듭니다)

자세한 순서는 `day17_데이터베이스_SQL/실습_가이드.md` 의 **0. 준비** 를 따라가세요.

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
day16_RAG_파이프라인/      RAG 파이프라인
day17_데이터베이스_SQL/    데이터베이스·SQL (sqlite → Supabase·pgvector)
day18_LangChain_기본구조/  LangChain 기본 구조 (모델·프롬프트·파서·LCEL·Runnable·Memory)
day19_LangChain_에이전트_툴/  LangChain 에이전트·도구 (구조화 출력·@tool·create_agent·RAG 체인·Text-to-SQL)
day20_ReAct_멀티툴_에이전트/  ReAct·멀티툴 에이전트 (도구 셋 라우팅·검색 평가·평가셋 구축)
day21_Agent_데이터분석_자동화/  MCP 클라이언트·계획 실행 자동화 (서버 다섯 종·미들웨어·Plan-and-Execute)
```

각 일차 폴더 안에 교안·과제 노트북과 `data/`·`images/`·`실습_가이드.md` 가 들어 있습니다.

---

## 참고 — 공식 문서

- 가격표 — https://developers.openai.com/api/docs/pricing
- 모델 목록·사양 — https://developers.openai.com/api/docs/models
- 텍스트 생성 가이드 — https://developers.openai.com/api/docs/guides/text
- Function calling — https://developers.openai.com/api/docs/guides/function-calling
- 구조화된 출력 — https://developers.openai.com/api/docs/guides/structured-outputs
