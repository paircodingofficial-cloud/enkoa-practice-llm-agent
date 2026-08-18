# 실행: uv run streamlit run 교안_02_챗봇과_연동/03_RAG_연동.py
#
# 교안 02: 기존 RAG 시스템 연동 + API 키 관리
# 지난 단원(RAG 파이프라인)에서 만든 검색 기반 답변(core.rag_core)을 UI에 연결하고,
# 검색된 '출처'를 함께 보여 줍니다.

import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "core").is_dir()),
    Path(__file__).resolve().parent,
)
sys.path.insert(0, str(PROJECT_ROOT))
from core import rag_core
from core.keys import require_openai_key_or_stop

st.title("📗 기존 RAG 시스템 연동")
st.caption("core.rag_core 로 문서 기반 답변과 출처를 보여 줍니다.")

# 이 화면은 실제 OpenAI 임베딩·생성을 호출한다. 키가 없으면 안내를 띄우고 여기서 멈춘다.
require_openai_key_or_stop()

st.divider()

# =============================================================================
st.header("1. 연동할 RAG 시스템 살펴보기")
st.markdown(
    """
`core/rag_core.py` 는 서비스 FAQ 문서(`data/faq_docs.csv`)에 대한 RAG 입니다. 역시 **그대로 씁니다**.

- `rag_core.search(question, k)` → 관련 문서 상위 k개 `[{id, title, text, score}]`
- `rag_core.ask(question, k)` → `{"answer": 답변, "sources": [관련 문서...]}`
- `rag_core.is_live()` → API 키가 준비됐는지 확인(키가 없으면 검색·답변 대신 오류를 냅니다)

RAG의 핵심 가치는 **답변의 근거(출처)를 함께 제시**해 환각을 줄이는 것입니다.
"""
)
st.code(
    '''from core import rag_core

# 버튼을 눌렀을 때만 검색·생성을 부른다. 화면을 열 때마다 API 를 부르면 요금이 샌다.
if st.button("예시 질문으로 물어보기"):
    result = rag_core.ask("비밀번호를 잊어버렸어요")
    st.write(result["answer"])
    st.write("출처:", [s["title"] for s in result["sources"]])''',
    language="python",
)
st.caption("▼ 실제 실행 결과: 버튼을 누르면 실제 검색·생성이 돕니다")
if st.button("예시 질문으로 물어보기"):
    result = rag_core.ask("비밀번호를 잊어버렸어요")
    st.write(result["answer"])
    st.write("출처:", [s["title"] for s in result["sources"]])

st.divider()

# =============================================================================
st.header("2. 문서 Q&A 화면 만들기: 답변 + 출처")
st.markdown(
    "질문을 받아 `ask` 로 답하고, 근거 문서를 `st.expander` 안에 제목·유사도 점수·본문으로 보여 줍니다."
)

st.code(
    '''question = st.text_input("FAQ에 대해 물어보세요", placeholder="예: 파일 용량 제한이 얼마인가요?")
top_k = st.slider("참고할 문서 수", 1, 5, 3)

if question:
    result = rag_core.ask(question, k=top_k)
    st.markdown("### 답변")
    st.write(result["answer"])

    st.markdown("### 근거 문서")
    for s in result["sources"]:
        with st.expander(f"{s['title']}  (유사도 {s['score']})"):
            st.write(s["text"])''',
    language="python",
)
st.caption("▼ 실제 실행 결과")
question = st.text_input("FAQ에 대해 물어보세요", placeholder="예: 파일 용량 제한이 얼마인가요?")
top_k = st.slider("참고할 문서 수", 1, 5, 3)
if question:
    result = rag_core.ask(question, k=top_k)
    st.markdown("### 답변")
    st.write(result["answer"])
    st.markdown("### 근거 문서")
    for s in result["sources"]:
        with st.expander(f"{s['title']}  (유사도 {s['score']})"):
            st.write(s["text"])

# 🖐️ 직접 해보기: 참고 문서 수 슬라이더를 1과 5로 바꿔 같은 질문을 다시 물어 보세요.
#               근거 문서가 늘면 답이 더 좋아지는지, 아니면 관계없는 문서까지 딸려 오는지 비교해 보세요.
#               FAQ 에 없는 것(예: 환불 정책)을 물으면 어떻게 답하는지도 확인해 보세요.

st.divider()

# =============================================================================
st.header("3. API 키 관리: st.secrets")
st.markdown(
    """
실제 OpenAI 모델을 쓰려면 API 키가 필요합니다. 키는 **코드에 절대 적지 않고** 따로 보관합니다.
Streamlit 표준 방식은 프로젝트에 `.streamlit/secrets.toml` 을 두고 `st.secrets` 로 읽는 것입니다.

```toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "sk-..."
```

- **로컬**: 위 파일을 만들어 둡니다(`.gitignore` 에 있어 커밋되지 않습니다).
- **Streamlit Cloud 배포**: 앱 설정의 **Secrets** 에 같은 내용을 붙입니다. 코드는 그대로 둡니다.

한 가지 옮기는 단계가 필요합니다. LangChain 의 `ChatOpenAI`·`OpenAIEmbeddings` 는
`st.secrets` 를 보지 않고 **`OPENAI_API_KEY` 환경변수**를 읽습니다. 그래서 secrets 에서 읽은 값을
환경변수로 넘겨 줘야 합니다. `core/keys.py` 가 그 일을 합니다.
"""
)
st.markdown("`core/keys.py` 가 하는 일(요지):")
st.code(
    '''def _from_st_secrets():
    try:
        return st.secrets["OPENAI_API_KEY"]
    except (StreamlitSecretNotFoundError, KeyError):
        return None                             # 파일이 없으면 조회 자체가 예외다

def load_key():
    if os.getenv("OPENAI_API_KEY"):
        return                                  # 이미 있으면 그대로 둔다
    key = _from_st_secrets() or _from_unit_folder()
    if key:
        os.environ["OPENAI_API_KEY"] = key      # LangChain 이 읽는 자리로 옮긴다''',
    language="python",
)
st.caption(
    "읽는 곳이 두 군데인 이유: `st.secrets` 는 **앱을 실행한 폴더** 기준으로 secrets 파일을 찾습니다. "
    "이 자료는 단원 폴더에서도, 실습자료 루트에서도 실행하므로 "
    "`_from_unit_folder()` 가 단원 폴더의 파일을 절대경로로 한 번 더 확인합니다."
)
st.warning(
    "함정: secrets 파일이 **아예 없으면** `st.secrets` 는 조회하는 순간 예외를 냅니다. "
    "`if \"OPENAI_API_KEY\" in st.secrets:` 같은 확인조차 예외가 나므로, 위처럼 **try 로 감싸야** 합니다."
)
st.markdown("앱 첫머리에서 키를 확인하고, 없으면 그 자리에서 멈춥니다:")
st.code(
    '''from core.keys import require_openai_key_or_stop

require_openai_key_or_stop()   # 키가 없으면 st.error 안내 후 st.stop()
st.success("OpenAI 연결됨")''',
    language="python",
)
st.caption("▼ 실제 실행 결과: 여기까지 화면이 보인다면 키가 준비된 것입니다")
require_openai_key_or_stop()
st.success("OpenAI 연결됨")

st.divider()

# =============================================================================
st.header("4. 무거운 준비는 st.cache_resource 로 한 번만")
st.markdown(
    "검색 인덱스·모델처럼 무거운 자원은 재실행마다 다시 만들면 느립니다. `@st.cache_resource` 로 "
    "**한 번만** 만들어 공유하세요. (교안 01-05 복습)"
)
st.code(
    '''@st.cache_resource
def get_rag():
    # 실제로는 인덱스를 만들어 반환. 여기서는 모듈을 그대로 공유.
    return rag_core

rag = get_rag()   # 처음 한 번만 준비, 이후 재사용
st.write("RAG 준비 완료:", rag is rag_core)''',
    language="python",
)
st.caption("▼ 실제 실행 결과")


@st.cache_resource
def get_rag():
    return rag_core


rag = get_rag()
st.write("RAG 준비 완료:", rag is rag_core)

# 🖐️ 직접 해보기: get_rag 에 st.write("준비 중...") 한 줄을 넣고 화면을 여러 번 새로고침해 보세요.
#               그 문구가 몇 번 나오는지 세어 보면 캐시가 도는 것을 눈으로 확인할 수 있습니다(확인 후 되돌리기).

st.divider()
st.subheader("이번 강의 정리")
st.markdown(
    """
- `rag_core.ask` 로 **답변 + 출처**를 함께 표시(환각 완화)
- 근거 문서는 `st.expander` 에 제목·유사도·본문으로
- API 키는 `.streamlit/secrets.toml`(로컬)·Cloud Secrets(배포)에 두고 `st.secrets` 로 읽는다. 코드에 넣지 않는다
- 무거운 인덱스는 `@st.cache_resource` 로 한 번만
"""
)
st.markdown("⏭️ **다음 시간**: 여러 페이지를 하나로 (`교안_02_챗봇과_연동/04_멀티페이지_데모/`)")
