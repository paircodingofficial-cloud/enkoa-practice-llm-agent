# [제공 코드]
"""rag_core: '기존 RAG 시스템' (LangChain 검색 기반 답변).

지난 단원(RAG 파이프라인·ChromaDB)에서 만든 RAG라고 생각하세요.
문서 코퍼스는 data/faq_docs.csv (서비스 FAQ)입니다.
이 단원에서는 이 함수를 Streamlit UI에 **연결**하기만 하면 됩니다. RAG를 다시 만들지 않습니다.

이 모듈은 **실제 OpenAI 호출만** 합니다(임베딩 + 생성). 키가 없을 때 대신 도는 키워드 검색 같은
우회 경로는 없습니다. 키가 없으면 안내와 함께 `RuntimeError` 를 냅니다
(앱은 그 전에 `core.keys.require_openai_key_or_stop()` 으로 화면에 안내를 띄우고 멈춥니다).

핵심 함수:
- search(question, k)  -> 관련 문서 리스트 [{id, title, text, score}]
- ask(question, k)     -> {"answer": 답변 문자열, "sources": 관련 문서 리스트}
"""

import os
from functools import lru_cache
from pathlib import Path

import pandas as pd

from core.keys import MISSING_KEY_MESSAGE, load_key

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "faq_docs.csv"


def is_live() -> bool:
    """실제 OpenAI 임베딩·LLM 연동이 가능한 상태인지 알려줍니다.

    UI 가 '키 없음'을 감지해 안내를 띄울 때 씁니다. 검색·답변 경로를 바꾸는 스위치가 아닙니다.
    """
    load_key()
    return bool(os.getenv("OPENAI_API_KEY"))


def _require_key() -> None:
    """키가 없으면 안내와 함께 중단합니다(가짜 검색·답변으로 대신 돌지 않습니다)."""
    if not is_live():
        raise RuntimeError(MISSING_KEY_MESSAGE)


# @lru_cache 는 함수 결과를 기억해 두고, 같은 인자로 다시 부르면 실행하지 않고 그 결과를 돌려준다.
#   maxsize=1 은 "기억할 결과를 하나만 둔다"는 뜻이다. 인자가 없는 함수라 결과도 하나뿐이라 1로 충분하다.
#   Streamlit 의 @st.cache_data 와 목적이 같지만, 이 모듈은 Streamlit 없이도 쓰이므로 표준 라이브러리를 쓴다.
@lru_cache(maxsize=1)
def _load_docs() -> pd.DataFrame:
    """FAQ 코퍼스를 한 번만 읽어 캐싱합니다."""
    return pd.read_csv(DATA_PATH)


# 검색·생성: LangChain + ChromaDB + OpenAI
@lru_cache(maxsize=1)
def _retriever():
    """OpenAI 임베딩으로 FAQ 를 ChromaDB 에 적재하고 벡터 저장소를 만듭니다(1회)."""
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    from langchain_openai import OpenAIEmbeddings

    docs = _load_docs()
    documents = [
        Document(
            page_content=row["text"],
            metadata={"id": row["id"], "title": row["title"]},
        )
        for _, row in docs.iterrows()
    ]
    store = Chroma.from_documents(documents, OpenAIEmbeddings(model="text-embedding-3-small"))
    return store


def _generate_answer(question: str, sources: list[dict]) -> str:
    """근거 문서만 참고해 답변 문장을 만들어 돌려줍니다."""
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    context = "\n\n".join(f"[{s['title']}] {s['text']}" for s in sources)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "너는 서비스 FAQ 도우미다. 아래 문서 내용에만 근거해 한국어로 간결히 답하라. "
                "문서에 없으면 모른다고 답하라.\n\n문서:\n{context}",
            ),
            ("human", "{question}"),
        ]
    )
    chain = prompt | ChatOpenAI(model="gpt-4o-mini", temperature=0) | StrOutputParser()
    return chain.invoke({"context": context, "question": question})


def prepare():
    """FAQ 검색 인덱스(벡터 저장소)를 만들어 돌려줍니다.

    임베딩 API 를 부르고 벡터 저장소를 만드는 **무거운 준비**입니다.
    앱을 켤 때 미리 한 번 불러 두면 첫 질문이 느려지는 것을 막을 수 있습니다.

    Raises:
        RuntimeError: OPENAI_API_KEY 가 없을 때.
    """
    _require_key()
    return _retriever()


# 공개 API
def search(question: str, k: int = 3) -> list[dict]:
    """질문과 관련된 FAQ 문서 상위 k개를 돌려줍니다.

    Raises:
        RuntimeError: OPENAI_API_KEY 가 없을 때.
    """
    _require_key()
    store = _retriever()
    # 거리를 직접 받아 0~1 유사도로 바꾼다.
    #   similarity_search_with_relevance_scores 는 내부 변환식(1 - 거리/√2)이 먼 문서에서
    #   음수를 내고, 그때 "Relevance scores must be between 0 and 1" UserWarning 을 띄운다.
    #   Chroma 기본 거리 함수는 L2 이고 임베딩이 정규화돼 있어 거리는 0~2 범위다
    #   (0 에 가까울수록 질문과 가깝다). 그래서 1 - 거리/2 로 두면 항상 0~1 에 들어온다.
    hits = store.similarity_search_with_score(question, k=k)
    return [
        {
            "id": doc.metadata["id"],
            "title": doc.metadata["title"],
            "text": doc.page_content,
            "score": round(max(0.0, 1.0 - float(distance) / 2.0), 3),
        }
        for doc, distance in hits
    ]


def ask(question: str, k: int = 3) -> dict:
    """질문에 대해 검색 기반 답변과 근거 문서를 함께 돌려줍니다.

    Returns:
        {"answer": 답변 문자열, "sources": [{id, title, text, score}, ...]}
    Raises:
        RuntimeError: OPENAI_API_KEY 가 없을 때.
    """
    _require_key()
    sources = search(question, k)
    return {"answer": _generate_answer(question, sources), "sources": sources}
