"""교안 01-6: 종합 실습 - 데이터 분석 자동화 파이프라인

핵심 목표
    조회는 DB, 계산은 코드, 저장은 파일 서버.
    세 갈래를 한 에이전트에 붙여 "질문 한 문장 -> 리포트 파일" 까지 자동으로 잇는다.

학습 순서
    1) 세 서버(DB·코드 실행·파일시스템)의 도구를 한 목록으로 받기
    2) 실습 1: 그래프를 그려 PNG 로 저장하게 하기
    3) 실습 2: 리포트를 마크다운 파일로 저장하게 하기

앞 실습과의 관계
    01(파일시스템)·04(SQLite)·05(코드 실행)에서 하나씩 붙여 본 서버를 여기서 한꺼번에 붙인다.
    새로 배우는 것은 둘이다. 여러 서버를 한 클라이언트에 등록하고 접두사로 이름 충돌을 막는 방법,
    그리고 같은 도구 묶음이라도 프롬프트와 도구 목록을 어떻게 주느냐에 따라 결과가 달라진다는 것이다.
    실습 1과 2는 붙이는 도구도 시키는 일도 다르다. 그 차이를 나란히 놓고 본다.

쓰는 MCP 서버와 공식 문서
    SQLite 서버 mcp-server-sqlite
        https://pypi.org/project/mcp-server-sqlite/
    코드 실행 서버 mcp-server-code-runner
        https://github.com/formulahendry/mcp-server-code-runner
    파일시스템 서버 @modelcontextprotocol/server-filesystem
        https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem

실행: 이 파일이 있는 폴더에서  uv run 06_종합_데이터분석_자동화2.py

OPENAI_API_KEY 가 필요합니다(일차 폴더의 .env).
"""

import asyncio
import sys
import platform
from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools   # 열린 세션에서 도구를 꺼낸다
from langchain_openai import ChatOpenAI

sys.path.append(str(Path(__file__).resolve().parent.parent))   # 일차 폴더의 utils.py 를 쓴다

from utils import (child_env, chinook_db_path, load_api_key,
                   print_trajectory, quiet_stdio_logs)


quiet_stdio_logs()   # 코드 실행 서버가 stdout 에 섞어 보내는 안내문 때문에 나는 긴 경고를 끈다

DAY_DIR = Path(__file__).resolve().parent.parent    # 일차 폴더(day21). 아래 경로들의 기준점
DATA_DIR = DAY_DIR / "data"      # 실습에 쓰는 CSV·DB 가 있는 곳

load_api_key(DAY_DIR)   # 모델을 부르는 파일이라 키를 맨 앞에서 확인한다

DB_PATH = chinook_db_path(DATA_DIR)   # data 폴더의 chinook.db 경로를 돌려준다
CHILD_ENV = child_env()                 # 코드 실행 서버가 python 을 찾을 수 있게 PATH 를 맞춰 넘긴다

# 04 번에서 쓴 그 설정이다. DB 파일 하나만 열어 준다.
SQLITE = {
    "command": "uvx",                        # 파이썬 패키지를 받아 실행하는 실행기
    "args": ["--with", "mcp==1.9.4",         # mcp 버전 고정. 최신으로 띄우면 서버가 바로 죽는다
             "--from", "mcp-server-sqlite",  # 이 패키지에서
             "mcp-server-sqlite",            # 이 명령을 실행한다
             "--db-path", str(DB_PATH)],     # 열어 줄 DB 파일 하나
    "transport": "stdio",
}
# 05 번에서 쓴 그 설정이다. env 로 실행 환경을 정해 준다.
CODE_RUNNER = {
    "command": "npx",                          # Node 패키지 실행기
    "args": ["-y", "mcp-server-code-runner"],  # 묻지 않고 진행 + 띄울 서버 패키지 이름
    "transport": "stdio",
    "env": CHILD_ENV,                          # 서버가 python 을 찾게 하는 환경 변수
}
# 01 번에서 쓴 그 설정이다. 리포트를 저장할 폴더를 열어 준다.
FILESYSTEM = {
    "command": "npx",
    "args": ["-y",
             "@modelcontextprotocol/server-filesystem",
             str(DAY_DIR)],                    # 서버가 볼 수 있는 폴더. 이 밖은 건드리지 못한다
    "transport": "stdio",
}

# 산출물 경로는 우리가 만들어 넘긴다. 절대경로라야 코드 실행 서버가 어느 폴더에서 돌든 같은 자리에 남는다.
CHART_PATH = DAY_DIR / "output" / "연도별_매출.png"
REPORT_PATH = DAY_DIR / "output" / "매출_리포트.md"

# 한글 폰트 이름은 OS 마다 다르다. 코드 실행 서버는 같은 컴퓨터에서 도니까 여기서 정해 넘긴다.
FONT = {"Windows": "Malgun Gothic", "Darwin": "AppleGothic"}.get(platform.system(), "NanumGothic")

# 두 실습이 함께 쓰는 앞부분. 어떤 일을 어느 도구에 맡길지를 못 박는다.
BASE_PROMPT = (
    "너는 데이터 분석 도우미다. 표의 집계는 db_read_query 로 SQL 을 실행해 구하고, "
    "그 결과를 가공하는 계산은 code_run-code 로 한다. 숫자를 암산하거나 지어내지 않는다. "
    "코드의 결과에 대한 마지막 줄은 반드시 print 로 출력한다. "
    "결과가 비어 있으면 print 를 빠뜨린 것이니 print 를 넣어 다시 실행한다. "
    "표나 열 이름이 확실하지 않으면 db_list_tables 와 db_describe_table 로 먼저 확인한다. "
)


async def main():
    print("\n=== 1. 세 서버의 도구를 한 목록으로 받기 ===")
    # 서버가 여럿이면 도구 이름이 겹칠 수 있다. 접두사를 붙이면 충돌이 사라지고,
    # 이름만 보고 서버 단위로 도구를 고를 수 있다(뒤에서 그 방식으로 권한을 좁힌다).
    print("서버 세 개를 띄우는 중입니다(첫 실행은 오래 걸립니다)...")
    client = MultiServerMCPClient({"db": SQLITE, "code": CODE_RUNNER, "files": FILESYSTEM})

    # 05 번에서 하나 열어 본 session 을 여기서는 셋 겹쳐 연다.
    # 이렇게 열어 두면 서버 프로세스가 블록이 끝날 때까지 살아 있어,
    # 도구를 부를 때마다 npx·uvx 가 다시 뜨지 않는다.
    async with client.session("db") as db_session:
        async with client.session("code") as code_session:
            async with client.session("files") as files_session:
                tools = []
                for prefix, session in (("db", db_session),
                                        ("code", code_session),
                                        ("files", files_session)):
                    for tool_item in await load_mcp_tools(session):
                        # 세션에서 직접 꺼낸 도구에는 접두사가 붙지 않는다. 이름을 우리가 붙여 준다.
                        tool_item.name = f"{prefix}_{tool_item.name}"
                        tools.append(tool_item)

                by_name = {tool_item.name: tool_item for tool_item in tools}

                print(f"도구 {len(tools)}개")
                print(" ", ", ".join(sorted(by_name)))

                # timeout 을 준다. 기본값은 10분이라 응답이 늦으면 멈춘 것과 구별되지 않는다.
                model = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60)

                print("\n=== 2. 실습 1: 그래프를 그려 저장하게 하기 ===")
                # 그림은 코드 실행 서버가 그린다. 파일 저장 도구는 넣지 않는다.
                # 권한은 말이 아니라 목록으로 준다. 넘기지 않은 도구는 모델이 존재조차 모른다.
                chart_tools = [t for t in tools if t.name in
                               {"db_read_query", "db_list_tables", "db_describe_table", "code_run-code"}]
                print("에이전트에 붙인 도구:", [t.name for t in chart_tools])

                chart_agent = create_agent(
                    model,
                    chart_tools,
                    # 그림에만 붙는 조건 셋을 프롬프트에 미리 적어 둔다.
                    #   Agg      : 저쪽은 창을 띄울 수 없는 프로세스라 화면 대신 파일로만 그려야 한다
                    #   한글 폰트 : 기본 폰트에 한글이 없어 제목이 네모(□□□)로 나온다
                    #   경고 끄기 : 폰트 경고가 하나라도 나면 이 서버는 표준 출력을 통째로 버린다.
                    #              그러면 모델은 print 한 값이 사라진 것을 실패로 오해하고 같은 코드를 계속 다시 보낸다.
                    system_prompt=BASE_PROMPT + (
                        "그래프는 matplotlib 으로 그리되 matplotlib.use('Agg') 로 창을 띄우지 않는다. "
                        f"한글이 깨지지 않게 plt.rcParams['font.family'] 를 '{FONT}' 로 지정한다. "
                        "코드 맨 위에서 warnings.filterwarnings('ignore') 로 경고를 끈다. "
                        "경고가 하나라도 나면 이 서버는 표준 출력을 버려서 print 한 값이 사라진다. "
                        "code_run-code 는 한 번에 하나씩만 부른다. 이 서버는 모든 코드를 같은 임시 파일에 쓰므로 "
                        "동시에 두 번 부르면 서로의 코드를 덮어써 실패한다. "
                        "저장을 마치면 os.path.getsize 로 파일 크기를 재서 경로와 함께 print 한다. 0 이면 저장에 실패한 것이다."
                    ),
                    middleware=[ModelCallLimitMiddleware(run_limit=15, exit_behavior="end")],
                )

                chart_question = (
                    "invoices 표에서 연도별 매출 합계를 구하고, 연도별 막대그래프를 그려서 "
                    f"'{CHART_PATH}' 에 저장해 줘. 경로는 이 문자열을 그대로 써 줘."
                )
                print("질문:", chart_question)
                print()
                print_trajectory(await chart_agent.ainvoke({"messages": chart_question}))

                # 모델의 '저장했습니다' 라는 말이 아니라 파일로 확인한다.
                print()
                print("그림이 생겼나?:", CHART_PATH.exists())

                print("\n=== 3. 실습 2: 리포트를 파일로 저장하게 하기 ===")
                # 같은 DB·코드 도구에 파일 쓰기 도구 하나를 더한다. 시키는 일이 달라지면 붙일 도구도 달라진다.
                report_tools = chart_tools + [t for t in tools if t.name == "files_write_file"]
                print("에이전트에 붙인 도구:", [t.name for t in report_tools])

                report_agent = create_agent(
                    model,
                    report_tools,
                    system_prompt=BASE_PROMPT + (
                        "파일로 저장할 때는 files_write_file 을 쓴다. "
                        "표는 마크다운 표로 정리하고, 수치는 조회·계산한 값만 쓴다."
                    ),
                    middleware=[ModelCallLimitMiddleware(run_limit=15, exit_behavior="end")],
                )

                report_question = (
                    "invoices 표에서 연도별 매출 합계를 구하고, 전년 대비 증감률까지 계산해 줘. "
                    f"결과를 표로 정리한 마크다운 리포트를 '{REPORT_PATH}' 에 저장해 줘. "
                    "경로는 이 문자열을 그대로 써 줘."
                )
                print("질문:", report_question)
                print()
                print_trajectory(await report_agent.ainvoke({"messages": report_question}))

                print()
                print("리포트가 생겼나?:", REPORT_PATH.exists())
                if REPORT_PATH.exists():
                    print("-" * 40)
                    print(REPORT_PATH.read_text(encoding="utf-8")[:400])
    # 블록을 빠져나오면 files -> code -> db 순서로(연 순서의 역순) 세 서버가 닫힌다.
    # 도구는 세션에 묶여 있으므로 이 밖에서 부르면 끊긴 연결에 붙어 실패한다.


# 이 파일을 직접 실행할 때만 main 을 돌린다(다른 파일이 import 해도 실행되지 않게).
if __name__ == "__main__":
    asyncio.run(main())
