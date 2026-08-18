"""실습 03: 자동 분석 파이프라인 (조회 -> 계산 -> 그래프 -> 리포트)

핵심 목표
    네 단계를 순서까지 못박아 한 번에 시키고, 계획 에이전트가 끝까지 해내는지 확인한다.
    요청이 구체적일수록 계획이 그대로 따라온다.

보는 법
    맨 끝에서 그래프와 리포트 두 파일이 실제로 생겼는지 크기까지 본다.
    모델이 "저장했습니다" 라고 말해도 파일이 없거나 0 바이트일 수 있다.

실행: 이 파일이 있는 폴더에서  uv run 03_자동_분석_파이프라인.py
준비물: OPENAI_API_KEY(일차 폴더 .env) · npx(Node.js) · uvx(uv)
"""

import asyncio

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, TodoListMiddleware
from langchain_openai import ChatOpenAI

from 공통 import DAY_DIR, FONT, MODEL_NAME, OUTPUT_DIR, load_api_key, open_tools, report_file
from utils import print_trajectory

load_api_key(DAY_DIR)

CHART_NAME = "연도별_매출.png"
REPORT_NAME = "음악판매_리포트.md"

# 에이전트에 실제로 나가는 시스템 프롬프트다. 이 실습의 절반은 이 글에 있으므로 공통.py 에서
# 불러오지 않고 여기에 그대로 적었다. 파이프라인이 왜 그 순서로 도는지가 이 문장들에 들어 있다.
# (01·02 는 같은 내용을 공통.py 에서 가져다 쓴다. 문구를 고칠 일이 있으면 양쪽을 함께 고칠 것.)
SYSTEM_PROMPT = (
    # 어느 일을 어느 도구로 할지 갈라 적는다. 뭉뚱그리면 모델이 엉뚱한 도구를 고른다(02 에서 확인한 것).
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
    # 계획을 세우게 만드는 지시. '먼저 계획을 세우라' 정도로 뭉뚱그리면 모델이 그냥 넘긴다.
    " 요청을 받으면 무엇을 하든 첫 도구 호출은 반드시 write_todos 여야 한다. "
    "할 일을 단계로 나눠 계획을 세운 뒤 하나씩 처리한다. 한 단계를 끝내면 곧바로 "
    "write_todos 를 다시 불러 그 항목을 completed 로 바꾼다. 마지막에는 모든 항목이 completed 여야 한다."
)

# 네 단계를 번호로 갈라 적는다. 뭉뚱그린 한 문장보다 계획이 그대로 따라온다.
# 저장 폴더는 시스템 프롬프트에 이미 있으니 여기서는 파일 이름만 준다.
PIPELINE_Q = (
    "1) invoices 표에서 연도별 매출 합계를 조회하고, "
    "2) 전년 대비 증감률을 계산하고, "
    f"3) 연도별 매출 막대그래프를 '{CHART_NAME}' 이라는 이름으로 저장하고, "
    f"4) 위 결과를 정리한 마크다운 리포트를 '{REPORT_NAME}' 이라는 이름으로 저장해줘. "
    "그래프는 matplotlib 으로 그려서 저장해."
)


async def main():
    tools = await open_tools()
    model = ChatOpenAI(model=MODEL_NAME, temperature=0, timeout=60)

    analyst = create_agent(
        model, tools,
        middleware=[TodoListMiddleware(),
                    ModelCallLimitMiddleware(run_limit=25, exit_behavior="end")],
        system_prompt=SYSTEM_PROMPT,
    )

    # 지난 실행의 산출물을 먼저 지운다. 남아 있으면 이번에 아무것도 안 만들어도 '있음=True' 가 나온다.
    made = [OUTPUT_DIR / CHART_NAME, OUTPUT_DIR / REPORT_NAME]
    for old in made:
        old.unlink(missing_ok=True)

    print("\n=== 네 단계를 한 번에 시키기 ===")
    result = await analyst.ainvoke({"messages": PIPELINE_Q})
    print_trajectory(result)

    print("\n---- 세운 계획과 진행 상태 ----")
    todos = result.get("todos", [])
    for item in todos:
        print(f"- [{item['status']}] {item['content']}")

    print("\n---- 실제로 생긴 파일 ----")
    for path in made:
        report_file(path)

    print("\n[확인 기준] 두 파일이 모두 생기고 크기가 0 이 아니어야 합니다.")
    print("            기록에서 조회(db_read_query) -> 계산(code_run-code) ->")
    print("            그래프(code_run-code) -> 저장(files_write_file) 순서를 찾아보세요.")
    print("            증감률을 모델이 암산했는지 코드로 계산했는지도 code_run-code 기록으로 확인합니다.")


# 이 파일을 직접 실행할 때만 main 을 돌린다(다른 파일이 import 해도 실행되지 않게).
if __name__ == "__main__":
    asyncio.run(main())
