"""📝 교안 02 과제: DB 요약에서 리포트 파일까지, 에이전트 한 대로

`# 여기에 코드를 작성하세요` 자리 셋을 채우고 이 파일을 실행하세요.
아래 `# [자가채점]` 이 답을 검사하고, 통과하면 "문제 1 통과" 가 찍힙니다.

실습(`01_자동_리포트.py`)과 같은 구조를 **다른 데이터**로 다시 만듭니다.
CSV 대신 **chinook DB**(가상의 음악 판매점)에서 국가별 매출을 뽑아 리포트를 씁니다.

만들 것은 셋입니다.

    1단계  DB 를 읽어 요약 문자열을 돌려주는 도구      summarize_country_sales
    2단계  성찰 루프를 체인으로 조립하고 도구로 감싸기   write_report
    3단계  두 도구에 파일 저장 도구를 더해 에이전트 한 대로 실행

**확인 기준**: 기록에 도구가 요약 → 리포트 → 저장 순서로 세 번 찍히고,
`output/country_sales_report.md` 가 실제로 생기며 크기가 0 이 아니어야 합니다.

준비물: OPENAI_API_KEY(일차 폴더 .env) · npx(Node.js)
실행: 이 파일이 있는 폴더에서  uv run 문제1_DB_리포트_에이전트.py
"""

import asyncio
import sqlite3
import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

DAY_DIR = Path(__file__).resolve().parents[2]   # 과제 폴더에서 두 단계 올라가면 일차 폴더다
sys.path.append(str(DAY_DIR))                   # 일차 폴더의 utils.py 를 쓴다

from utils import load_api_key, print_trajectory, quiet_stdio_logs  # noqa: E402

quiet_stdio_logs()
DB_PATH = DAY_DIR / "data" / "chinook.db"
OUTPUT_DIR = DAY_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)      # 파일 서버는 없는 폴더를 만들어 주지 않는다
REPORT_NAME = "country_sales_report.md"
REPORT_PATH = OUTPUT_DIR / REPORT_NAME

load_api_key(DAY_DIR)   # 모델을 부르는 과제라 키를 맨 앞에서 확인한다

# 저장을 맡을 파일시스템 MCP 서버. 열어 준 폴더가 곧 쓰기 허용 범위다.
FILESYSTEM = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", str(OUTPUT_DIR)],
    "transport": "stdio",
}

model = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60)

# 성찰 루프가 매긴 점수를 여기에 쌓습니다. 루프가 실제로 돌았는지 자가채점이 이 목록으로 확인합니다.
SCORE_LOG = []


class Critique(BaseModel):
    """비평 결과. 점수는 멈출지 판단하는 데, 개선점은 수정 입력으로 쓴다."""
    score: int = Field(ge=1, le=10, description='1~10 종합 점수')
    issues: list[str] = Field(description='개선점 목록(짧게)')


# 프롬프트 틀은 그대로 씁니다. 중괄호로 감싼 자리가 값을 받는 칸이고, 그 칸 이름이 invoke 의 키가 됩니다.
GEN_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "너는 데이터 분석 리포트 작성자다. 주어진 수치 요약을 바탕으로 핵심 인사이트를 한국어 세 문장으로 써라. "
               "요약에 있는 수치만 쓴다. 요약에 없는 값·연도·단위를 지어내지 않는다."),
    ("human", "{summary}"),
])
CRITIC_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "너는 깐깐한 리포트 편집자다. 아래 리포트를 평가하라. 구체적 수치 인용·해석의 명확성·실행 제안 유무를 "
               "기준으로 1~10점을 매기고, 개선점을 항목으로 지적하라."),
    ("human", "{report}"),
])
REVISE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "너는 리포트 작성자다. 아래 [리포트]를 [개선점]을 모두 반영해 다시 써라. 한국어 세 문장을 유지하라. "
               "새로운 수치를 만들어 넣지 않는다. [리포트]에 있는 수치만 그대로 쓴다."),
    ("human", "[리포트]\n{report}\n\n[개선점]\n{issues}"),
])

# 에이전트에 나갈 시스템 프롬프트입니다. 고칠 필요는 없지만 무엇을 시키는지는 읽어 두세요.
SYSTEM_PROMPT = (
    "너는 데이터 분석 리포트 비서다. 분석 요청을 받으면 다음 순서로 처리한다. "
    "1) summarize_country_sales 로 수치 요약을 구한다. 숫자를 암산하거나 지어내지 않는다. "
    "2) 그 요약 문자열을 write_report 에 그대로 넘겨 리포트 본문을 받는다. 리포트를 네가 직접 쓰지 않는다. "
    "3) 받은 본문을 고치지 않고 files_write_file 로 저장한다. 저장할 때는 폴더 경로를 적지 않고 파일 이름만 적는다. "
    "저장할 내용의 맨 위에는 '# 국가별 매출 인사이트' 라는 제목 줄을 붙인다. "
    "끝나면 저장한 파일 이름과 리포트 본문을 함께 답한다."
)

QUESTION = f"매출 상위 국가를 분석해서 인사이트 리포트를 쓰고 '{REPORT_NAME}' 이라는 이름으로 저장해줘."


# ── 1단계: DB 를 읽어 요약을 돌려주는 도구 ─────────────────────────────
#   - 함수 이름은 `summarize_country_sales`, 매개변수는 `limit: int` 하나, 돌려주는 값은 문자열입니다.
#   - `@tool` 을 붙여 에이전트가 고를 수 있는 도구로 만드세요.
#   - **docstring 을 반드시 쓰세요.** 모델은 그 글을 읽고 이 도구를 고릅니다. 없으면 도구 등록이 안 됩니다.
#   - `sqlite3.connect(DB_PATH)` 로 열고 아래 SQL 을 그대로 쓰면 됩니다(`limit` 만 인자로 넘깁니다).
#         SELECT BillingCountry, ROUND(SUM(Total), 2) AS 매출
#         FROM invoices GROUP BY BillingCountry ORDER BY 매출 DESC LIMIT ?
#   - 돌려줄 문자열은 이 모양입니다(수치는 DB 에서 나온 값 그대로).
#         매출 상위 5개 국가(단위: 달러): USA 523.06, Canada 303.96, France 195.1, Brazil 190.1, Germany 156.48
#     단위를 적어 주는 이유가 있습니다. 숫자만 주면 모델이 '억 원' 같은 단위를 제 마음대로 붙입니다.
#     **확인 기준**: 이 문자열 안에 `USA` 와 `523.06` 이 그대로 들어 있어야 합니다.
# 여기에 코드를 작성하세요


# ── 2단계: 성찰 루프를 체인으로 조립하고 도구로 감싸기 ──────────────────
#   - 위 프롬프트 틀과 `model` 을 파이프(`|`)로 이어 체인 셋을 만드세요.
#     생성·수정 체인은 끝에 `StrOutputParser()` 를 달아 본문 문자열만 받습니다.
#     비평 체인만 파서가 없습니다. `with_structured_output(Critique)` 이 이미 객체로 돌려주기 때문입니다.
#   - 요약 문자열을 받아 `(최종 리포트, 점수 이력)` 을 돌려주는 `reflect(summary)` 를 만드세요.
#     생성은 맨 처음 한 번이고, 그 뒤로는 비평 점수가 8 이상이면 멈추고 아니면 고쳐 씁니다(최대 2회).
#     개선점 목록은 `- 항목` 처럼 줄바꿈 문자열로 펴서 수정 체인에 넘깁니다.
#   - 그 `reflect` 를 부르는 도구 `write_report(summary: str) -> str` 를 만들고 `@tool` 을 붙이세요.
#     리포트 본문만 돌려주고, **점수 이력은 `SCORE_LOG` 에 넣으세요**(`SCORE_LOG.extend(점수이력)`).
#     자가채점이 이 목록으로 루프가 돌았는지 확인합니다.
# 여기에 코드를 작성하세요


async def main():
    print("MCP 서버를 띄우는 중입니다(첫 실행은 오래 걸립니다)...")
    client = MultiServerMCPClient({"files": FILESYSTEM}, tool_name_prefix=True)
    file_tools = [t for t in await client.get_tools() if t.name == "files_write_file"]

    REPORT_PATH.unlink(missing_ok=True)   # 지난 실행의 파일을 지우고 시작한다

    # ── 3단계: 세 도구를 붙인 에이전트로 요청 한 줄 처리하기 ────────────
    #   - `summarize_country_sales`, `write_report`, 그리고 `file_tools` 의 도구를 한 목록에 담으세요.
    #     `file_tools` 에는 파일시스템 MCP 가 준 `files_write_file` 하나가 들어 있습니다.
    #   - `create_agent` 로 에이전트를 만들어 변수 `reporter` 에 담으세요.
    #       system_prompt : 위 `SYSTEM_PROMPT`
    #       middleware    : `ModelCallLimitMiddleware(run_limit=10, exit_behavior="end")` 하나
    #   - 위 `QUESTION` 을 물어 결과를 변수 `result` 에 담고, `print_trajectory(result)` 로 기록을 찍으세요.
    #     MCP 도구가 섞여 있으므로 `await reporter.ainvoke({"messages": QUESTION})` 로 부릅니다.
    # 여기에 코드를 작성하세요

    # [자가채점]
    called = [c["name"] for m in result["messages"] if isinstance(m, AIMessage) for c in (m.tool_calls or [])]

    for name in ("summarize_country_sales", "write_report", "files_write_file"):
        assert name in called, f"{name} 이(가) 한 번도 불리지 않았습니다: {called}"
    # 순서까지 본다. 요약을 건너뛰고 리포트부터 썼다면 숫자가 근거 없이 나온 것이다.
    assert called.index("summarize_country_sales") < called.index("write_report") < called.index("files_write_file"), \
        f"도구 순서가 요약 → 리포트 → 저장이 아닙니다: {called}"

    # 도구 자체가 맞게 만들어졌는지는 모델을 부르지 않고 직접 확인한다(비용이 들지 않는 검사다).
    summary = summarize_country_sales.invoke({"limit": 5})
    assert "USA" in summary and "523.06" in summary, \
        f"요약 문자열에 1위 국가(USA)와 그 매출(523.06)이 없습니다: {summary}"

    assert SCORE_LOG, "점수 이력이 비어 있습니다. write_report 안에서 SCORE_LOG 에 넣었는지 확인하세요."
    assert all(1 <= score <= 10 for score in SCORE_LOG), f"점수가 1~10 범위를 벗어났습니다: {SCORE_LOG}"

    # 모델의 '저장했습니다' 라는 말이 아니라 파일로 확인한다. 0 바이트 파일도 exists() 는 True 다.
    assert REPORT_PATH.exists() and REPORT_PATH.stat().st_size > 0, \
        f"리포트 파일이 없거나 비어 있습니다: {REPORT_PATH}"
    saved = REPORT_PATH.read_text(encoding="utf-8")
    assert "USA" in saved or "미국" in saved, \
        f"저장된 리포트에 1위 국가가 없습니다. 요약이 아니라 다른 내용이 저장된 것 같습니다: {saved[:200]}"

    print("\n문제 1 통과 · 점수 이력", SCORE_LOG, "· 호출한 도구", called)
    print("리포트:", REPORT_PATH.name, REPORT_PATH.stat().st_size, "바이트")
    print("\n[더 볼 것] 기록에서 도구가 세 번 불렸나요? 사람이 부른 도구는 하나도 없습니다.")
    print("           QUESTION 을 '장르별 매출' 로 바꾸면 무엇을 더 만들어야 할지 생각해 보세요.")


if __name__ == "__main__":
    asyncio.run(main())
