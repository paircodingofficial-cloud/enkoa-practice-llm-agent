# 실행: uv run streamlit run 교안_01_기초UI/05_상태와_캐싱.py
#
# 교안 01: 상태 유지(session_state)와 캐싱(cache)
# 재실행 모델에서 '값을 기억'하고 '무거운 일을 한 번만' 하게 만드는 두 도구입니다.

import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import time
from pathlib import Path

import pandas as pd
import streamlit as st

# 이 파일이 어디서 실행되든 이미지를 찾을 수 있게 절대경로로 만든다
# (uv run streamlit run 을 어느 폴더에서 하느냐에 따라 상대경로가 어긋난다)
IMAGES = Path(__file__).resolve().parent.parent / "images"

st.title("📗 상태 유지와 캐싱")
st.caption("재실행 모델의 두 필수 도구: st.session_state 와 st.cache_data")

st.divider()

# =============================================================================
st.header("1. 왜 필요한가: 재실행 모델 복습")
st.markdown(
    """
Streamlit은 위젯을 조작할 때마다 스크립트를 **처음부터 다시 실행**합니다. 그래서 그냥 만든
파이썬 변수는 재실행 때 **초기화**됩니다. 두 가지 문제를 각각 해결합니다.

- 값이 **유지**되어야 한다 → `st.session_state`
- 무거운 계산·로딩을 **매번 다시 하면 느리다** → `st.cache_data` / `st.cache_resource`
"""
)

st.image(str(IMAGES / "streamlit_rerun.png"), width=900)
st.caption("같은 버튼을 세 번 눌러도 보통 변수는 계속 0 입니다. 재실행 때마다 새로 만들어지기 때문입니다.")

st.divider()

# =============================================================================
st.header("2. st.session_state: 재실행에도 값 기억")
st.markdown(
    "딕셔너리처럼 값을 저장합니다. **키가 없을 때만 초기화**하고, 버튼 등으로 값을 바꿉니다."
)

st.code(
    '''if "count" not in st.session_state:
    st.session_state.count = 0

col1, col2 = st.columns(2)
if col1.button("➕ 증가"):
    st.session_state.count += 1
if col2.button("🔄 초기화"):
    st.session_state.count = 0

st.metric("현재 카운트", st.session_state.count)''',
    language="python",
)
st.caption("▼ 실제 실행 결과: 버튼을 눌러도 값이 유지됩니다")
if "count" not in st.session_state:
    st.session_state.count = 0
col1, col2 = st.columns(2)
if col1.button("➕ 증가"):
    st.session_state.count += 1
if col2.button("🔄 초기화"):
    st.session_state.count = 0
st.metric("현재 카운트", st.session_state.count)

# 🖐️ 직접 해보기: 위 초기화 부분에서 if 문을 빼고 st.session_state.count = 0 만 남겨 보세요.
#               버튼을 눌러도 숫자가 오르지 않습니다. 왜 그런지 재실행 모델로 설명해 보고 되돌리세요.

st.info("챗봇의 '대화 이력'도 바로 이 session_state 에 리스트로 쌓아 유지합니다(교안 02).")

st.divider()

# =============================================================================
st.header("3. st.cache_data: 데이터 로딩·계산 캐싱")
st.markdown(
    """
`@st.cache_data` 를 함수에 붙이면, **같은 인자로 다시 부를 때 계산을 건너뛰고** 저장된 결과를 돌려줍니다.
CSV 읽기·API 호출·무거운 집계에 씁니다. 아래는 3초 걸리는 함수를 캐싱한 예입니다.
"""
)

st.code(
    '''@st.cache_data
def load_slow():
    time.sleep(3)          # 느린 작업 흉내
    return pd.DataFrame({"값": [1, 2, 3]})

data = load_slow()   # 처음: 3초, 이후: 즉시(캐시)
st.dataframe(data)''',
    language="python",
)
st.caption("▼ 실제 실행 결과: 처음만 느리고, 재실행 때는 즉시 나옵니다")


@st.cache_data
def load_slow():
    time.sleep(3)
    return pd.DataFrame({"값": [1, 2, 3]})


data = load_slow()
st.dataframe(data)

# 🖐️ 직접 해보기: @st.cache_data 줄을 잠시 주석 처리하고 위 카운터 버튼을 눌러 보세요.
#               재실행마다 3초를 기다리게 됩니다. 확인했으면 주석을 풀어 되돌리세요.

st.divider()

# =============================================================================
st.header("4. cache_data vs cache_resource")
st.markdown(
    """
| 데코레이터 | 캐싱 대상 | 예시 |
| --- | --- | --- |
| `@st.cache_data` | **데이터**(복사해서 반환) | DataFrame, API 응답, 계산 결과 |
| `@st.cache_resource` | **자원**(하나를 공유) | DB 연결, ML 모델, 검색 인덱스 |

무거운 **모델·연결·RAG 검색 인덱스**처럼 여러 번 만들면 안 되는 것은 `cache_resource` 로 **한 번만** 만들어 공유합니다.
다음 단원에서 RAG 인덱스를 `cache_resource` 로 올려 챗봇에 연결합니다.
"""
)

st.code(
    '''@st.cache_resource
def get_model():
    # 무거운 모델/연결을 한 번만 만들어 공유
    return {"name": "demo-model", "loaded": True}

model = get_model()
st.write(model)''',
    language="python",
)
st.caption("▼ 실제 실행 결과")


@st.cache_resource
def get_model():
    return {"name": "demo-model", "loaded": True}


model = get_model()
st.write(model)

# 🖐️ 직접 해보기: get_model 의 데코레이터를 cache_resource 대신 cache_data 로 바꿔 보세요.
#               둘 다 화면은 같아 보이지만, 반환된 것이 원본 자체인지 복사본인지가 다릅니다.
#               모델·DB 연결처럼 "하나만 있어야 하는 것"에 복사본이 생기면 왜 곤란할지 생각해 보세요.

st.divider()

# =============================================================================
st.header("5. 캐시 유효시간(ttl)과 비우기(clear)")
st.markdown(
    """
캐시는 한 번 저장하면 계속 그 값을 돌려줍니다. 그래서 **원본이 바뀌는 데이터**(API 응답·오늘 매출)는
오래된 값을 붙잡고 있게 됩니다. 다루는 방법이 두 가지입니다.

- `@st.cache_data(ttl=60)` : 저장한 지 **60초가 지나면 버리고** 다시 계산합니다(ttl = time to live, 초 단위).
- `함수.clear()` : 그 함수의 캐시를 **지금 즉시 비웁니다**. 사용자에게 "새로 고침" 버튼을 줄 때 씁니다.
- `st.cache_data.clear()` : 앱의 **모든** `cache_data` 캐시를 비웁니다.

`show_spinner` 로 캐시가 비어 처음 계산할 때 뜨는 문구도 바꿀 수 있습니다.
"""
)

st.code(
    '''@st.cache_data(ttl=60, show_spinner="시세를 불러오는 중…")
def fetch_price():
    return {"조회시각": time.strftime("%H:%M:%S")}   # 매번 다른 값이라 캐시 여부가 눈에 보인다

price = fetch_price()
st.write(price)

if st.button("캐시 비우고 다시 불러오기"):
    fetch_price.clear()      # 이 함수의 캐시만 비운다
    st.rerun()               # 비운 뒤 화면을 다시 그려야 새 값이 보인다''',
    language="python",
)
st.caption("▼ 실제 실행 결과 (버튼을 누르면 조회시각이 바뀌고, 그냥 새로고침하면 그대로입니다)")


# ttl=60: 저장 후 60초가 지나면 캐시를 버리고 함수를 다시 부른다
@st.cache_data(ttl=60, show_spinner="시세를 불러오는 중…")
def fetch_price():
    # 호출 시각을 담아 둔다. 캐시가 살아 있으면 이 값이 안 바뀐다.
    return {"조회시각": time.strftime("%H:%M:%S")}


price = fetch_price()
st.write(price)

if st.button("캐시 비우고 다시 불러오기"):
    fetch_price.clear()  # 데코레이터가 함수에 붙여 준 메서드. 이 함수의 캐시만 지운다.
    st.rerun()  # 캐시를 비우기만 하면 화면은 그대로다. 다시 그려야 새 값이 나온다.

# 🖐️ 직접 해보기: 위 버튼 대신 브라우저 새로고침만 여러 번 눌러 보세요. 조회시각이 그대로입니다.
#               ttl=60 을 ttl=3 으로 바꾸고 3초 뒤 새로고침하면 값이 바뀝니다.

st.info(
    "판단 기준: 원본이 안 바뀌는 데이터(고정 CSV)는 `ttl` 없이, "
    "바뀌는 데이터(API·오늘 집계)는 `ttl` 을 주고, 사용자가 직접 갱신해야 하면 `.clear()` 버튼을 답니다."
)

st.divider()
st.subheader("이번 강의 정리")
st.markdown(
    """
- 재실행 모델: 일반 변수는 초기화된다
- `st.session_state` : 재실행에도 **값 유지**(카운터·대화 이력)
- `@st.cache_data` : **데이터·계산** 캐싱(CSV·API·집계)
- `@st.cache_resource` : **자원**(모델·연결·검색 인덱스) 한 번만 만들어 공유
- `ttl=초` 로 오래된 캐시를 자동 폐기, `함수.clear()` 로 즉시 비우기
"""
)
st.markdown("⏭️ **다음 시간**: 진행 표시와 폼 (`교안_01_기초UI/06_진행표시와_폼.py`)")
