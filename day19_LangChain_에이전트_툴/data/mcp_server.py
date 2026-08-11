# [제공 코드] MCP 유틸 도구 서버 (FastMCP, stdio) — 노트북이 서브프로세스로 실행합니다.
# MCP(Model Context Protocol)는 도구를 표준 규격으로 노출하는 방법입니다.
# 이 파일은 "환율 변환", "남은 일수 계산", "신간 도서 검색" 도구를 표준 MCP 서버로 제공합니다.
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("utils")

# 신간 도서 스냅샷 — 실무에서는 이 자리가 '실제 웹 검색'이나 '사내 시스템 MCP 서버'입니다.
# 여기서는 실습 재현성을 위해 고정된 스냅샷 목록을 검색합니다(인터넷 호출 없음).
_NEW_BOOKS = [
    {"title": "파이썬으로 배우는 통계", "author": "김데이터", "price": 27000,
     "summary": "표본과 분포부터 가설검정까지 파이썬 예제로 익히는 입문서."},
    {"title": "밤의 서점 이야기", "author": "문가영", "price": 16000,
     "summary": "심야에만 문을 여는 서점을 배경으로 한 따뜻한 장편 소설."},
    {"title": "머신러닝 파이프라인", "author": "한지원", "price": 34000,
     "summary": "데이터 수집부터 배포까지 실전 머신러닝 워크플로를 다룬다."},
    {"title": "데이터 시각화의 기술", "author": "오세훈", "price": 25000,
     "summary": "표와 그래프로 숫자를 이야기로 바꾸는 시각화 실무 가이드."},
    {"title": "처음 만나는 SQL", "author": "정하늘", "price": 23000,
     "summary": "조회부터 집계까지 관계형 데이터베이스 질의를 처음부터 배운다."},
    {"title": "바다 건너 우체국", "author": "문가영", "price": 15000,
     "summary": "먼 섬 마을 우체국을 무대로 한 잔잔한 성장 소설."},
]


@mcp.tool()
def krw_to_usd(amount_krw: float) -> float:
    """원화 금액(amount_krw)을 미국 달러로 환산한다(고정 환율: 1달러=1300원)."""
    return round(amount_krw / 1300, 2)


@mcp.tool()
def days_until(target_date: str) -> int:
    """오늘부터 목표 날짜(target_date, 'YYYY-MM-DD' 형식)까지 남은 일수를 돌려준다."""
    from datetime import date

    year, month, day = map(int, target_date.split("-"))
    return (date(year, month, day) - date.today()).days


@mcp.tool()
def search_new_books(keyword: str) -> str:
    """신간 도서를 검색한다. keyword(제목·저자·소개에 포함된 단어)와 일치하는 책들을
    '제목 | 저자 | 가격원 | 소개' 형식의 줄로 돌려준다. 없으면 '검색 결과 없음'."""
    hits = [b for b in _NEW_BOOKS
            if keyword in b["title"] or keyword in b["author"] or keyword in b["summary"]]
    if not hits:
        return "검색 결과 없음"
    return "\n".join(f"{b['title']} | {b['author']} | {b['price']}원 | {b['summary']}"
                      for b in hits)


if __name__ == "__main__":
    mcp.run(transport="stdio")
