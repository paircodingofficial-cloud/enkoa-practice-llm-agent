# 멀티페이지 데모: 챗봇 페이지 (core.chatbot_core 연동)
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
from core import chatbot_core
from core.keys import require_openai_key_or_stop

st.title("💬 챗봇")

# 실제 OpenAI 호출이 필요한 페이지: 키가 없으면 안내를 띄우고 여기서 멈춘다.
require_openai_key_or_stop()

st.caption("OpenAI 연결됨 · 실제 모델이 답변합니다.")

# 페이지 간 공유되는 대화 이력(자립적 초기화)
if "messages" not in st.session_state:
    st.session_state.messages = []

# main.py 로 열면 main.py 가 잡아 둔 자리에, 이 파일만 단독 실행하면 사이드바에 바로 그린다.
slot = st.session_state.get("sidebar_slot")
with (slot.container() if slot else st.sidebar):
    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.rerun()

# 이력 다시 그리기
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 새 입력 → 기존 챗봇 연동(스트리밍)
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
