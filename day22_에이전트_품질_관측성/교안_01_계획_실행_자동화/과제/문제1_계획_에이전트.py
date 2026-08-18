"""📝 과제 문제 1: TodoListMiddleware 로 계획을 세우고 단계별로 실행하기 (Plan-and-Execute)

`# 여기에 코드를 작성하세요` 자리를 채우고 이 파일을 실행하세요.
아래 `# [자가채점]` 이 답을 검사하고, 통과하면 "문제 1 통과" 가 찍힙니다.

이 문제가 보는 것은 **계획을 세웠는가** 하나가 아닙니다.
계획을 세우고(plan) → 단계를 처리하며 **상태를 갱신하는가**(execute) 까지 봅니다.
`write_todos` 가 **두 번 이상** 불려야 통과합니다. 처음 한 번은 계획을 적는 호출이고,
그 뒤 호출은 끝난 단계를 completed 로 바꾸는 호출입니다.

준비물: OPENAI_API_KEY(일차 폴더 .env) · npx(Node.js) · uvx(uv)
실행: 이 파일이 있는 폴더에서  uv run 문제1_계획_에이전트.py
"""

import asyncio
from pprint import pprint

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, TodoListMiddleware
from langchain_core.messages import AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

from 공통 import ALLOWED, CODE_RUNNER, DAY_DIR, FILESYSTEM, FONT, OUTPUT_DIR, SQLITE, load_api_key
from utils import print_trajectory   # 공통.py 가 일차 폴더를 경로에 넣어 둔다

load_api_key(DAY_DIR)   # 모델을 부르는 문제라 키를 맨 앞에서 확인한다

CHART_NAME = "장르별_매출.png"
CHART_PATH = OUTPUT_DIR / CHART_NAME

# 에이전트에 나갈 시스템 프롬프트다. 이 문제에서는 여러분이 쓸 일이 없으니 그대로 넘기면 되지만,
# 무엇을 시키고 있는지는 읽어 두세요. 마지막 한 문장이 계획을 세우게 만드는 문장입니다.
SYSTEM_PROMPT = (
    "너는 데이터 분석 비서다. 표의 조회·집계는 db_read_query 로 SQL 을 실행해 구하고, "
    "그 결과를 가공하는 계산과 그래프는 code_run-code 로 한다. 숫자를 암산하거나 지어내지 않는다. "
    "코드의 마지막 줄은 반드시 print 로 출력한다. 값만 적은 줄은 아무것도 돌려주지 않는다. "
    "같은 코드를 두 번 보내지 않는다. code_run-code 는 한 번에 하나씩만 부른다. "
    "code_run-code 를 부를 때는 code 와 languageId 두 인자를 함께 준다. languageId 는 'python' 이다. "
    # 짐작해서 질의하면 틀린 열 이름으로 한 번 실패하고 그제야 확인한다. 순서를 못 박아 그 낭비를 없앤다.
    "SQL 을 처음 쓰기 전에 db_list_tables 로 표 목록을 보고, db_describe_table 로 쓸 표의 열 이름을 "
    "반드시 확인한다. 열 이름을 짐작해서 쓰지 않는다. 이 DB 는 표 이름이 invoices 처럼 소문자이고 "
    "열 이름은 InvoiceDate 처럼 대문자로 시작해서, 짐작하면 대개 틀린다. "
    "매출을 표 여럿에 걸쳐 구할 때는 invoice_items 의 UnitPrice * Quantity 를 더한다. "
    "invoices 의 Total 을 invoice_items 와 이어 붙여 더하면 한 청구서의 금액이 줄 수만큼 "
    "거듭 세어져 값이 부풀려진다. "
    "그림은 files_write_file 로 만들 수 없다. 그림은 code_run-code 안에서 matplotlib 의 "
    "savefig 로 저장하고, 저장한 뒤 os.path.getsize 로 크기를 print 해 0 이 아닌지 확인한다. "
    "그래프 코드는 맨 위에 다음 네 줄을 그대로 넣는다.\n"
    # matplotlib 을 직접 import 하는 첫 줄이 없으면 모델이 pyplot 만 불러온 채 matplotlib.use 를
    # 부르다 NameError 로 한 번 실패한 뒤에야 고친다. 네 줄을 통째로 주어 그 한 번을 없앤다.
    "import matplotlib\n"
    "matplotlib.use('Agg')\n"
    "import matplotlib.pyplot as plt\n"
    f"plt.rcParams['font.family'] = '{FONT}'\n"
    "파일을 저장할 때는 폴더 경로를 적지 않는다. 파일 이름만 적는다. "
    # 계획을 세우게 만드는 지시. '먼저 계획을 세우라' 정도로 뭉뚱그리면 모델이 그냥 넘긴다.
    " 요청을 받으면 무엇을 하든 첫 도구 호출은 반드시 write_todos 여야 한다. "
    "할 일을 단계로 나눠 계획을 세운 뒤 하나씩 처리한다. 한 단계를 끝내면 곧바로 "
    "write_todos 를 다시 불러 그 항목을 completed 로 바꾼다. 마지막에는 모든 항목이 completed 여야 한다."
)

# 세 단계짜리 복합 요청이다. 계획 없이 던지면 한 단계를 빠뜨리기 쉽다.
Q1 = ("chinook DB 에서 장르별 총 매출 상위 3개 장르와 각 매출을 구하고, "
      "1위 장르가 전체 매출에서 차지하는 비중(%)도 계산한 다음, "
      f"장르별 매출 상위 3개 막대그래프를 '{CHART_NAME}' 이라는 이름으로 저장해줘.")


async def main():
    # 문제 1. 계획을 세우고 단계별로 실행하는 에이전트 만들기
    #   - MultiServerMCPClient 에 {"db": SQLITE, "code": CODE_RUNNER, "files": FILESYSTEM} 을 넘기고,
    #     tool_name_prefix=True 를 함께 주어 만드세요. 서버 별명이 도구 이름 앞에 붙습니다.
    #     get_tools() 를 await 한 뒤 이름이 `ALLOWED` 에 있는 도구만 남겨 변수 `tools` 에 담으세요.
    #   - 모델은 ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60) 입니다.
    #   - create_agent 로 에이전트를 만들어 변수 `analyst` 에 담으세요.
    #       system_prompt : 위 `SYSTEM_PROMPT`
    #       middleware    : TodoListMiddleware() 와
    #                       ModelCallLimitMiddleware(run_limit=30, exit_behavior="end") 둘
    #     계획 도구(write_todos)는 우리가 넘긴 도구 목록이 아니라 TodoListMiddleware 가 붙여 줍니다.
    #   - 위 `Q1` 을 물어 결과를 변수 `result` 에 담고, print_trajectory(result) 로 기록을 찍으세요.
    #   - 마지막 계획 상태를 변수 `todos` 에 담으세요. 계획은 result 의 "todos" 자리에 들어 있는데,
    #     계획을 세우지 않은 실행도 있으므로 result.get("todos", []) 로 꺼냅니다.
    #   - `todos` 를 pprint 로 출력하세요(항목이 딕셔너리라 그냥 print 하면 한 줄로 뭉칩니다).
    # 여기에 코드를 작성하세요

    # [자가채점]
    called = [c["name"] for m in result["messages"] if isinstance(m, AIMessage) for c in (m.tool_calls or [])]
    answer = result["messages"][-1].text
    # write_todos 는 부를 때마다 계획 전체를 새로 쓴다. 그래서 마지막 상태(todos)만 보면
    # 처음 세운 계획이 몇 단계였는지, 중간에 갱신을 했는지 알 수 없다. 호출 기록에서 그대로 꺼낸다.
    plans = [c["args"]["todos"] for m in result["messages"] if isinstance(m, AIMessage)
             for c in (m.tool_calls or []) if c["name"] == "write_todos"]

    assert plans, f"계획을 세우지 않았습니다. write_todos 가 한 번도 불리지 않았습니다: {called}"
    assert len(plans[0]) >= 3, f"처음 세운 계획이 너무 짧습니다(3단계 이상이어야 합니다): {plans[0]}"
    # 이 문제의 핵심. 계획만 적고 끝내면 execute 가 없는 것이다.
    assert len(plans) >= 2, (
        f"계획을 세우기만 하고 진행 상태를 갱신하지 않았습니다(write_todos 호출 {len(plans)}회). "
        "TodoListMiddleware 를 middleware 에 넘겼는지, 시스템 프롬프트를 그대로 썼는지 확인하세요.")
    assert any(item["status"] == "completed" for item in todos), \
        f"완료로 표시된 단계가 하나도 없습니다: {todos}"
    assert "db_read_query" in called, f"DB 를 조회하지 않았습니다: {called}"
    assert "Rock" in answer or "록" in answer, \
        f"매출 1위 장르(Rock)가 답에 없습니다: {answer[:200]}"
    # 모델의 '저장했습니다' 라는 말이 아니라 파일로 확인한다. 0 바이트 파일도 exists() 는 True 다.
    assert CHART_PATH.exists() and CHART_PATH.stat().st_size > 0, \
        f"그래프 파일이 없거나 비어 있습니다: {CHART_PATH}"

    done = [item["status"] for item in todos].count("completed")
    print("문제 1 통과 -- 처음 세운 계획", len(plans[0]), "단계 ·",
          "write_todos 호출", len(plans), "회 ·", "완료", done, "/", len(todos))
    print("호출한 도구:", called)
    print("그래프:", CHART_PATH.name, CHART_PATH.stat().st_size, "바이트")
    print("\n[더 볼 것] 기록의 맨 앞이 write_todos 인가요? 계획을 세운 뒤에 조회·계산·그래프가 오고,")
    print("           단계를 끝낼 때마다 write_todos 가 다시 불리는 모양이면 제대로 도는 것입니다.")


if __name__ == "__main__":
    asyncio.run(main())
