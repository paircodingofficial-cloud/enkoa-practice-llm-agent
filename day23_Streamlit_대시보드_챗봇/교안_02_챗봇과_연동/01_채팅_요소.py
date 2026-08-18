# 실행: uv run streamlit run 교안_02_챗봇과_연동/01_채팅_요소.py
#
# 교안 02: 채팅 UI 요소
# 대화형 AI의 화면은 st.chat_message · st.chat_input · st.write_stream 세 가지로 만듭니다.

import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import time

import streamlit as st

st.title("📗 채팅 UI 요소")
st.caption("메시지 말풍선·입력창·스트리밍으로 챗봇 화면을 만듭니다.")

st.divider()

# =============================================================================
st.header("1. st.chat_message: 말풍선")
st.markdown(
    "`st.chat_message(role)` 은 발화자(`user`/`assistant`)별 **말풍선**을 만듭니다. "
    "`with` 블록 안에 그 말풍선의 내용을 넣습니다."
)

st.code(
    '''with st.chat_message("user"):
    st.write("안녕하세요!")
with st.chat_message("assistant"):
    st.write("무엇을 도와드릴까요?")''',
    language="python",
)
st.caption("▼ 실제 실행 결과")
with st.chat_message("user"):
    st.write("안녕하세요!")
with st.chat_message("assistant"):
    st.write("무엇을 도와드릴까요?")

st.divider()

# =============================================================================
st.header("2. st.chat_input: 입력창")
st.markdown(
    "`st.chat_input` 은 채팅 입력창을 만들고, 사용자가 엔터를 치면 그 문자열을, "
    "아니면 `None` 을 반환합니다. `if prompt := st.chat_input(...)` 패턴을 씁니다."
)
st.info(
    "**입력창이 그려지는 자리**: 스크립트 맨 바깥에서 부르면 화면 **맨 아래에 고정**됩니다. "
    "챗봇 앱은 화면이 하나뿐이라 그게 자연스럽습니다. "
    "반면 `st.container()`·탭·사이드바 **안에서** 부르면 부른 그 자리에 그려집니다. "
    "이 교안은 한 파일에 예제가 여러 개라, 예제마다 제자리에 보이도록 컨테이너 안에서 부릅니다."
)

st.code(
    '''with st.container():
    if prompt := st.chat_input("메시지를 입력하세요"):
        st.write(f"입력한 내용: {prompt}")''',
    language="python",
)
st.caption("▼ 실제 실행 결과: 아래 입력창에 무언가 입력해 보세요")
with st.container():
    if prompt := st.chat_input("메시지를 입력하세요"):
        st.write(f"입력한 내용: {prompt}")

st.divider()

# =============================================================================
st.header("3. st.write_stream: 한 글자씩 스트리밍")
st.markdown(
    "LLM 답변처럼 **조금씩 흘러나오는** 텍스트는 `st.write_stream` 에 제너레이터(문자열 조각을 "
    "차례로 내놓는 함수)를 넘기면 타이핑되듯 출력됩니다."
)

st.code(
    '''def stream_words():
    """문장을 단어 단위로 조금씩 흘려보낸다(스트리밍 흉내)."""
    for word in "안녕하세요 스트리밍 출력 예시입니다".split():
        yield word + " "
        time.sleep(0.1)

if st.button("스트리밍 시작"):
    st.write_stream(stream_words())''',
    language="python",
)
st.caption("▼ 실제 실행 결과: 버튼을 누르면 단어가 하나씩 나타납니다")


def stream_words():
    """문장을 단어 단위로 조금씩 흘려보낸다(스트리밍 흉내)."""
    for word in "안녕하세요 스트리밍 출력 예시입니다".split():
        yield word + " "
        time.sleep(0.1)


if st.button("스트리밍 시작"):
    st.write_stream(stream_words())

# 🖐️ 직접 해보기: stream_words 의 time.sleep 값을 0.5 로 키워 스트리밍을 눈으로 따라가 보세요.
#               yield 뒤의 " " 를 지우면 왜 단어가 붙어 나오는지도 확인해 보세요.

st.divider()

# =============================================================================
st.header("4. 세 요소를 합치기: Echo 챗봇")
st.markdown(
    """
이제 하나로 합칩니다. 챗봇의 뼈대는 항상 같습니다.

1. `st.session_state` 에 대화 이력(리스트)을 준비
2. 저장된 이력을 **모두 다시 그린다**(재실행 모델!)
3. `chat_input` 으로 새 입력을 받아 이력에 추가하고, 답변을 만들어 이력에 추가

아래는 입력을 그대로 되돌려 주는 **Echo 봇**입니다. 다음 시간에 이 답변 부분만
진짜 AI(`core.chatbot_core`)로 바꿉니다.
"""
)

st.code(
    '''# 1. 대화 이력 준비
if "echo_messages" not in st.session_state:
    st.session_state.echo_messages = []

# 2. 저장된 이력을 모두 다시 그린다
for msg in st.session_state.echo_messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 3. 새 입력 처리 (컨테이너 안이라 이 자리에 입력창이 그려진다)
with st.container():
    if prompt := st.chat_input("아무 말이나 해보세요", key="echo_input"):
        st.session_state.echo_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        answer = f"당신은 '{prompt}' 라고 했습니다."   # ← 나중에 AI 답변으로 교체
        st.session_state.echo_messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.write(answer)''',
    language="python",
)
st.caption("▼ 실제 실행 결과: 아래 입력창에 말을 걸면 되돌려 줍니다")

if "echo_messages" not in st.session_state:
    st.session_state.echo_messages = []
for msg in st.session_state.echo_messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
with st.container():
    if prompt := st.chat_input("아무 말이나 해보세요", key="echo_input"):
        st.session_state.echo_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        answer = f"당신은 '{prompt}' 라고 했습니다."
        st.session_state.echo_messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.write(answer)

# 🖐️ 직접 해보기: 이력을 다시 그리는 for 문을 잠시 주석 처리하고 두세 마디를 주고받아 보세요.
#               직전 대화만 남고 앞의 대화가 사라집니다. 재실행 모델을 몸으로 확인한 뒤 되돌리세요.
#               여유가 되면 답변 문장을 "OO님, ..." 처럼 바꿔 이력에도 그대로 남는지 확인해 보세요.

st.divider()
st.subheader("이번 강의 정리")
st.markdown(
    """
- `st.chat_message(role)` : 발화자별 말풍선
- `st.chat_input` : 채팅 입력창(입력 시 문자열, 아니면 None). 맨 바깥에서 부르면 화면 하단 고정
- `st.write_stream` : 제너레이터를 받아 타이핑하듯 스트리밍
- 챗봇 뼈대 = 이력 준비 → 이력 다시 그리기 → 새 입력 처리(이력에 append)
"""
)
st.markdown("⏭️ **다음 시간**: 기존 챗봇 시스템 연동 (`교안_02_챗봇과_연동/02_챗봇_연동.py`)")
