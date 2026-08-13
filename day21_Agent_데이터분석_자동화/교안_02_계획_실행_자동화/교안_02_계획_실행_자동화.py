"""교안 02: 계획을 세우고 실행하기 (MCP 도구로)

핵심 목표
    에이전트에 미들웨어를 끼워 할 일 목록(계획)을 세우게 하고,
    수집 -> 분석·통계 -> 시각화 -> 리포트로 이어지는 자동 분석 파이프라인을 MCP 도구만으로 완성한다.

학습 순서
    1) 계획 없는 에이전트의 한계 관찰
    2) 미들웨어와 훅: 에이전트 루프의 어디를 확장하는가
    3) TodoListMiddleware 로 Plan-and-Execute 구현하기
    4) 그래프 저장이 실패하는 두 가지와 고친 방법
    5) 자동 분석 파이프라인: 조회 -> 계산 -> 그래프 -> 리포트
    6) 결과 정형화: 자유 문장을 정해진 틀로 바꿔 표·JSON 에 적재

이론 설명(미들웨어·훅의 여섯 자리, before/after 와 wrap 의 차이, 여러 개를 끼울 때의 순서)은
같은 폴더의 노트북 `교안_02_계획_실행_자동화.ipynb` 에 그림과 함께 있습니다.
이 파일은 그 이론을 코드로 확인하는 판입니다.

쓰는 MCP 서버와 공식 문서
    SQLite 서버 mcp-server-sqlite
        https://pypi.org/project/mcp-server-sqlite/
    코드 실행 서버 mcp-server-code-runner
        https://github.com/formulahendry/mcp-server-code-runner
    파일시스템 서버 @modelcontextprotocol/server-filesystem
        https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem

실행: 이 파일이 있는 폴더에서  uv run 교안_02_계획_실행_자동화.py

OPENAI_API_KEY 가 필요합니다(일차 폴더의 .env).
"""

import asyncio
import platform
import sys
from pathlib import Path

import pandas as pd
from langchain.agents import create_agent
from langchain.agents.middleware import (AgentMiddleware, HumanInTheLoopMiddleware,
                                         ModelCallLimitMiddleware, SummarizationMiddleware,
                                         TodoListMiddleware, ToolCallLimitMiddleware,
                                         ToolRetryMiddleware)
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from pydantic import BaseModel, Field

sys.path.append(str(Path(__file__).resolve().parent.parent))   # 일차 폴더의 utils.py 를 쓴다

from utils import (child_env, chinook_db_path, load_api_key,
                   print_trajectory, quiet_stdio_logs, tool_names)


quiet_stdio_logs()   # 코드 실행 서버가 stdout 에 섞어 보내는 안내문 때문에 나는 긴 경고를 끈다

DAY_DIR = Path(__file__).resolve().parent.parent    # 일차 폴더(day21). 아래 경로들의 기준점
DATA_DIR = DAY_DIR / "data"

load_api_key(DAY_DIR)   # 모델을 부르는 파일이라 키를 맨 앞에서 확인한다

DB_PATH = chinook_db_path(DATA_DIR)   # data 폴더의 chinook.db 경로를 돌려준다
CHILD_ENV = child_env()                 # 코드 실행 서버가 python 을 찾게 하는 환경 변수

# 산출물은 모두 일차 폴더의 output 에 모은다. 두 서버를 이 폴더 기준으로 띄우면
# (파일 서버는 열어 준 폴더가, 코드 실행 서버는 작업 폴더 cwd 가 상대경로의 기준이다)
# 모델은 파일 이름만 적으면 된다. 긴 경로를 프롬프트에 넣으면 모델이 다시 타이핑하다 오타를 낸다.
OUTPUT_DIR = DAY_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)      # 파일 서버는 없는 폴더를 만들어 주지 않는다
REPORT_NAME = "음악판매_리포트.md"
CHART_NAME = "연도별_매출.png"

# 앞 단원(교안_01)에서 한 줄씩 뜯어본 설정 그대로다. 이번 시간의 주제는 설정이 아니라 '계획' 이다.
SQLITE = {
    "command": "uvx",
    "args": ["--with", "mcp==1.9.4",         # 이 서버는 최신 mcp 로 띄우면 죽는다. 버전을 고정한다
             "--from", "mcp-server-sqlite",
             "mcp-server-sqlite",
             "--db-path", str(DB_PATH)],
    "transport": "stdio",
}
CODE_RUNNER = {
    "command": "npx",
    "args": ["-y", "mcp-server-code-runner"],
    "transport": "stdio",
    "env": CHILD_ENV,
    "cwd": str(OUTPUT_DIR),   # 이 서버가 돌리는 코드의 작업 폴더. savefig("그림.png") 가 여기에 떨어진다
}
FILESYSTEM = {
    "command": "npx",
    # 열어 주는 폴더가 곧 쓰기 허용 범위이자 상대경로의 기준이다
    "args": ["-y", "@modelcontextprotocol/server-filesystem", str(OUTPUT_DIR)],
    "transport": "stdio",
}


# 한글 폰트 이름은 OS 마다 다르다. "한글 폰트를 써라" 라고만 하면 모델이 없는 이름을 골라
# 제목이 네모(□□□)로 나온다. 여기서 정해 프롬프트에 넣어 준다.
FONT = {"Windows": "Malgun Gothic", "Darwin": "AppleGothic"}.get(platform.system(), "NanumGothic")

# 에이전트에 넘길 도구. 쓰기 도구는 리포트 저장용 하나만 남긴다.
# 넘기지 않은 도구는 모델이 존재조차 모른다 -- 권한은 말이 아니라 목록으로 준다.
ALLOWED = {"db_read_query", "db_list_tables", "db_describe_table",
           "code_run-code", "files_write_file"}

PNG_MAGIC = b"\x89PNG"   # 진짜 PNG 파일은 이 네 바이트로 시작한다

# 프롬프트 비교용. 두 버전이 공유하는 앞부분이다.
SYSTEM_BASE_SHORT = (
    "너는 데이터 분석 비서다. 표의 조회·집계는 db_read_query 로 SQL 을 실행해 구한다. "
    "숫자를 암산하거나 지어내지 않는다. "
    "코드의 결과에 대한 마지막 줄은 반드시 print 로 출력한다. "
)

SYSTEM_BASE = (
    "너는 데이터 분석 비서다. 표의 조회·집계는 db_read_query 로 SQL 을 실행해 구하고, "
    "그 결과를 가공하는 계산과 그래프는 code_run-code 로 한다. 숫자를 암산하거나 지어내지 않는다. "
    "코드의 마지막 줄은 반드시 print 로 출력한다. 값만 적은 줄은 아무것도 돌려주지 않는다. "
    "결과가 비어 있으면 print 를 빠뜨린 것이니 print 를 넣어 다시 실행한다. "
    "경고(Stderr)만 돌아오면 이 서버가 표준 출력을 버린 것이다. 코드 맨 위에서 "
    "warnings.filterwarnings('ignore') 로 경고를 끄고 다시 실행한다. "
    "같은 코드를 두 번 보내지 않는다. "
    "code_run-code 는 한 번에 하나씩만 부른다. 이 서버는 모든 코드를 같은 임시 파일에 쓰므로 "
    "동시에 두 번 부르면 서로의 코드를 덮어써 실패한다. "
    "표나 열 이름이 확실하지 않으면 db_list_tables 와 db_describe_table 로 먼저 확인한다. "
    "그림은 files_write_file 로 만들 수 없다. 그림은 code_run-code 안에서 matplotlib 의 "
    "savefig 로 저장하고, 저장한 뒤 os.path.getsize 로 크기를 print 해 0 이 아닌지 확인한다. "
    "그래프 코드는 맨 위에 다음 두 줄을 그대로 넣는다. 창을 띄우지 않고, 한글이 네모로 깨지지 않게 하려는 것이다.\n"
    "matplotlib.use('Agg')\n"
    f"plt.rcParams['font.family'] = '{FONT}'\n"
    "마크다운·텍스트만 files_write_file 로 저장한다. "
    "파일을 저장할 때는 폴더 경로를 적지 않는다. 파일 이름만 적는다. "
    "두 도구 모두 저장 폴더에서 실행되므로 이름만 적으면 그 폴더에 저장된다."
)

# 한 문장에 네 가지 일(집계 2개·계산·그래프)을 담은 복합 요청
COMPLEX_Q = ("chinook DB 를 분석해줘. 연도별 매출 합계와 국가별 매출 상위 5개를 구하고, "
             "연도별 매출의 전년 대비 증감률도 계산하고, 연도별 매출 막대그래프도 저장해줘.")

HOOKS = ["before_agent", "before_model", "wrap_model_call",
         "after_model", "wrap_tool_call", "after_agent"]


def used_hooks(mw_class):
    """그 미들웨어가 실제로 구현한 훅 이름만 골라 돌려준다."""
    # 기본 클래스의 훅과 '다른 함수' 로 바뀌어 있으면 그 자리를 쓴 것이다
    return [h for h in HOOKS
            if getattr(mw_class, h) is not getattr(AgentMiddleware, h)]


class AnalysisResult(BaseModel):
    """분석 답변을 담는 정해진 틀 - 지표 이름·핵심 수치·한 문장 해석."""
    # 필드 설명은 '이 칸에 무엇이 들어가는가' 를 짧은 명사구로 적는다.
    # "~하라", "~쓰지 마라" 처럼 긴 지시문으로 쓰면 모델이 그 문장을 값으로 베껴 넣는다.
    metric: str = Field(description="집계 대상과 방법이 드러나는 한국어 지표 이름. 예: 매출 1위 국가의 매출 합계")
    value: float = Field(description="핵심 수치 하나. 단위 없는 숫자")
    interpretation: str = Field(description="그 수치를 설명하는 한국어 한 문장")


async def main():
    print("\n=== 0. 서버 세 개에 붙어 도구 고르기 ===")
    print("서버를 띄우는 중입니다(첫 실행은 오래 걸립니다)...")
    client = MultiServerMCPClient(
        {"db": SQLITE, "code": CODE_RUNNER, "files": FILESYSTEM},
        tool_name_prefix=True,      # db_·code_·files_ 접두사를 붙인다. 서버끼리 도구 이름이 겹쳐도 충돌하지 않는다
    )
    tools = [t for t in await client.get_tools() if t.name in ALLOWED]
    print("에이전트에 쓸 도구:", [t.name for t in tools])

    # timeout 을 준다. 기본값은 요청 하나를 10분까지 기다리고 두 번 더 재시도해서,
    # 응답이 늦거나 분당 한도에 걸리면 화면만 보고는 멈춘 것과 구별되지 않는다.
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60)

    print("\n=== 1. 계획 없는 에이전트의 한계 ===")
    # 계획 장치(middleware) 없이 도구만 붙인 에이전트 -- 비교용.
    # 여러 단계를 던지면 어디까지 했는지 남기지 않아 한 단계를 통째로 빠뜨리기 쉽다.
    # 모델 호출 횟수에 상한을 둔다. 반복에 빠져도 상한에서 스스로 끝나므로
    # (exit_behavior="end") 예외 없이 여태 기록을 그대로 돌려준다.
    LIMIT = ModelCallLimitMiddleware(run_limit=20, exit_behavior="end")

    plain_agent = create_agent(model, tools, system_prompt=SYSTEM_BASE, middleware=[LIMIT])
    result_plain = await plain_agent.ainvoke({"messages": COMPLEX_Q})
    print_trajectory(result_plain)
    print("\n불린 도구:", tool_names(result_plain))
    print("=> 네 가지를 시켰는데 몇 가지를 했는지 위 목록에서 세어 보자. 그래프 저장이 흔히 빠진다.")

    print("\n=== 2. 미들웨어는 어느 자리를 쓰나 ===")
    # 기본 클래스(AgentMiddleware)와 달라진 훅이 그 미들웨어가 쓰는 자리다.
    for mw in (TodoListMiddleware, SummarizationMiddleware, HumanInTheLoopMiddleware,
               ToolCallLimitMiddleware, ToolRetryMiddleware):
        print(f"{mw.__name__:28} {used_hooks(mw)}")
    print("=> 하나같이 한두 자리만 쓴다. 재시도·대체 모델이 wrap_ 자리인 이유는 호출을 쥐고 있어야 하기 때문이다.")

    print("\n=== 3. TodoListMiddleware 로 계획 세우기 ===")
    # 도구는 그대로 두고 middleware 한 줄과 프롬프트 한 문장만 더한다.
    system_plan = SYSTEM_BASE + " 여러 단계가 필요한 복합 요청은 먼저 write_todos 로 계획을 세우고 단계별로 처리하라."
    analyst = create_agent(model, tools,
                           middleware=[TodoListMiddleware(), LIMIT],
                           system_prompt=system_plan)

    # 같은 모양의 복합 요청을 계획 에이전트에 던진다.
    # 볼 것은 하나다. 계획을 먼저 세우는가, 그리고 네 가지를 다 해내는가.
    plan_q = ("chinook DB 에서 아티스트별 앨범 수와 앨범별 곡 수를 구하고, "
              "앨범이 가장 많은 아티스트 3팀이 전체 앨범에서 차지하는 비중(%)도 계산한 다음, "
              "아티스트별 앨범 수 상위 10팀 막대그래프를 아티스트별_앨범수.png 라는 이름으로 저장해줘.")

    result = await analyst.ainvoke({"messages": plan_q})
    print_trajectory(result)

    print("\n---- 세운 계획과 진행 상태 ----")
    print("계획(todos)이 있나?:", "todos" in result)
    # 계획을 세우지 않은 실행도 있을 수 있으므로 get 으로 안전하게 꺼낸다
    for item in result.get("todos", []):
        print(f"- [{item['status']}] {item['content']}")

    print("\n=== 4. 프롬프트 한 문단이 도구 선택을 바꾼다 ===")
    # 같은 질문·같은 도구·같은 모델로 두 번 돌린다. 다른 것은 시스템 프롬프트뿐이다.
    # 중간 출력(도구 호출 기록)에서 그래프를 어느 도구로 저장했는지 견주는 것이 이 절의 전부다.
    CHART_A = OUTPUT_DIR / "비교_A.png"
    CHART_B = OUTPUT_DIR / "비교_B.png"
    compare_q = ("invoices 표에서 연도별 매출 합계를 구하고, "
                 "연도별 매출 막대그래프를 '{name}' 이라는 이름으로 저장해 줘.")

    # A: 저장 방법을 뭉뚱그렸다. 그림에도 files_write_file 을 쓰라는 말로 읽힌다.
    prompt_a = SYSTEM_BASE_SHORT + "파일로 저장할 때는 files_write_file 을 쓴다. 경로는 파일 이름만 적는다."
    # B: 그림과 글을 갈라 적고, 그림에 필요한 것을 코드로 못 박았다(SYSTEM_BASE 와 같은 방식).
    prompt_b = SYSTEM_BASE

    for label, prompt, chart in [("A. 뭉뚱그린 프롬프트", prompt_a, CHART_A),
                                 ("B. 갈라 적은 프롬프트", prompt_b, CHART_B)]:
        print(f"\n----- {label} -----")
        chart.unlink(missing_ok=True)          # 지난 실행의 파일을 지우고 시작한다
        agent = create_agent(model, tools, system_prompt=prompt,
                             middleware=[ModelCallLimitMiddleware(run_limit=12, exit_behavior="end")])
        print_trajectory(await agent.ainvoke({"messages": compare_q.format(name=chart.name)}))
        size = chart.stat().st_size if chart.exists() else 0
        is_png = chart.exists() and chart.read_bytes()[:4] == PNG_MAGIC
        print(f"\n[산출물] {chart.name} · 크기 {size} 바이트 · PNG 서명 {is_png}")

    print("\n[보는 법] 두 기록에서 그래프를 어느 도구로 저장했는지 찾아 견주세요.")
    print("  A 는 files_write_file 로 .png 를 쓰려다 빈 파일을 남기기 쉽습니다.")
    print("     그 도구는 글자만 쓰는데도 서버는 'Successfully wrote' 라고 답합니다.")
    print("  B 는 code_run-code 안에서 savefig 로 저장하므로 파일이 실제로 남습니다.")
    print("[교훈] 도구가 여럿일 때는 '무엇을 어느 도구로' 를 갈라 적습니다.")
    print("       '파일로 저장해라' 처럼 뭉뚱그리면 모델이 엉뚱한 도구를 고릅니다.")

    print("\n=== 5. 자동 분석 파이프라인: 조회 -> 계산 -> 그래프 -> 리포트 ===")
    # 네 단계를 순서까지 못박아 적는다 -- 요청이 구체적일수록 계획이 그대로 따라온다.
    # Agg 와 한글 폰트를 질문에 미리 적는 이유: 그래프는 남의 프로세스에서 그려져 우리가 고쳐 줄 수 없다.
    # 지난 실행의 산출물을 먼저 지운다. 남아 있으면 이번에 아무것도 안 만들어도 '있음=True' 가 나온다
    for old in [OUTPUT_DIR / CHART_NAME, OUTPUT_DIR / REPORT_NAME]:
        old.unlink(missing_ok=True)

    pipeline_q = (
        "1) invoices 표에서 연도별 매출 합계를 조회하고, "
        "2) 전년 대비 증감률을 계산하고, "
        f"3) 연도별 매출 막대그래프를 '{CHART_NAME}' 이라는 이름으로 저장하고, "
        f"4) 위 결과를 정리한 마크다운 리포트를 '{REPORT_NAME}' 이라는 이름으로 저장해줘. "
        "그래프는 matplotlib 으로 그려서 저장해."
    )
    report_result = await analyst.ainvoke({"messages": pipeline_q})
    print_trajectory(report_result)

    print()
    # 모델의 '저장했습니다' 라는 말이 아니라 파일로 확인한다
    for made in [OUTPUT_DIR / CHART_NAME, OUTPUT_DIR / REPORT_NAME]:
        # 0 바이트 파일도 exists() 는 True 다. 크기까지 봐야 '정말 저장됐나' 를 안다.
        size = made.stat().st_size if made.exists() else 0
        print(f"{made.name:24} 있음={made.exists()} 크기={size}바이트")

    print("\n=== 6. 결과 정형화: 자유 문장을 정해진 틀로 ===")
    # 1단계: 에이전트가 평소처럼 문장으로 답한다.
    single_q = "국가별 매출 합계에서 가장 매출이 큰 국가와 그 합계를 알려줘."
    res_single = await analyst.ainvoke({"messages": single_q})
    answer_text = res_single["messages"][-1].text
    print("[에이전트 답변]", answer_text)

    # 2단계: 그 문장을 정해진 틀로 바꾼다. 도구 없이 한 번만 부르므로 안전하고 결과가 일정하다.
    structurer = model.with_structured_output(AnalysisResult)
    # 질문과 답변을 함께 넣는다. 답변만 주면 지표 이름이 '매출' 처럼 뭉뚱그려진다.
    # 답변을 함께 주는 것이 중요하다. 그래야 새로 답하지 않고 옮겨 담기만 한다.
    info = structurer.invoke(f"질문: {single_q}\n답변: {answer_text}")
    print("지표:", info.metric, "/ 수치:", info.value, f"({type(info.value).__name__})")
    print("해석:", info.interpretation)

    # 정형화의 목적은 적재다. 딕셔너리를 모으면 표가 되고, 표는 JSON 으로 남는다.
    metrics_df = pd.DataFrame([info.model_dump()])
    metrics_path = DAY_DIR / "output" / "metrics.json"
    # orient='records' 는 '행 하나 = 객체 하나', force_ascii=False 는 한글을 그대로 쓰기 위한 옵션
    metrics_df.to_json(metrics_path, orient="records", force_ascii=False)
    print("지표 저장:", metrics_path)
    print(metrics_path.read_text(encoding="utf-8")[:200])

    print("\n=== 7. 함께 따라하기 (아래 순서대로 이 자리에 직접 작성해 보세요) ===")
    # 앞의 파이프라인을 이번에는 국가별 매출로 한 번 더 돌립니다.
    # 1) analyst 에 네 단계를 순서대로 못박아 요청한다:
    #    국가별 매출 상위 10개 조회 -> 상위 3개국 비중(%) 계산 ->
    #    국가별_매출.png 저장 -> 국가별_리포트.md 저장 (저장 폴더는 시스템 프롬프트에 이미 있으니 이름만 적는다)
    #    (그래프 요청에 Agg 와 한글 폰트 지정을 함께 적는다)
    # 2) print_trajectory 로 기록을 찍고 todos 의 전체·완료 수를 출력한다
    # 3) 두 파일이 실제로 생겼는지 파이썬으로 확인한다
    print("[확인 기준] 파일 두 개가 모두 생기고, todos 의 모든 항목이 completed 입니다.")
    print("            비중(%) 을 모델이 암산했는지 코드로 계산했는지 기록의 code_run-code 로 확인하세요.")



# 이 파일을 직접 실행할 때만 main 을 돌린다(다른 파일이 import 해도 실행되지 않게).
if __name__ == "__main__":
    asyncio.run(main())
