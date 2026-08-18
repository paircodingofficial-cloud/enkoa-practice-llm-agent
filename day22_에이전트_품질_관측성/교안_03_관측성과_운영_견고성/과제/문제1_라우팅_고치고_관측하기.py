"""📝 교안 03 과제: 라우팅을 고치고, 그 실행을 관측에 남기기

`# 여기에 코드를 작성하세요` 자리 셋을 채우고 이 파일을 실행하세요.
아래 `# [자가채점]` 이 답을 검사하고, 통과하면 "문제 1 통과" 가 찍힙니다.

교안 6절에서 본 흐름을 **다른 도메인**(헬스장 회원권)으로 다시 만듭니다.
이름도 설명도 모호한 도구를 그대로 한 번 돌려 보고, 이름과 docstring 만 고쳐
다시 돌린 뒤 **불린 도구가 어떻게 달라지는지** 기록으로 비교합니다.

만들 것은 셋입니다.

    1단계  콜백을 실어 부르는 함수                observed_invoke
    2단계  이름과 설명을 고친 도구                 membership_fee
    3단계  고친 도구로 다시 돌리고 토큰까지 집계    fixed_run · total_tokens

**확인 기준**: 고친 쪽 기록에 `membership_fee` 가 들어 있고 답에 135,000 이 나옵니다.
그리고 두 실행이 모두 Langfuse 의 **Tracing → Traces** 에 올라와 있어야 합니다.

준비물: OPENAI_API_KEY · LANGFUSE_PUBLIC_KEY · LANGFUSE_SECRET_KEY (일차 폴더 .env)
실행: 이 파일이 있는 폴더에서  uv run 문제1_라우팅_고치고_관측하기.py
"""

import os
import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langfuse import get_client
from langfuse.langchain import CallbackHandler

DAY_DIR = Path(__file__).resolve().parents[2]   # 과제 폴더에서 두 단계 올라가면 일차 폴더다
sys.path.append(str(DAY_DIR))                   # 일차 폴더의 utils.py 를 쓴다

from utils import load_api_key  # noqa: E402

load_api_key(DAY_DIR)   # 모델을 부르는 과제라 키를 맨 앞에서 확인한다

# 관측 준비. 교안 2절의 준비 셀과 같은 코드입니다.
if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
    raise SystemExit("Langfuse 키를 찾지 못했습니다. 일차 폴더 .env 의 LANGFUSE_PUBLIC_KEY / "
                     "LANGFUSE_SECRET_KEY 를 채우세요.")
handlers = [CallbackHandler()]
# 키가 '있지만 틀린' 경우 langfuse 는 전송만 조용히 실패한다. 그래서 인증을 여기서 확인한다.
try:
    authenticated = get_client().auth_check()
except Exception:
    authenticated = False
if not authenticated:
    raise SystemExit("Langfuse 인증에 실패했습니다. 일차 폴더 .env 의 키와 LANGFUSE_BASE_URL 을 확인하세요.")

model = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60)

FEES = {"1개월": 55000, "3개월": 135000, "6개월": 240000, "12개월": 420000}
QUESTION = "3개월 회원권 요금이 얼마인가요?"


def fee_of(plan):
    """'3개월 정기권' 처럼 이름이 섞여 들어와도 찾도록 부분 일치로 고른다."""
    for name, fee in FEES.items():
        if name in plan:
            return fee
    return 55000


def tool_trace(result):
    """메시지 기록에서 '어떤 도구가 불렸나'를 순서대로 뽑는다(교안 6절과 같은 도우미)."""
    names = []
    for message in result["messages"]:
        # 도구 호출은 AIMessage 에만 담긴다(사람 말·도구 결과에는 없다) - 타입으로 가른다
        if isinstance(message, AIMessage) and message.tool_calls:
            for call in message.tool_calls:
                names.append(call["name"])
    return names


# 모호한 도구 한 쌍입니다. 고치지 말고 그대로 두세요 - 1단계에서 이대로 돌려 봅니다.
@tool
def info(plan: str) -> str:
    """회원 정보를 조회한다."""    # ← 요금을 돌려주는 도구인데 그 말이 어디에도 없다
    return str(fee_of(plan))


@tool
def gym_guide(plan: str) -> str:
    """회원권 상품을 안내한다."""
    return f"{plan} 회원권은 헬스장 전 구역을 이용할 수 있는 상품입니다."


# ── 1단계: 콜백을 실어 부르는 함수 만들기 ──────────────────────────────
#   - 함수 `observed_invoke(agent, question)` 를 만드세요.
#     받은 에이전트를 `agent.invoke({'messages': question}, ...)` 로 부르되,
#     `config={'callbacks': handlers}` 를 함께 넘기고 결과를 그대로 돌려줍니다.
#   - 관측을 붙이려고 에이전트를 고치지 않는다는 것이 요점입니다. 얹는 자리는 `config` 한 곳입니다.
#   - 이어서 모호한 도구 두 개(`info`, `gym_guide`)로 `create_agent` 에이전트를 만들고,
#     방금 만든 함수로 `QUESTION` 을 물어 결과를 `vague_run` 에 담으세요.
#   - 그 기록에서 불린 도구 이름을 `tool_trace(vague_run)` 로 뽑아 `vague_tools` 에 담으세요.
#   - 여기서는 **틀리는 것이 정상**입니다. 요금과 상관없어 보이는 도구가 불리고,
#     답도 "요금 정보는 제공되지 않았습니다" 처럼 나옵니다. 그 화면을 보고 넘어가세요.
# 여기에 코드를 작성하세요


# ── 2단계: 이름과 설명을 고친 도구 만들기 ──────────────────────────────
#   - 도구 `membership_fee(plan: str) -> int` 를 만들고 `@tool` 을 붙이세요.
#   - 안에서는 `fee_of(plan)` 을 그대로 돌려주면 됩니다. 계산은 바꾸지 않습니다.
#   - **바꾸는 것은 이름과 docstring 뿐입니다.** docstring 에는 무엇을 받아 무엇을 돌려주는지
#     한 문장으로 적으세요(예: 회원권 이름을 받아 정가를 원 단위로 돌려준다).
#     모델은 그 한 줄을 읽고 이 도구를 고릅니다.
# 여기에 코드를 작성하세요


# ── 3단계: 고친 도구로 다시 돌리고 토큰 집계하기 ────────────────────────
#   - `membership_fee` 와 `gym_guide` 로 에이전트를 새로 만들어 `observed_invoke` 로
#     같은 `QUESTION` 을 묻고 결과를 `fixed_run` 에 담으세요.
#   - 불린 도구를 `fixed_tools` 에, 마지막 메시지의 답 본문을 `fixed_answer` 에 담으세요.
#     (답 본문은 `fixed_run['messages'][-1].text` 입니다.)
#   - 이 실행이 쓴 토큰을 모두 더해 `total_tokens` 에 담으세요.
#     한 번의 에이전트 실행에도 모델 호출은 여러 번입니다. `fixed_run['messages']` 를 훑으며
#     `AIMessage` 인 메시지의 `usage_metadata['total_tokens']` 를 더하면 됩니다
#     (`usage_metadata` 가 없는 메시지도 있으니 `or {}` 로 받아 `.get('total_tokens', 0)` 을 쓰세요).
# 여기에 코드를 작성하세요


# [자가채점]
# 콜백을 정말 얹었는지는 결과만 봐서는 알 수 없습니다 - 가짜 에이전트를 넣어 config 를 들여다봅니다
# (실제 모델 호출은 일어나지 않습니다).
from types import SimpleNamespace  # noqa: E402

seen = {}


def probe_invoke(payload, **kwargs):
    seen["config"] = kwargs.get("config")
    return {"messages": []}


observed_invoke(SimpleNamespace(invoke=probe_invoke), "점검용 질문")
assert seen.get("config"), "observed_invoke 안에서 invoke 에 config 를 함께 넘겨야 합니다"
assert seen["config"].get("callbacks") is handlers, \
    "config={'callbacks': handlers} 로 위에서 만든 handlers 를 그대로 넘기세요"

assert isinstance(vague_tools, list), "vague_tools 에는 tool_trace 가 돌려준 목록을 담으세요"

# 고친 도구는 모델을 부르지 않고 직접 확인합니다(비용이 들지 않는 검사입니다).
assert membership_fee.name == "membership_fee", "도구 이름을 membership_fee 로 지으세요"
assert membership_fee.description and len(membership_fee.description.strip()) >= 15, \
    "docstring 이 비었거나 너무 짧습니다. 무엇을 받아 무엇을 돌려주는지 한 문장으로 적으세요"
assert membership_fee.invoke({"plan": "3개월"}) == 135000, \
    "membership_fee 는 fee_of 의 값을 그대로 돌려줘야 합니다"

assert "membership_fee" in fixed_tools, \
    f"고친 뒤에도 요금 도구가 불리지 않았습니다: {fixed_tools}. docstring 을 더 분명하게 적어 보세요"
assert len(fixed_tools) <= 3, f"도구를 너무 많이 불렀습니다: {fixed_tools}"
assert "135,000" in fixed_answer or "135000" in fixed_answer, \
    f"답에 3개월 요금이 들어 있지 않습니다: {fixed_answer}"
assert total_tokens > 0, "실제 호출이라면 응답마다 토큰 수가 함께 옵니다. 합계가 0 이면 집계를 확인하세요"

print("\n문제 1 통과")
print("  모호한 쪽 :", vague_tools)
print("  고친 쪽   :", fixed_tools, f"(토큰 {total_tokens})")
print("  최종 답   :", fixed_answer)
print("\n[확인] Langfuse 의 Tracing → Traces 를 열어 방금 두 실행이 올라왔는지 보세요.")
print("       노트북을 닫아도 남는다는 것이 관측 도구를 붙이는 이유입니다.")
print("[더 볼 것] gym_guide 의 설명도 모호하게 바꾸면 무엇이 달라질까요?")
