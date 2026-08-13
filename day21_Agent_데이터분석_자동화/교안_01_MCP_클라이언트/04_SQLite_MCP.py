"""교안 01-4: SQLite MCP 서버로 DB 조회하기

핵심 목표
    DB 를 MCP 로 붙여, 스키마부터 물어 가며 에이전트가 스스로 SELECT 를 쓰게 만든다.

학습 순서
    1) 실습용 샘플 DB(chinook) 준비
    2) SQLite MCP 서버 연결과 도구 6개 -- 읽기 도구와 쓰기 도구가 함께 온다
    3) 스키마부터 보기: 표 목록과 표 하나의 열 구성
    4) SELECT 를 직접 보내 결과 받기
    5) 읽기 도구만 붙인 에이전트가 스스로 SQL 쓰기

쓰는 MCP 서버와 공식 문서
    SQLite 서버 mcp-server-sqlite
        https://pypi.org/project/mcp-server-sqlite/

실행: 이 파일이 있는 폴더에서  uv run 04_SQLite_MCP.py

에이전트를 만드는 절부터 OPENAI_API_KEY 가 필요합니다(일차 폴더의 .env).
첫 실행은 DB 내려받기와 서버 패키지 설치로 수십 초 걸릴 수 있습니다.
"""

import asyncio
import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

sys.path.append(str(Path(__file__).resolve().parent.parent))   # 일차 폴더의 utils.py 를 쓴다

from utils import block_text, chinook_db_path, load_api_key, print_trajectory, quiet_stdio_logs


quiet_stdio_logs()   # 서버가 stdout 에 섞어 보내는 안내문 때문에 나는 긴 경고를 끈다

DAY_DIR = Path(__file__).resolve().parent.parent    # 일차 폴더(day21). 아래 경로들의 기준점
DATA_DIR = DAY_DIR / "data"      # 실습에 쓰는 CSV·DB 가 있는 곳

load_api_key(DAY_DIR)   # 모델을 부르는 절이 있으므로 키를 맨 앞에서 확인한다

DB_PATH = chinook_db_path(DATA_DIR)   # data 폴더의 chinook.db 경로를 돌려준다

# SQLite 서버: DB 파일 하나를 열어 SQL 로 조회하게 해 준다. 지정한 파일 밖은 건드리지 못한다.
SQLITE = {
    "command": "uvx",                        # 파이썬 패키지를 받아 실행하는 실행기(uv 에 딸려 온다)
    "args": ["--with", "mcp==1.9.4",         # mcp 버전 고정. 최신으로 띄우면 서버가 시작하자마자 죽는다
             "--from", "mcp-server-sqlite",  # 이 패키지에서
             "mcp-server-sqlite",            # 이 명령을 실행한다(패키지 이름과 명령 이름이 다를 수 있다)
             "--db-path", str(DB_PATH)],     # 열어 줄 DB 파일 하나. 서버가 정한 인자다
    "transport": "stdio",                    # 내 컴퓨터에 프로세스로 띄운다
}


async def main():
    print("\n=== 1. 샘플 DB 확인하기 ===")
    # chinook: 표 11개가 서로 이어진 음악 판매점 샘플 DB. 우리가 만든 데이터가 아니라 뒤에서 스키마부터 물어본다.
    print("DB 경로:", DB_PATH)

    print("\n=== 2. SQLite 서버에 붙기 ===")
    print("서버를 띄우는 중입니다(첫 실행은 오래 걸립니다)...")
    tools = await MultiServerMCPClient({"db": SQLITE}).get_tools()
    by_name = {tool.name: tool for tool in tools}

    print(f"도구 {len(tools)}개")
    for tool in tools:
        print(f" - {tool.name}({', '.join(tool.args)}): {tool.description.strip().splitlines()[0][:60]}")

    print()
    print("[읽기 도구] list_tables, describe_table, read_query")
    print("[쓰기 도구] write_query, create_table, append_insight")
    print("=> 서버 하나에 읽기와 쓰기가 함께 들어 있다. 이 실습에서는 읽기 도구만 쓴다.")
    # 이 서버에는 권한 범위를 정하는 인자가 없다. 그래서 권한을 좁히는 자리가 뒤(읽기 도구만 넘기기)로 옮겨 간다.

    print()
    print("[알아 둘 것] 이 서버는 관리가 멈춰 있어 최신 mcp 라이브러리로 띄우면 시작하자마자 죽는다.")
    print("            (서버가 쓰는 Server.list_resources 가 최신 버전에서 없어졌다)")
    print("            그래서 SQLITE 설정은 --with mcp==1.9.4 로 버전을 고정해 띄운다.")
    print("            남이 만든 서버를 쓸 때 실제로 겪는 일이다: 버전을 고정할 자리를 알아 두자.")

    print("\n=== 3. 스키마부터 보기 ===")
    # list_tables: DB 안의 표 이름을 모두 받아 오는 도구. 인자가 없어도 빈 딕셔너리를 넘긴다.
    print("[표 목록]")
    print(block_text(await by_name["list_tables"].ainvoke({})))

    print()
    print("[invoices 의 열]")
    # describe_table: 표 이름을 받아 열 구성을 돌려주는 도구. 인자 이름은 table 이 아니라 table_name 이다.
    print(block_text(await by_name["describe_table"].ainvoke({"table_name": "invoices"})))

    print("\n=== 4. SELECT 를 직접 보내기 ===")
    # read_query 는 SELECT 만 받는다. invoices 한 표에 국가와 금액이 다 있어 조인이 필요 없다.
    country_sales_sql = """
    SELECT BillingCountry AS country,
           COUNT(*) AS invoice_count,
           ROUND(SUM(Total), 2) AS total_sales
    FROM invoices
    GROUP BY BillingCountry
    ORDER BY total_sales DESC
    LIMIT 5
    """

    print(country_sales_sql.strip())
    print("-" * 40)
    print(block_text(await by_name["read_query"].ainvoke({"query": country_sales_sql})))

    print("\n=== 5. 에이전트가 스스로 SQL 을 쓰게 하기 ===")
    # 앞에서 말한 대로 읽기 도구만 골라 넘긴다. 넘기지 않은 도구는 모델이 존재조차 모른다.
    read_only_names = {"list_tables", "describe_table", "read_query"}
    read_tools = [tool for tool in tools if tool.name in read_only_names]
    print("에이전트에 붙일 도구:", [tool.name for tool in read_tools])

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = create_agent(
        model,
        read_tools,
        # 스키마 확인을 순서로 못 박는다. 안 그러면 모델이 열 이름을 짐작해 쓰고 "no such column" 을 받는다.
        system_prompt=(
            "너는 SQLite DB 분석 도우미다. 질문을 받으면 먼저 list_tables 와 describe_table 로 "
            "스키마를 확인한 뒤 SELECT 문을 작성해 read_query 로 실행한다. "
            "열 이름을 짐작하지 않고, 조회 결과에 없는 값을 지어내지 않는다. "
            "마지막 답은 조회한 표의 값을 근거로 이름과 수치를 함께 넣은 한국어 문장으로 쓴다."
        ),
    )

    # 담당 직원이 있다는 사실만 알려 주고 어느 열인지는 모델이 찾게 둔다. "중복 없이"가 없으면 고객 수가 부풀어 나온다.
    question = (
        "고객마다 담당 직원이 지정돼 있어. 담당 직원별로 맡은 고객 수와 그 고객들의 매출 합계를 "
        "구해서 직원 이름과 함께 알려 줘. 고객 수는 같은 고객을 여러 번 세지 말고 중복 없이 세어 줘. "
        "담당 고객이 없는 직원은 빼고 알려 줘."
    )
    print("질문:", question)
    print()
    # 메시지 기록에 모델이 만든 SQL 이 그대로 남는다. 사람이 검토할 수 있다는 점이 중요하다.
    print_trajectory(await agent.ainvoke({"messages": question}))


# 이 파일을 직접 실행할 때만 main 을 돌린다(다른 파일이 import 해도 실행되지 않게).
if __name__ == "__main__":
    asyncio.run(main())
