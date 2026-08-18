# 실행: uv run streamlit run 교안_02_챗봇과_연동/02_챗봇_연동.py
#
# 교안 02: 기존 챗봇 시스템 연동
# 지난 단원(LangChain)에서 만든 챗봇(core.chatbot_core)을 채팅 UI에 '연결'합니다.
# 핵심: 챗봇 로직은 새로 만들지 않는다. 이미 있는 함수를 import 해서 UI에만 얹는다.

import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import sys
from pathlib import Path

import streamlit as st

# [제공 코드] core 를 import 하기 위해 프로젝트 루트를 경로에 추가합니다.
PROJECT_ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "core").is_dir()),
    Path(__file__).resolve().parent,
)
sys.path.insert(0, str(PROJECT_ROOT))
from core import chatbot_core
from core.keys import require_openai_key_or_stop

st.title("📗 기존 챗봇 시스템 연동")
st.caption("core.chatbot_core 를 채팅 UI에 연결합니다.")

# 이 화면은 실제 OpenAI 모델을 호출한다. 키가 없으면 안내를 띄우고 여기서 멈춘다.
require_openai_key_or_stop()

st.divider()

# =============================================================================
st.header("1. 연동할 기존 시스템 살펴보기")
st.markdown(
    """
`core/chatbot_core.py` 에는 지난 단원에서 만든 챗봇 함수가 이미 있습니다. 우리는 이걸 **그대로 씁니다**.

- `chatbot_core.stream_reply(message, history)` → 답변을 **토큰(조각) 단위로 스트리밍**하는 제너레이터
- `chatbot_core.reply(message, history)` → 답변 **전체 문자열**
- `chatbot_core.is_live()` → API 키가 준비됐는지 확인(키가 없으면 답변 대신 오류를 냅니다)

`history` 는 `[{"role": "user"/"assistant", "content": "..."}]` 형식입니다.
"""
)
st.code(
    '''from core import chatbot_core

# 버튼을 눌렀을 때만 모델을 부른다. 화면을 열 때마다 API 를 부르면 요금이 샌다.
if st.button("챗봇에게 인사해 보기"):
    st.write(chatbot_core.reply("안녕하세요", []))''',
    language="python",
)
st.caption("▼ 실제 실행 결과: 버튼을 누르면 실제 모델이 답합니다")
if st.button("챗봇에게 인사해 보기"):
    st.write(chatbot_core.reply("안녕하세요", []))

st.info(
    "이 챗봇은 **실제 OpenAI 모델**을 호출합니다. 대신 도는 가짜 응답은 없습니다.\n\n"
    "키 준비: 1) 단원 폴더에서 `cp .streamlit/secrets.toml.example .streamlit/secrets.toml` "
    "2) 그 파일에 본인 키(https://platform.openai.com/api-keys) 입력 3) 앱 다시 실행.\n\n"
    "키가 없으면 화면에 안내가 뜨고 앱이 그 자리에서 멈춥니다."
)

st.divider()

# =============================================================================
st.header("2. Echo 봇의 답변만 진짜 챗봇으로 교체")
st.markdown(
    """
지난 시간 Echo 봇에서 답변을 만드는 한 줄만 바꾸면 됩니다.

- 이전: `answer = f"당신은 '{prompt}' 라고 했습니다."`
- 이제: `chatbot_core.stream_reply(prompt, 이력)` 을 `st.write_stream` 에 넘겨 **스트리밍**
  (이력에는 방금 넣은 내 메시지를 빼고 넘깁니다. 그 문장은 첫 번째 인자로 이미 가니까요)

`st.write_stream` 은 스트리밍이 끝나면 **완성된 전체 문자열을 반환**하므로, 그 값을 이력에 저장합니다.
"""
)

st.code(
    '''# 1. 대화 이력 준비
if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. 저장된 이력을 모두 다시 그리기
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 3. 새 입력 → 기존 챗봇 연동
if prompt := st.chat_input("무엇이든 물어보세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        # 기존 시스템의 스트리밍 함수를 그대로 st.write_stream 에 연결.
        # 이력에서 방금 넣은 내 메시지는 뺀다. 그 문장은 첫 번째 인자로 이미 전달된다.
        answer = st.write_stream(
            chatbot_core.stream_reply(prompt, st.session_state.messages[:-1])
        )
    st.session_state.messages.append({"role": "assistant", "content": answer})''',
    language="python",
)
st.caption("▼ 실제 실행 결과: 아래 입력창에 말을 걸어 보세요")

if "messages" not in st.session_state:
    st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
if prompt := st.chat_input("무엇이든 물어보세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        # 이력에서 방금 넣은 내 메시지는 뺀다. 그 문장은 첫 번째 인자로 이미 전달된다.
        answer = st.write_stream(
            chatbot_core.stream_reply(prompt, st.session_state.messages[:-1])
        )
    st.session_state.messages.append({"role": "assistant", "content": answer})

# 🖐️ 직접 해보기: stream_reply 에 넘기는 이력에서 [:-1] 을 떼고 두세 마디를 주고받아 보세요.
#               모델이 같은 문장을 두 번 받게 됩니다. 답이 어색해지는지 관찰한 뒤 되돌리세요.
#               (질문 한 번이 실제 요금이 나가는 호출이라는 점도 기억하세요.)

st.divider()

# =============================================================================
st.header("3. 사이드바에 '대화 초기화' 버튼")
st.markdown("대화 이력은 결국 `session_state` 리스트이므로, 비우면 새 대화가 됩니다.")

st.code(
    '''with st.sidebar:
    st.header("설정")
    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.rerun()   # 즉시 화면을 다시 그려 반영''',
    language="python",
)
st.caption("▼ 실제 실행 결과: 사이드바의 버튼으로 대화를 비웁니다")
with st.sidebar:
    st.header("설정")
    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.rerun()

# 🖐️ 직접 해보기: st.rerun() 줄을 잠시 지우고 초기화 버튼을 눌러 보세요.
#               이력은 비워졌는데 화면은 그대로입니다. 한 박자 늦게 반영되는 이유를 생각한 뒤 되돌리세요.

st.divider()
st.subheader("이번 강의 정리")
st.markdown(
    """
- 챗봇 로직은 **새로 만들지 않고** `core.chatbot_core` 를 import 해서 UI에만 연결
- Echo 봇의 답변 한 줄을 `st.write_stream(chatbot_core.stream_reply(...))` 로 교체
- `st.write_stream` 은 완성 답변을 반환 → 이력에 저장
- 대화 초기화 = `session_state.messages` 를 비우고 `st.rerun()`
"""
)
st.markdown("⏭️ **다음 시간**: 기존 RAG 연동과 API 키 관리 (`교안_02_챗봇과_연동/03_RAG_연동.py`)")
