"""실습 04: 에이전트 답변을 정해진 틀로 받기

핵심 목표
    에이전트 답변은 매번 문장이 달라 그대로는 표에 쌓을 수 없다.
    response_format 으로 틀을 먼저 정해 두면 답이 그 틀에 맞춰 나오고, 그대로 표·JSON 이 된다.

순서
    1) 틀(AnalysisResult)을 정한다
    2) create_agent 에 response_format 으로 그 틀을 넘긴다
    3) 결과의 structured_response 를 모아 표로 만들고 JSON 으로 남긴다

에이전트는 앞 실습과 같은 구성입니다. MCP 서버 세 개를 붙이고 TodoListMiddleware 로 계획을 세우게 합니다.
달라지는 것은 한 줄뿐입니다. response_format 을 주면 최종 답이 문장이 아니라 틀로 나옵니다.

실행: 이 파일이 있는 폴더에서  uv run 04_구조화된_출력.py
준비물: OPENAI_API_KEY(일차 폴더 .env) · npx(Node.js) · uvx(uv)
"""

import asyncio

import pandas as pd
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, TodoListMiddleware
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from 공통 import DAY_DIR, FONT, MODEL_NAME, OUTPUT_DIR, load_api_key, open_tools
from utils import print_trajectory

load_api_key(DAY_DIR)

SYSTEM_PROMPT = (
    "너는 데이터 분석 비서다. 표의 조회·집계는 db_read_query 로 SQL 을 실행해 구하고, "
    "그 결과를 가공하는 계산과 그래프는 code_run-code 로 한다. 숫자를 암산하거나 지어내지 않는다. "
    "코드의 마지막 줄은 반드시 print 로 출력한다. 값만 적은 줄은 아무것도 돌려주지 않는다. "
    # 이 서버는 code 만 보내면 인자가 모자란다며 거절한다. 적어 주지 않으면 같은 호출을 되풀이한다.
    "code_run-code 를 부를 때는 code 와 languageId 두 인자를 함께 준다. languageId 는 'python' 이다. "
    # 짐작해서 질의하면 틀린 열 이름으로 한 번 실패하고 그제야 확인한다. 순서를 못 박아 그 낭비를 없앤다.
    "SQL 을 처음 쓰기 전에 db_list_tables 로 표 목록을 보고, db_describe_table 로 쓸 표의 열 이름을 "
    "반드시 확인한다. 열 이름을 짐작해서 쓰지 않는다. 이 DB 는 표 이름이 invoices 처럼 소문자이고 "
    "열 이름은 InvoiceDate 처럼 대문자로 시작해서, 짐작하면 대개 틀린다. "
    "그래프를 그릴 일이 있으면 code_run-code 안에서 matplotlib 의 savefig 로 저장하고, "
    "코드 맨 위에 import matplotlib 와 matplotlib.use('Agg'), import matplotlib.pyplot as plt, "
    f"plt.rcParams['font.family'] = '{FONT}' 를 그 순서로 그대로 넣는다. "
    # 계획을 세우게 만드는 지시. '먼저 계획을 세우라' 정도로 뭉뚱그리면 모델이 그냥 넘긴다.
    " 요청을 받으면 무엇을 하든 첫 도구 호출은 반드시 write_todos 여야 한다. "
    "할 일을 단계로 나눠 계획을 세운 뒤 하나씩 처리한다. 한 단계를 끝내면 곧바로 "
    "write_todos 를 다시 불러 그 항목을 completed 로 바꾼다. 마지막에는 모든 항목이 completed 여야 한다."
)

# 정형화는 '수치 하나로 답이 나오는 질문' 일 때 잘 맞는다.
QUESTIONS = [
    "국가별 매출 합계에서 가장 매출이 큰 국가와 그 합계를 알려줘.",
    "직원별 담당 고객 매출 합계에서 1위 직원과 그 합계를 알려줘.",
]


class AnalysisResult(BaseModel):
    """분석 답변을 담는 정해진 틀. 지표 이름·핵심 수치·답변 문장·그 값을 구한 SQL."""
    # 필드 설명은 '이 칸에 무엇이 들어가는가' 를 짧은 명사구로 적는다.
    # "~하라", "~쓰지 마라" 처럼 긴 지시문으로 쓰면 모델이 그 문장을 값으로 베껴 넣는다.
    metric: str = Field(description="집계 대상과 방법이 드러나는 한국어 지표 이름. 예: 매출 1위 국가의 매출 합계")
    value: float = Field(description="핵심 수치 하나. 단위 없는 숫자")
    # 틀로 받으면 에이전트가 사람에게 하던 문장 답변이 사라진다. 그 자리를 이 칸이 대신한다.
    answer: str = Field(description="질문에 그대로 답하는 한국어 문장. 대상 이름과 수치를 그 안에 함께 적는다")
    # 값과 근거를 같은 행에 담는다. 나중에 숫자가 이상할 때 어디서 나온 값인지 되짚을 자리가 된다.
    # '한 문장 해석' 같은 칸을 두면 모델이 answer 를 바꿔 쓴 공허한 말로 채운다. 확인할 수 있는 것을 받는다.
    sql: str = Field(description="그 값을 구할 때 db_read_query 로 실행한 SQL 원문. SQL 을 쓰지 않았으면 '해당 없음'")


async def main():
    tools = await open_tools()   # 앞 실습과 같은 세 서버
    model = ChatOpenAI(model=MODEL_NAME, temperature=0, timeout=60)
    agent = create_agent(
        model, tools, system_prompt=SYSTEM_PROMPT,
        # 이 한 줄이 이 실습의 전부다. 최종 답이 문장 대신 AnalysisResult 로 나온다.
        # 도구를 부르는 중간 단계는 그대로다. 모델이 말(텍스트)을 꺼내는 순간에만 틀이 걸린다.
        # 앞 단원의 model.with_structured_output(스키마) 는 모델 하나를 감쌀 때 쓰고,
        # 에이전트에는 이렇게 response_format 으로 준다. 하는 일은 같다.
        response_format=AnalysisResult,
        # 앞 실습과 같은 구성이다. 계획은 TodoListMiddleware 가, 폭주 방지는 상한 미들웨어가 맡는다.
        middleware=[TodoListMiddleware(),
                    ModelCallLimitMiddleware(run_limit=15, exit_behavior="end")],
    )

    rows = []
    for question in QUESTIONS:
        print(f"\n=== 질문: {question} ===")

        result = await agent.ainvoke({"messages": question})
        print_trajectory(result)   # '최종 답' 자리에 문장이 아니라 JSON 이 찍히는 것을 본다

        # 틀은 messages 가 아니라 structured_response 에 담겨 온다. 파싱은 이미 끝나 있다.
        # 대괄호로 꺼내면 안 된다. 호출 상한(run_limit)에 걸려 끝난 실행에는 이 키가 아예 없어 KeyError 가 난다.
        info = result.get("structured_response")
        if info is None:
            print("\n[건너뜀] 호출 상한에 걸려 틀을 채우지 못했습니다. run_limit 을 올리거나 질문을 쪼개세요.")
            continue

        print(f"\n[틀에 담은 결과] {info.metric} = {info.value} ({type(info.value).__name__})")
        print(f"                  {info.answer}")
        print(f"                  근거 SQL: {info.sql}")
        rows.append(info.model_dump())   # 파이단틱 객체를 딕셔너리로 바꾼다

    if not rows:
        raise SystemExit("틀에 담긴 결과가 하나도 없어 표를 만들 수 없습니다.")

    # 3단계: 딕셔너리를 모으면 표가 되고, 표는 JSON 으로 남는다.
    print("\n=== 표로 쌓기 ===")
    metrics_df = pd.DataFrame(rows)
    # 문장·SQL 열이 길어 그대로 찍으면 화면을 덮는다. 여기서는 표의 모양을 보는 것이 목적이라 줄여 찍는다.
    # max_columns 도 함께 풀어야 한다. 이것을 빼면 판다스가 열을 '...' 로 접어 네 열이 다 보이지 않는다.
    with pd.option_context("display.max_colwidth", 24, "display.width", 200,
                           "display.max_columns", None):
        print(metrics_df)
    print("\n자료형:")
    print(metrics_df.dtypes)      # value 가 문자열이 아니라 숫자(float)인지 확인한다

    metrics_path = OUTPUT_DIR / "metrics.json"
    # orient='records' 는 '행 하나 = 객체 하나', force_ascii=False 는 한글을 그대로 쓰기 위한 옵션
    metrics_df.to_json(metrics_path, orient="records", force_ascii=False)
    print("\n지표 저장:", metrics_path)
    print(metrics_path.read_text(encoding="utf-8")[:300])

    print("\n[확인 기준] value 의 자료형이 object 가 아니라 float64 여야 합니다.")
    print("            answer 의 문장은 실행할 때마다 달라지지만, 열 이름과 자료형은 그대로입니다.")
    print("            sql 열이 위 트래젝토리의 db_read_query 인자와 같은지 눈으로 맞춰 보세요.")
    print("            값과 근거가 한 행에 함께 쌓여야 나중에 숫자를 되짚을 수 있습니다.")


# 이 파일을 직접 실행할 때만 main 을 돌린다(다른 파일이 import 해도 실행되지 않게).
if __name__ == "__main__":
    asyncio.run(main())
