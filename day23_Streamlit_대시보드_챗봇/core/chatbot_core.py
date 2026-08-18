# [제공 코드]
"""chatbot_core: '기존 챗봇 시스템' (LangChain 대화형 챗봇).

지난 단원(LangChain LCEL·Memory)에서 만든 챗봇이라고 생각하세요.
이 단원에서는 이 함수를 Streamlit 채팅 UI에 **연결**하기만 하면 됩니다.

이 모듈은 **실제 OpenAI 호출만** 합니다. 키가 없을 때 대신 도는 가짜 응답 경로는 없습니다.
키가 없으면 `stream_reply` 가 안내와 함께 `RuntimeError` 를 냅니다
(앱은 그 전에 `core.keys.require_openai_key_or_stop()` 으로 화면에 안내를 띄우고 멈춥니다).
"""

import os
from typing import Iterator

from core.keys import MISSING_KEY_MESSAGE, load_key

SYSTEM_PROMPT = "당신은 한국어로 친절하고 간결하게 답하는 도우미입니다."


def is_live() -> bool:
    """실제 OpenAI 연동이 가능한 상태인지(키가 설정됐는지) 알려줍니다.

    UI 가 '키 없음'을 감지해 안내를 띄울 때 씁니다. 답변 경로를 바꾸는 스위치가 아닙니다.
    """
    load_key()
    return bool(os.getenv("OPENAI_API_KEY"))


def build_chain():
    """프롬프트 · 모델 · 출력 파서를 이어 붙인 체인을 만들어 돌려줍니다.

    만드는 데 시간이 드는 준비물이라 **매 메시지마다 새로 만들 필요가 없습니다**.
    이 함수는 캐싱하지 않습니다. 캐싱은 이 함수를 부르는 쪽이 정합니다
    (Streamlit 앱이라면 `@st.cache_resource`, 일반 스크립트라면 변수에 담아 두기).

    Raises:
        RuntimeError: OPENAI_API_KEY 가 없을 때.
    """
    if not is_live():
        raise RuntimeError(MISSING_KEY_MESSAGE)

    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_openai import ChatOpenAI

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("history"),
            ("human", "{input}"),
        ]
    )
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    return prompt | model | StrOutputParser()


def stream_reply(message: str, history: list[dict] | None = None, chain=None) -> Iterator[str]:
    """사용자 메시지에 대한 답변을 토큰(문자열 조각) 단위로 스트리밍합니다.

    Args:
        message: 이번 사용자 입력.
        history: 이전 대화 [{"role": "user"/"assistant", "content": ...}, ...].
        chain: 미리 만들어 둔 체인. 주지 않으면 이 호출에서 새로 만듭니다.
            같은 체인을 계속 쓰려면 앱에서 한 번 만들어 넘기세요.
    Yields:
        답변 텍스트 조각. `st.write_stream()` 에 그대로 넘길 수 있습니다.
    Raises:
        RuntimeError: OPENAI_API_KEY 가 없을 때(가짜 응답으로 대신 돌지 않습니다).
    """
    chain = chain or build_chain()

    # history(딕셔너리 리스트)를 LangChain 메시지 튜플로 변환
    past = [(m["role"], m["content"]) for m in (history or [])]
    for token in chain.stream({"history": past, "input": message}):
        yield token


def reply(message: str, history: list[dict] | None = None) -> str:
    """스트리밍이 필요 없을 때 쓰는 전체 답변 문자열 버전."""
    return "".join(stream_reply(message, history))
