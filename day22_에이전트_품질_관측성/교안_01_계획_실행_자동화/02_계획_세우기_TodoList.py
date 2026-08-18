"""실습 02: TodoListMiddleware 로 계획을 세우게 하기 (Plan-and-Execute)

핵심 목표
    도구·모델은 그대로 두고 middleware 한 줄과 프롬프트 한 문장만 더한다.
    에이전트가 먼저 계획(todos)을 세우고 단계별로 처리하는지 확인한다.

보는 법
    맨 끝의 '세운 계획과 진행 상태' 에서 항목이 나오고 상태가 completed 로 끝나는지 본다.
    계획 도구(write_todos)는 우리가 넘긴 목록이 아니라 이 미들웨어가 붙여 준다.

실행: 이 파일이 있는 폴더에서  uv run 02_계획_세우기_TodoList.py
준비물: OPENAI_API_KEY(일차 폴더 .env) · npx(Node.js) · uvx(uv)
"""

import asyncio
from pprint import pprint

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, TodoListMiddleware
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from 공통 import DAY_DIR, FONT, MODEL_NAME, load_api_key, open_tools
from utils import print_trajectory, tool_names

load_api_key(DAY_DIR)

# 도구를 어떻게 쓸지 일러 두는 기본 지시. 계획과는 상관없는, 이 DB 를 다루는 데 필요한 규칙들이다.
SYSTEM_BASE = (
    # 어느 일을 어느 도구로 할지 갈라 적는다. 뭉뚱그리면 모델이 엉뚱한 도구를 고른다.
    "너는 데이터 분석 비서다. 표의 조회·집계는 db_read_query 로 SQL 을 실행해 구하고, "
    "그 결과를 가공하는 계산과 그래프는 code_run-code 로 한다. 숫자를 암산하거나 지어내지 않는다. "
    # 코드 실행 서버는 표준 출력만 돌려준다. print 를 빠뜨리면 빈 결과가 온다.
    "코드의 마지막 줄은 반드시 print 로 출력한다. 값만 적은 줄은 아무것도 돌려주지 않는다. "
    "결과가 비어 있으면 print 를 빠뜨린 것이니 print 를 넣어 다시 실행한다. "
    "경고(Stderr)만 돌아오면 이 서버가 표준 출력을 버린 것이다. 코드 맨 위에서 "
    "warnings.filterwarnings('ignore') 로 경고를 끄고 다시 실행한다. "
    "같은 코드를 두 번 보내지 않는다. "
    "code_run-code 를 부를 때는 code 와 languageId 두 인자를 함께 준다. languageId 는 'python' 이다. "
    # 이 서버는 모든 코드를 같은 임시 파일에 쓴다. 동시에 두 번 부르면 서로를 덮어써 실패한다.
    "code_run-code 는 한 번에 하나씩만 부른다. 이 서버는 모든 코드를 같은 임시 파일에 쓰므로 "
    "동시에 두 번 부르면 서로의 코드를 덮어써 실패한다. "
    # 짐작해서 질의하면 틀린 열 이름으로 한 번 실패하고 그제야 확인한다. 순서를 못 박아 그 낭비를 없앤다.
    "SQL 을 처음 쓰기 전에 db_list_tables 로 표 목록을 보고, db_describe_table 로 쓸 표의 열 이름을 "
    "반드시 확인한다. 열 이름을 짐작해서 쓰지 않는다. 이 DB 는 표 이름이 invoices 처럼 소문자이고 "
    "열 이름은 InvoiceDate 처럼 대문자로 시작해서, 짐작하면 대개 틀린다. "
    # 그림은 남의 프로세스에서 그려져 우리가 고쳐 줄 수 없다. 필요한 것을 미리 못 박아 준다.
    "그림은 files_write_file 로 만들 수 없다. 그림은 code_run-code 안에서 matplotlib 의 "
    "savefig 로 저장하고, 저장한 뒤 os.path.getsize 로 크기를 print 해 0 이 아닌지 확인한다. "
    "그래프 코드는 맨 위에 다음 네 줄을 그대로 넣는다. 창을 띄우지 않고, 한글이 네모로 깨지지 않게 하려는 것이다.\n"
    # matplotlib 을 직접 import 하는 첫 줄이 없으면 모델이 pyplot 만 불러온 채 matplotlib.use 를
    # 부르다 NameError 로 한 번 실패한 뒤에야 고친다. 네 줄을 통째로 주어 그 한 번을 없앤다.
    "import matplotlib\n"
    "matplotlib.use('Agg')\n"
    "import matplotlib.pyplot as plt\n"
    # 한글 폰트 이름은 OS 마다 다르다. 정해 주지 않으면 모델이 없는 이름을 골라 제목이 네모로 나온다.
    f"plt.rcParams['font.family'] = '{FONT}'\n"
    "마크다운·텍스트만 files_write_file 로 저장한다. "
    # 긴 경로를 넣으면 모델이 다시 타이핑하다 오타를 낸다. 두 서버를 같은 폴더 기준으로 띄워 뒀다.
    "파일을 저장할 때는 폴더 경로를 적지 않는다. 파일 이름만 적는다. "
    "두 도구 모두 저장 폴더에서 실행되므로 이름만 적으면 그 폴더에 저장된다."
)

# 이 실습에서 더하는 것은 이 계획 지시뿐이다. '먼저 계획을 세우라' 정도로 뭉뚱그리면 모델이 그냥 넘긴다.
PLAN_RULE = (" 요청을 받으면 무엇을 하든 첫 도구 호출은 반드시 write_todos 여야 한다. "
             "할 일을 단계로 나눠 계획을 세운 뒤 하나씩 처리한다. 한 단계를 끝내면 곧바로 "
             "write_todos 를 다시 불러 그 항목을 completed 로 바꾼다. 마지막에는 모든 항목이 completed 여야 한다.")

# 한 문장에 여러 일(집계 2개·계산·그래프)을 담은 복합 요청이다. 계획 없이는 한 단계를 빠뜨리기 쉽다.
PLAN_Q = ("chinook DB 에서 아티스트별 앨범 수와 앨범별 곡 수를 구하고, "
          "앨범이 가장 많은 아티스트 3팀이 전체 앨범에서 차지하는 비중(%)도 계산한 다음, "
          "아티스트별 앨범 수 상위 10팀 막대그래프를 아티스트별_앨범수.png 라는 이름으로 저장해줘.")


async def main():
    tools = await open_tools()
    model = ChatOpenAI(model=MODEL_NAME, temperature=0, timeout=60)
    limit = ModelCallLimitMiddleware(run_limit=20, exit_behavior="end")

    # 달라지는 것은 두 가지뿐이다. middleware 에 TodoListMiddleware() 를 넣고,
    # 시스템 프롬프트 뒤에 '먼저 계획을 세우라' 는 한 문장(PLAN_RULE)을 붙였다.
    analyst = create_agent(model, tools,
                           middleware=[TodoListMiddleware(), limit],
                           system_prompt=SYSTEM_BASE + PLAN_RULE)

    print("\n=== 계획을 세우는 에이전트에 복합 요청 ===")
    print("요청:", PLAN_Q)
    result = await analyst.ainvoke({"messages": PLAN_Q})
    print_trajectory(result)

    print("\n불린 도구:", tool_names(result))

    # write_todos 는 부를 때마다 계획 전체를 새로 쓴다. 끝난 항목을 빼고 다시 쓰는 일이 잦아,
    # 마지막 상태만 보면 처음에 몇 단계를 세웠는지도, 몇 번 고쳤는지도 알 수 없다. 호출 기록에서 꺼낸다.
    plans = [call["args"]["todos"] for message in result["messages"]
             if isinstance(message, AIMessage)
             for call in (message.tool_calls or []) if call["name"] == "write_todos"]

    print("\n---- 처음 세운 계획 ----")
    if plans:
        # 항목이 딕셔너리 목록이라 그냥 print 하면 한 줄로 뭉친다. pprint 는 항목마다 줄을 나눠 준다
        pprint(plans[0])
        print(f"\n{len(plans[0])} 단계로 세우고, 진행하며 write_todos 를 {len(plans)} 번 다시 불렀다")
    else:
        print("계획을 세우지 않았습니다. PLAN_RULE 을 빼고 돌리면 이 자리가 비어 있습니다.")

    print("\n---- 마지막 계획 상태 ----")
    todos = result.get("todos", [])   # 계획을 세우지 않은 실행도 있으므로 get 으로 꺼낸다
    pprint(todos)

    print("\n[확인 기준] 기록에서 write_todos 가 일 사이사이에 끼어 있어야 합니다.")
    print("            계획을 세우고(pending) → 하나를 붙잡고(in_progress) → 끝내는(completed) 순서입니다.")
    print("            마지막 상태에 항목이 한둘만 남기도 합니다. 그 도구는 부를 때마다 목록을 통째로")
    print("            새로 쓰기 때문입니다. 그래서 '처음 세운 계획' 은 호출 기록에서 따로 꺼냈습니다.")
    print("            노트북 1절의 계획 없는 실행과 견주세요. 시킨 일을 빠뜨리는 정도가 달라집니다.")


# 이 파일을 직접 실행할 때만 main 을 돌린다(다른 파일이 import 해도 실행되지 않게).
if __name__ == "__main__":
    asyncio.run(main())
