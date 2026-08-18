"""교안 02 실습: 요청 한 줄로 분석에서 저장까지 (성찰 루프 + 파일시스템 MCP)

핵심 목표
    "분석해서 저장해줘" 한 줄을 받아 에이전트 한 대가 끝까지 처리하게 만든다.
    데이터를 읽는 것도, 성찰 루프를 도는 것도, 파일로 남기는 것도 모두 모델이 도구를 골라서 한다.

에이전트가 쓰는 도구 세 개
    1) summarize_completion_rate   데이터를 읽어 수치 요약 문자열을 돌려준다
    2) write_report                요약을 받아 성찰 루프(생성 -> 비평 -> 수정)를 돌려 리포트를 돌려준다
    3) files_write_file            리포트를 output/ 에 저장한다 (파일시스템 MCP 서버)

노트북과 다른 곳
    노트북에서는 사람이 요약 문자열을 손으로 넣고 generate·critique·revise 를 차례로 불렀습니다.
    여기서는 세 단계를 체인(|)으로 이어 붙이고, 그 체인을 도구 하나로 감싸 에이전트에 넘깁니다.
    사람이 하는 일은 요청 문장 한 줄을 쓰는 것뿐입니다.

실행: 이 파일이 있는 폴더에서  uv run 01_자동_리포트.py
준비물: OPENAI_API_KEY(일차 폴더 .env) · npx(Node.js)
"""

import asyncio
import sys
from pathlib import Path

import pandas as pd
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

DAY_DIR = Path(__file__).resolve().parent.parent   # 이 파일은 교안_02 폴더 안이라 한 단계 올라가야 일차 폴더다
sys.path.append(str(DAY_DIR))                      # 일차 폴더의 utils.py 를 쓴다

from utils import load_api_key, print_trajectory, quiet_stdio_logs  # noqa: E402

quiet_stdio_logs()   # 서버가 stdout 에 섞어 보내는 안내문 때문에 나는 긴 경고를 끈다
DATA_PATH = DAY_DIR / "data" / "courses.csv"
OUTPUT_DIR = DAY_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)      # 파일 서버는 없는 폴더를 만들어 주지 않는다
REPORT_NAME = "course_report.md"

load_api_key(DAY_DIR)   # 모델을 부르므로 키를 맨 앞에서 확인한다

# 파일시스템 MCP 서버. 열어 준 폴더가 곧 쓰기 허용 범위이자 상대경로의 기준이다.
# 이 폴더 밖으로는 쓰지 못하므로, 에이전트에 저장을 맡겨도 다른 파일을 건드릴 수 없다.
FILESYSTEM = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", str(OUTPUT_DIR)],
    "transport": "stdio",
}

MODEL_NAME = "gpt-4o-mini"
# 체인을 파일 맨 위에서 조립하려면 모델도 여기 있어야 한다. 에이전트와 성찰 루프가 같은 모델을 함께 쓴다.
model = ChatOpenAI(model=MODEL_NAME, temperature=0, timeout=60)


# ── 1) 성찰 루프를 체인으로 조립하기 ──────────────────────────────────
class Critique(BaseModel):
    """비평 결과. 점수는 멈출지 판단하는 데, 개선점은 수정 입력으로 쓴다."""
    score: int = Field(ge=1, le=10, description='1~10 종합 점수')
    issues: list[str] = Field(description='개선점 목록(짧게)')


# 프롬프트 틀에서 중괄호로 감싼 자리가 나중에 값을 받는 칸이다. 그 칸 이름이 invoke 의 키가 된다.
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

# 노트북에서 함수 세 개로 나눠 만든 단계를 체인으로 잇는다. 파이프(|)는 '왼쪽 결과를 오른쪽 입력으로' 라는 뜻이다.
# StrOutputParser 는 답 객체에서 본문 문자열만 꺼낸다. 이것이 있어야 다음 단계가 문자열을 그대로 받는다.
generate_chain = GEN_PROMPT | model | StrOutputParser()
# 비평 체인만 파서가 없다. with_structured_output 이 이미 Critique 객체로 돌려주기 때문이다.
critique_chain = CRITIC_PROMPT | model.with_structured_output(Critique)
revise_chain = REVISE_PROMPT | model | StrOutputParser()


def reflect(summary: str, threshold: int = 8, max_iter: int = 2) -> tuple[str, list[int]]:
    """수치 요약을 받아 (최종 리포트, 점수 이력) 을 돌려준다."""
    report = generate_chain.invoke({"summary": summary})   # 생성은 맨 처음 한 번뿐이고 뒤로는 고쳐 쓰기만 한다
    score_history = []                  # 반복마다 점수를 쌓아야 좋아졌는지 눈으로 확인된다
    for _ in range(max_iter):           # 상한이 없으면 점수가 안 오를 때 영영 끝나지 않는다
        result = critique_chain.invoke({"report": report})
        score_history.append(result.score)
        if result.score >= threshold:
            break                       # 충분하면 수정하지 않고 그대로 내보낸다
        # 개선점은 줄바꿈 목록으로 펴서 넘긴다. 리스트를 그대로 넣으면 모델이 파이썬 표기를 읽는다
        issues = "\n".join(f"- {item}" for item in result.issues)
        report = revise_chain.invoke({"report": report, "issues": issues})
    return report, score_history


# ── 2) 두 가지 일을 도구로 만들어 모델에 넘기기 ────────────────────────
# @tool 을 붙이면 이 함수가 에이전트가 고를 수 있는 도구가 된다.
# docstring 은 주석이 아니다. 모델이 이 글을 읽고 도구를 고르므로 설명이 곧 성능이다.
@tool
def summarize_completion_rate(group_col: str) -> str:
    """수강 데이터를 읽어 group_col 별 평균 완료율을 요약 문자열로 돌려준다.

    group_col 로 쓸 수 있는 값은 '카테고리' 와 '가입경로' 두 가지다.
    """
    df = pd.read_csv(DATA_PATH)
    if group_col not in df.columns:
        # 모델이 없는 열 이름을 넣으면 그 자리에서 알려 준다. 그래야 다시 고를 수 있다.
        return f"'{group_col}' 열이 없습니다. 쓸 수 있는 열: 카테고리, 가입경로"
    s = df.groupby(group_col)["완료율"].mean().sort_values(ascending=False).round(1)
    parts = [f"{name} {value}" for name, value in s.items()]
    return f"{group_col}별 평균 완료율: " + ", ".join(parts)


@tool
def write_report(summary: str) -> str:
    """수치 요약 문자열을 받아 완성된 리포트 본문을 돌려준다.

    안에서 생성·비평·수정을 반복하므로, 이 도구가 돌려준 본문은 그대로 쓰면 된다.
    """
    report, score_history = reflect(summary)
    # 루프가 몇 번 돌았는지는 도구 안에서만 보인다. 에이전트 기록에는 최종 본문만 남으므로 여기서 찍는다.
    print(f"\n     [성찰 루프] 점수 이력 {score_history}\n")
    return report


# ── 3) 세 도구를 한 에이전트에 붙이기 ──────────────────────────────────
# 순서를 문장으로 못 박는다. 이 문장이 없으면 모델이 요약을 건너뛰고 리포트부터 지어낸다.
SYSTEM_PROMPT = (
    "너는 데이터 분석 리포트 비서다. 분석 요청을 받으면 다음 순서로 처리한다. "
    "1) summarize_completion_rate 로 요청받은 축의 수치 요약을 구한다. 숫자를 암산하거나 지어내지 않는다. "
    "2) 그 요약 문자열을 write_report 에 그대로 넘겨 리포트 본문을 받는다. 리포트를 네가 직접 쓰지 않는다. "
    "3) 받은 본문을 고치지 않고 files_write_file 로 저장한다. 저장할 때는 폴더 경로를 적지 않고 파일 이름만 적는다. "
    "저장할 내용의 맨 위에는 '# 강의 완료율 인사이트' 라는 제목 줄을 붙인다. "
    "끝나면 저장한 파일 이름과 리포트 본문을 함께 답한다."
)


async def main():
    print("MCP 서버를 띄우는 중입니다(첫 실행은 오래 걸립니다)...")
    client = MultiServerMCPClient({"files": FILESYSTEM}, tool_name_prefix=True)
    # 이 서버는 읽기·목록 도구까지 주지만, 저장만 시킬 것이라 쓰기 도구 하나만 남긴다.
    file_tools = [t for t in await client.get_tools() if t.name == "files_write_file"]

    # 파이썬이 만든 도구와 MCP 서버가 준 도구를 한 목록에 섞어 넘긴다. 모델에게는 둘 다 그냥 도구다.
    tools = [summarize_completion_rate, write_report, *file_tools]
    print("에이전트가 쓸 도구:", [t.name for t in tools])

    reporter = create_agent(
        model, tools, system_prompt=SYSTEM_PROMPT,
        # 세 단계면 충분한 일이라 상한을 낮게 둔다. exit_behavior='end' 면 걸려도 그때까지의 기록이 돌아온다.
        middleware=[ModelCallLimitMiddleware(run_limit=10, exit_behavior="end")],
    )

    report_path = OUTPUT_DIR / REPORT_NAME
    report_path.unlink(missing_ok=True)   # 지난 실행의 파일을 지우고 시작한다

    # 사람이 쓰는 문장은 이 한 줄뿐이다. 어느 축으로 볼지만 정해 주고 나머지는 모델이 도구로 처리한다.
    ask = f"가입경로별 완료율을 분석해서 인사이트 리포트를 쓰고 '{REPORT_NAME}' 이라는 이름으로 저장해줘."
    print(f"\n=== 요청: {ask} ===")
    result = await reporter.ainvoke({"messages": ask})
    print_trajectory(result)

    # 모델의 '저장했습니다' 라는 말이 아니라 파일로 확인한다. 0 바이트 파일도 exists() 는 True 다.
    size = report_path.stat().st_size if report_path.exists() else 0
    print(f"\n[산출물] {report_path.name} · 있음 {report_path.exists()} · 크기 {size} 바이트")

    print("\n[확인 기준] 기록에 도구가 summarize_completion_rate → write_report → files_write_file")
    print("            순서로 세 번 찍혔는지 보세요. 사람이 부른 도구는 하나도 없습니다.")
    print("            요청 문장을 '카테고리별로' 로 바꾸면 모델이 첫 도구의 인자를 알아서 바꿉니다.")


# 이 파일을 직접 실행할 때만 main 을 돌린다(다른 파일이 import 해도 실행되지 않게).
if __name__ == "__main__":
    asyncio.run(main())
