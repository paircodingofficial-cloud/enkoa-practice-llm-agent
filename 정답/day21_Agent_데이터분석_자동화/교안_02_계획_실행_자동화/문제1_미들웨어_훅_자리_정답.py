"""📝 과제 문제 1 정답: 어느 미들웨어가 에이전트 루프의 어느 자리를 쓰는지 표로 만들기

준비물: data/chinook.db
실행: 이 파일이 있는 폴더에서  uv run 문제1_미들웨어_훅_자리_정답.py
"""

import sys
from pathlib import Path

# 실습 폴더의 과제 파일들이 함께 쓰는 공통.py 를 그대로 씁니다
sys.path.append(str(Path(__file__).resolve().parents[3] / "day21_Agent_데이터분석_자동화" / "교안_02_계획_실행_자동화" / "과제"))

from langchain.agents.middleware import (AgentMiddleware, HumanInTheLoopMiddleware,
                                         ModelCallLimitMiddleware, SummarizationMiddleware,
                                         TodoListMiddleware, ToolCallLimitMiddleware,
                                         ToolRetryMiddleware)

from 공통 import HOOKS

MIDDLEWARES = [TodoListMiddleware, SummarizationMiddleware, HumanInTheLoopMiddleware,
               ToolCallLimitMiddleware, ToolRetryMiddleware, ModelCallLimitMiddleware]


def main():
    # 문제 1. 어느 미들웨어가 어느 자리를 쓰는지 표로 만들기
    def used_hooks(mw_class):
        """그 미들웨어가 실제로 구현한 훅 이름만 골라 돌려준다."""
        # 기본 클래스의 훅과 '다른 함수' 로 바뀌어 있으면 그 자리를 쓴 것이다
        return [h for h in HOOKS
                if getattr(mw_class, h) is not getattr(AgentMiddleware, h)]

    hook_users = {h: [mw.__name__ for mw in MIDDLEWARES if h in used_hooks(mw)] for h in HOOKS}
    for hook in HOOKS:
        print(f"{hook:16} {hook_users[hook]}")

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
