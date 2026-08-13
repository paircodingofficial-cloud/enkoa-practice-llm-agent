"""📝 과제 문제 1: 어느 미들웨어가 에이전트 루프의 어느 자리를 쓰는지 표로 만들기

`# 여기에 코드를 작성하세요` 자리를 채우고 이 파일을 실행하세요.
아래 `# [자가채점]` 이 답을 검사하고, 통과하면 "문제 1 통과" 가 찍힙니다.

모델도 MCP 서버도 부르지 않는 문제라 키·인터넷 없이 몇 초 만에 끝납니다.

준비물: data/chinook.db(공통.py 가 임포트될 때 있는지 확인합니다)
실행: 이 파일이 있는 폴더에서  uv run 문제1_미들웨어_훅_자리.py
"""

from langchain.agents.middleware import (AgentMiddleware, HumanInTheLoopMiddleware,
                                         ModelCallLimitMiddleware, SummarizationMiddleware,
                                         TodoListMiddleware, ToolCallLimitMiddleware,
                                         ToolRetryMiddleware)

from 공통 import HOOKS

# 자리를 조사할 미들웨어. 아래 순서를 그대로 쓰세요(채점이 이 순서로 값을 비교합니다).
MIDDLEWARES = [TodoListMiddleware, SummarizationMiddleware, HumanInTheLoopMiddleware,
               ToolCallLimitMiddleware, ToolRetryMiddleware, ModelCallLimitMiddleware]


def main():
    # 문제 1. 어느 미들웨어가 어느 자리를 쓰는지 표로 만들기
    #   - 미들웨어 클래스 하나를 받아 그 클래스가 실제로 구현한 훅 이름만 `HOOKS` 순서대로
    #     리스트로 돌려주는 함수 `used_hooks(mw_class)` 를 만드세요.
    #     기본 클래스인 AgentMiddleware 의 같은 이름 함수와 다르면 그 자리를 쓴 것입니다.
    #     (getattr(mw_class, 훅이름) is not getattr(AgentMiddleware, 훅이름) 으로 봅니다.)
    #   - 그 함수를 써서 자리 이름을 키로 하는 딕셔너리를 만들어 변수 `hook_users` 에 담으세요.
    #     키는 `HOOKS` 여섯 개 전부이고, 값은 그 자리를 쓰는 미들웨어의 클래스 이름 리스트입니다.
    #     클래스 이름은 mw.__name__ 으로 꺼내고, 값의 순서는 위 `MIDDLEWARES` 순서를 따릅니다.
    #     아무도 쓰지 않는 자리는 빈 리스트로 둡니다.
    #   - 만든 표를 자리 하나에 한 줄씩 print 로 찍으세요.
    # 여기에 코드를 작성하세요

    # [자가채점]
    assert set(hook_users) == set(HOOKS), f"여섯 자리가 다 있어야 합니다: {sorted(hook_users)}"
    assert all(isinstance(v, list) for v in hook_users.values()), "값은 리스트여야 합니다"
    assert "TodoListMiddleware" in hook_users["wrap_model_call"], \
        f"wrap_model_call 자리가 다릅니다: {hook_users['wrap_model_call']}"
    assert "ToolRetryMiddleware" in hook_users["wrap_tool_call"], \
        f"wrap_tool_call 자리가 다릅니다: {hook_users['wrap_tool_call']}"
    assert "SummarizationMiddleware" in hook_users["before_model"], \
        f"before_model 자리가 다릅니다: {hook_users['before_model']}"
    assert {"HumanInTheLoopMiddleware", "ToolCallLimitMiddleware"} <= set(hook_users["after_model"]), \
        f"after_model 자리가 다릅니다: {hook_users['after_model']}"
    assert hook_users["before_agent"] == [], \
        f"before_agent 를 쓰는 미들웨어는 이 중에 없습니다: {hook_users['before_agent']}"
    print("문제 1 통과 -- 자리를 쓰는 미들웨어 수:",
          {h: len(hook_users[h]) for h in HOOKS})


if __name__ == "__main__":
    main()
