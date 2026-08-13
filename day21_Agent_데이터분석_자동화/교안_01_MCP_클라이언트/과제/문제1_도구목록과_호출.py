"""📝 과제 문제 1: 파일시스템 서버에 붙어 도구 목록·명세를 보고 직접 호출하기

`# 여기에 코드를 작성하세요` 자리를 채우고 이 파일을 실행하세요.
아래 `# [자가채점]` 이 답을 검사하고, 통과하면 "문제 1 통과" 가 찍힙니다.

MCP 도구는 비동기 전용이라 `await 도구.ainvoke({...})` 로 부릅니다.

준비물: npx(Node.js)
실행: 이 파일이 있는 폴더에서  uv run 문제1_도구목록과_호출.py
"""

import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient

from 공통 import DATA_DIR, FILESYSTEM


async def main():
    # 문제 1. 파일시스템 서버에 붙어 도구 목록·명세를 보고 직접 호출하기
    #   - MultiServerMCPClient 에 {"files": FILESYSTEM} 을 넘겨 만들고, get_tools() 를 await 합니다.
    #   - 받은 도구 리스트를 변수 `fs_tools` 에 담으세요.
    #   - 이름으로 꺼내 쓸 수 있게 {이름: 도구} 딕셔너리를 만들어 변수 `fs_by_name` 에 담으세요.
    #   - "list_directory" 도구가 받는 인자 이름들을 리스트로 만들어 변수 `list_dir_args` 에 담으세요.
    #     (도구의 .args 는 딕셔너리입니다. 키만 모으면 됩니다.)
    #   - 그 도구를 await ...ainvoke({"path": str(DATA_DIR)}) 로 부르고,
    #     돌아온 값에서 [0]["text"] 를 꺼내 변수 `data_listing` 에 담으세요.
    # 여기에 코드를 작성하세요

    # [자가채점]
    assert len(fs_tools) >= 10, f"도구가 너무 적습니다: {len(fs_tools)}개"
    assert "list_directory" in fs_by_name, "list_directory 도구가 없습니다"
    assert list_dir_args == ["path"], f"인자 이름이 다릅니다: {list_dir_args}"
    assert isinstance(data_listing, str) and "cvs_sales.csv" in data_listing, "data 폴더 목록이 아닙니다"
    print("문제 1 통과 -- 도구", len(fs_tools), "개 · 인자:", list_dir_args)


if __name__ == "__main__":
    asyncio.run(main())
