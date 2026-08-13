"""교안 02-1: 같은 질문, 다른 시스템 프롬프트

핵심 목표
    프롬프트 몇 문장 차이로 에이전트의 도구 선택이 갈리는 것을 도구 호출 기록으로 확인한다.

두 버전을 같은 질문으로 한 번씩 돌린다.
    A(모호한 지시): "파일로 저장할 때는 files_write_file 을 쓴다" 만 적혀 있다.
    B(구체적 지시): 그림은 savefig 로, 저장 폴더는 절대경로로, Agg 와 한글 폰트까지 적어 준다.

실행: 이 파일이 있는 폴더에서  uv run 01_프롬프트_비교_그래프저장.py

OPENAI_API_KEY 가 필요합니다(일차 폴더의 .env).
"""

import asyncio
import platform
import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

sys.path.append(str(Path(__file__).resolve().parent.parent))   # 일차 폴더의 utils.py 를 쓴다

from utils import child_env, chinook_db_path, load_api_key, print_trajectory, quiet_stdio_logs


quiet_stdio_logs()

DAY_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = DAY_DIR / "data"
load_api_key(DAY_DIR)

DB_PATH = chinook_db_path(DATA_DIR)
CHILD_ENV = child_env()

# 산출물은 모두 일차 폴더의 output 에 모은다. 아래에서 두 서버를 이 폴더 기준으로 띄운다.
OUTPUT_DIR = DAY_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)   # 파일 서버는 없는 폴더를 만들어 주지 않는다
FONT = {"Windows": "Malgun Gothic", "Darwin": "AppleGothic"}.get(platform.system(), "NanumGothic")

SQLITE = {"command": "uvx",
          "args": ["--with", "mcp==1.9.4", "--from", "mcp-server-sqlite",
                   "mcp-server-sqlite", "--db-path", str(DB_PATH)],
          "transport": "stdio"}
# 두 서버를 output 폴더 기준으로 띄운다. 코드 실행 서버는 작업 폴더(cwd)가,
# 파일 서버는 열어 준 폴더가 상대경로의 기준이다. 같은 폴더로 맞추면 파일 이름만으로 통한다.
CODE_RUNNER = {"command": "npx", "args": ["-y", "mcp-server-code-runner"],
               "transport": "stdio", "env": CHILD_ENV, "cwd": str(OUTPUT_DIR)}
FILESYSTEM = {"command": "npx",
              "args": ["-y", "@modelcontextprotocol/server-filesystem", str(OUTPUT_DIR)],
              "transport": "stdio"}

ALLOWED = {"db_read_query", "db_list_tables", "db_describe_table",
           "code_run-code", "files_write_file"}

COMMON = ("너는 데이터 분석 비서다. 표의 조회·집계는 db_read_query 로 SQL 을 실행해 구한다. "
          "숫자를 암산하거나 지어내지 않는다. "
          "코드의 결과에 대한 마지막 줄은 반드시 print 로 출력한다. ")

# A: 저장 방법을 뭉뚱그려 적었다. 그림에도 files_write_file 을 쓰라는 말로 읽힌다.
PROMPT_A = COMMON + "파일로 저장할 때는 files_write_file 을 쓴다. 경로는 파일 이름만 적는다."

# B: 그림과 글을 갈라 적고, 그림에 필요한 세 가지를 코드로 못 박았다.
PROMPT_B = COMMON + (
    "그림은 files_write_file 로 만들 수 없다. 그림은 code_run-code 안에서 matplotlib 의 "
    "savefig 로 저장한다. 그래프 코드는 맨 위에 다음 두 줄을 그대로 넣는다.\n"
    "matplotlib.use('Agg')\n"
    f"plt.rcParams['font.family'] = '{FONT}'\n"
    "저장한 뒤 os.path.getsize 로 크기를 print 해 0 이 아닌지 확인한다. "
    "마크다운·텍스트만 files_write_file 로 저장한다. "
    "파일을 저장할 때는 폴더 경로를 적지 않는다. 파일 이름만 적는다."
)

# 두 버전에 똑같이 던지는 질문. 저장 폴더는 프롬프트에 있으니 질문에는 파일 이름만 준다.
CHART_A = OUTPUT_DIR / "비교_A.png"
CHART_B = OUTPUT_DIR / "비교_B.png"
QUESTION = ("invoices 표에서 연도별 매출 합계를 구하고, "
            "연도별 매출 막대그래프를 '{name}' 이라는 이름으로 저장해 줘.")


async def run_one(label: str, system_prompt: str, chart_path: Path, tools, model):
    """한 버전을 돌리고 도구 호출 기록과 산출물을 찍는다."""
    print(f"\n{'=' * 60}\n[{label}]\n{'=' * 60}")
    agent = create_agent(
        model, tools, system_prompt=system_prompt,
        middleware=[ModelCallLimitMiddleware(run_limit=12, exit_behavior="end")],
    )
    chart_path.unlink(missing_ok=True)     # 지난 실행의 파일을 지우고 시작한다
    print_trajectory(await agent.ainvoke({"messages": QUESTION.format(name=chart_path.name)}))

    # 도구의 말이 아니라 파일로 확인한다. 0 바이트 파일도 exists() 는 True 다.
    size = chart_path.stat().st_size if chart_path.exists() else 0
    png = chart_path.exists() and chart_path.read_bytes()[:4] == b"\x89PNG"
    print(f"\n[산출물] {chart_path.name} · 있음 {chart_path.exists()} · 크기 {size} 바이트 · PNG 서명 {png}")
    return size, png


async def main():
    print("서버 세 개를 띄우는 중입니다(첫 실행은 오래 걸립니다)...")
    client = MultiServerMCPClient({"db": SQLITE, "code": CODE_RUNNER, "files": FILESYSTEM},
                                  tool_name_prefix=True)
    tools = [t for t in await client.get_tools() if t.name in ALLOWED]
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60)

    a = await run_one("A. 저장 방법을 뭉뚱그린 프롬프트", PROMPT_A, CHART_A, tools, model)
    b = await run_one("B. 그림 저장을 코드로 못 박은 프롬프트", PROMPT_B, CHART_B, tools, model)

    print(f"\n{'=' * 60}\n[비교]\n{'=' * 60}")
    print(f"A: 크기 {a[0]} 바이트 · PNG {a[1]}")
    print(f"B: 크기 {b[0]} 바이트 · PNG {b[1]}")
    print("\n[보는 법] 두 기록에서 그래프를 어느 도구로 저장했는지 찾아 견주세요.")
    print("  A 는 files_write_file 로 .png 를 쓰려다 빈 파일을 남기기 쉽습니다.")
    print("    그 도구는 글자만 쓰는데, 서버는 'Successfully wrote' 라고 답합니다.")
    print("  B 는 code_run-code 안에서 savefig 로 저장하므로 파일이 실제로 남습니다.")
    print("\n[교훈] 도구가 여럿일 때는 '무엇을 어느 도구로' 를 갈라 적어야 합니다.")
    print("       '파일로 저장해라' 처럼 뭉뚱그리면 모델이 엉뚱한 도구를 고릅니다.")


if __name__ == "__main__":
    asyncio.run(main())
