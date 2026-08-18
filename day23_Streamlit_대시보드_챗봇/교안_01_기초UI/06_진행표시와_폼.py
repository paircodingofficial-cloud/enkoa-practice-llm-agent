# 실행: uv run streamlit run 교안_01_기초UI/06_진행표시와_폼.py
#
# 교안 01: 진행 표시와 폼
# 오래 걸리는 일은 '지금 하고 있다'고 알려 주고, 입력이 여러 개면 한 번에 받습니다.
# 앞 시간의 재실행 모델 위에서 '언제 다시 실행되는가'를 우리가 조절하기 시작합니다.

import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import time

import streamlit as st

st.title("📗 진행 표시와 폼")
st.caption("오래 걸리는 일 알려 주기, 콜백으로 순서 잡기, 폼으로 한 번에 받기")

st.divider()

# =============================================================================
st.header("1. st.spinner: 짧은 작업 동안 도는 표시")
st.markdown(
    """
데이터를 읽거나 AI 를 부르는 동안 화면이 멈춘 것처럼 보이면 사용자는 앱이 고장 났다고 생각합니다.
`with st.spinner("...")` 블록 안의 코드가 도는 동안 문구와 함께 회전 표시가 나옵니다.
블록을 벗어나면 표시는 저절로 사라집니다.
"""
)

st.code(
    '''with st.spinner("데이터를 불러오는 중…"):
    time.sleep(1.5)          # 무거운 작업이라고 가정
st.success("완료")''',
    language="python",
)
st.caption("▼ 실제 실행 결과 (이 화면을 새로고침하면 회전 표시가 잠깐 보입니다)")

# with 블록을 벗어나면 스피너는 자동으로 사라진다. 따로 지우는 코드가 필요 없다.
with st.spinner("데이터를 불러오는 중…"):
    time.sleep(1.5)
st.success("완료")

# 🖐️ 직접 해보기: sleep 시간을 0.1 로 줄여 보세요. 너무 빠른 작업에 스피너를 달면
#               깜빡임만 남아 오히려 산만해집니다. 어느 정도부터 달 만한지 감을 잡아 보세요.

st.divider()

# =============================================================================
st.header("2. st.status: 여러 단계 작업의 진행")
st.markdown(
    """
단계가 여러 개면 스피너 하나로는 어디까지 갔는지 알 수 없습니다. `st.status` 는 접이식 상자를 만들고,
그 안에 **단계별 기록**을 쌓습니다. 끝나면 `status.update(...)` 로 라벨과 상태를 바꿉니다.

`state` 는 세 가지입니다: `"running"`(기본, 도는 중) · `"complete"`(성공) · `"error"`(실패).
"""
)

st.code(
    '''with st.status("파이프라인 실행 중…", expanded=True) as status:
    st.write("1) 데이터 불러오기")
    time.sleep(0.4)
    st.write("2) 전처리")
    time.sleep(0.4)
    st.write("3) 집계")
    time.sleep(0.4)
    # 끝났음을 라벨·상태로 알린다. state 를 안 바꾸면 계속 도는 것처럼 보인다.
    status.update(label="파이프라인 완료", state="complete", expanded=False)''',
    language="python",
)
st.caption("▼ 실제 실행 결과 (완료된 상자를 눌러 펼치면 단계 기록이 남아 있습니다)")

with st.status("파이프라인 실행 중…", expanded=True) as status:
    st.write("1) 데이터 불러오기")
    time.sleep(0.4)
    st.write("2) 전처리")
    time.sleep(0.4)
    st.write("3) 집계")
    time.sleep(0.4)
    # state 를 complete 로 바꿔야 회전 표시가 멈추고 체크 표시가 된다.
    status.update(label="파이프라인 완료", state="complete", expanded=False)

st.info(
    "`st.spinner` 와 `st.status` 의 갈림길: 단계가 하나면 spinner, "
    "여러 단계이거나 **끝난 뒤에도 무슨 일을 했는지 남겨야** 하면 status 입니다."
)

st.divider()

# =============================================================================
st.header("3. st.progress: 진행률 막대")
st.markdown(
    """
전체 개수를 아는 반복 작업(파일 100개 처리 등)은 **몇 퍼센트 왔는지** 보여 줄 수 있습니다.
`st.progress` 가 돌려준 객체에 `.progress(값, text=...)` 를 다시 부르면 **같은 막대가 갱신**됩니다.
값은 0~100 정수 또는 0.0~1.0 실수입니다.
"""
)

st.code(
    '''files = ["a.csv", "b.csv", "c.csv", "d.csv", "e.csv"]

bar = st.progress(0, text="시작")
for i, name in enumerate(files, start=1):
    time.sleep(0.2)                                  # 파일 하나 처리한다고 가정
    percent = int(i / len(files) * 100)               # 계산은 f-string 밖에서 미리
    bar.progress(percent, text=f"{name} 처리 완료 ({percent}%)")
bar.empty()                                           # 다 끝났으면 막대를 치운다''',
    language="python",
)
st.caption("▼ 실제 실행 결과")

files = ["a.csv", "b.csv", "c.csv", "d.csv", "e.csv"]
bar = st.progress(0, text="시작")
for i, name in enumerate(files, start=1):
    time.sleep(0.2)
    # 퍼센트를 f-string 안에서 계산하지 않고 위에서 변수로 빼 둔다(읽기 쉽다)
    percent = int(i / len(files) * 100)
    bar.progress(percent, text=f"{name} 처리 완료 ({percent}%)")
bar.empty()  # 남겨 두면 100% 막대가 계속 화면을 차지한다
st.success(f"{len(files)}개 파일 처리 완료")

# 🖐️ 직접 해보기: bar.empty() 를 지우고 새로고침해 보세요. 다 끝난 막대가 계속 남습니다.
#               st.progress 를 for 문 '안'으로 옮기면 어떻게 되는지도 확인해 보세요(막대가 5개 생깁니다).

st.divider()

# =============================================================================
st.header("4. 콜백: 재실행보다 먼저 실행되는 함수")
st.markdown(
    """
위젯에 `on_click`(버튼) 또는 `on_change`(값이 바뀌는 위젯)로 함수를 달면, 그 위젯을 조작했을 때
**스크립트 재실행이 시작되기 전에 그 함수가 먼저** 실행됩니다. 그래서 상태를 정리(기록·검증·초기화)한
뒤에 화면이 그려집니다.

콜백 안에서는 **위젯의 반환값을 쓸 수 없습니다**(아직 화면을 그리기 전이니까요).
그래서 위젯에 `key` 를 주고 `st.session_state[key]` 로 값을 읽습니다.
"""
)

st.code(
    '''if "log" not in st.session_state:
    st.session_state.log = []

def add_log():
    """입력창의 현재 값을 기록 목록에 덧붙인다(버튼 콜백)."""
    # 콜백은 위젯 반환값을 못 본다. key 로 session_state 에서 값을 읽는다.
    st.session_state.log.append(st.session_state.memo)

def clear_log():
    """기록 목록을 비운다(버튼 콜백)."""
    st.session_state.log = []

st.text_input("메모", key="memo")
st.button("기록에 추가", on_click=add_log)      # 재실행 '전에' add_log 가 돈다
st.button("비우기", on_click=clear_log)
st.write(st.session_state.log)''',
    language="python",
)
st.caption("▼ 실제 실행 결과 (메모를 적고 '기록에 추가' 를 눌러 보세요)")

if "log" not in st.session_state:
    st.session_state.log = []


def add_log():
    """입력창의 현재 값을 기록 목록에 덧붙인다(버튼 콜백)."""
    # key="memo" 로 준 위젯의 현재 값이 st.session_state.memo 에 들어 있다
    st.session_state.log.append(st.session_state.memo)


def clear_log():
    """기록 목록을 비운다(버튼 콜백)."""
    st.session_state.log = []


st.text_input("메모", key="memo")
st.button("기록에 추가", on_click=add_log)
st.button("비우기", on_click=clear_log)
st.write(st.session_state.log)

st.warning(
    "`if st.button(...):` 안에서 처리하는 방식과 결과는 비슷해 보이지만 순서가 다릅니다. "
    "콜백은 **재실행 전에** 돌기 때문에, 화면을 그리는 코드가 이미 정리된 상태를 보고 그립니다."
)

st.divider()

# =============================================================================
st.header("5. st.form: 입력을 한 번에 받기")
st.markdown(
    """
지금까지 배운 위젯은 **하나만 건드려도 즉시 재실행**됩니다. 입력칸이 다섯 개인 신청서라면
글자를 칠 때마다 앱이 다시 도는 셈이라 낭비이고, 절반만 채운 상태로 처리될 수도 있습니다.

`with st.form(...)` 안에 넣은 위젯은 **제출 버튼을 누를 때까지 재실행을 일으키지 않습니다**.
폼에는 `st.form_submit_button` 이 **반드시 하나** 있어야 하고, 그 버튼에도 `on_click` 콜백을 달 수 있습니다.
"""
)

st.code(
    '''if "applied" not in st.session_state:
    st.session_state.applied = None

def save_form():
    """폼에 입력된 값들을 한꺼번에 읽어 저장한다(제출 콜백)."""
    # 폼 위젯도 key 로 값을 읽는다(제출 시점의 값이 들어 있다)
    st.session_state.applied = {
        "이름": st.session_state.f_name,
        "인원": st.session_state.f_size,
    }

with st.form("apply"):
    st.text_input("이름", key="f_name")
    st.number_input("인원", min_value=1, max_value=10, value=2, key="f_size")
    # 폼에는 submit 버튼이 반드시 하나 있어야 한다(없으면 에러)
    st.form_submit_button("신청", on_click=save_form)

if st.session_state.applied:
    st.success(f"접수: {st.session_state.applied}")''',
    language="python",
)
st.caption("▼ 실제 실행 결과 (이름·인원을 바꿔도 '신청' 을 누를 때까지 아래가 안 바뀝니다)")

if "applied" not in st.session_state:
    st.session_state.applied = None


def save_form():
    """폼에 입력된 값들을 한꺼번에 읽어 저장한다(제출 콜백)."""
    # 제출 버튼의 콜백. 폼 안 위젯 값들을 key 로 한꺼번에 읽는다.
    st.session_state.applied = {
        "이름": st.session_state.f_name,
        "인원": st.session_state.f_size,
    }


with st.form("apply"):
    st.text_input("이름", key="f_name")
    st.number_input("인원", min_value=1, max_value=10, value=2, key="f_size")
    st.form_submit_button("신청", on_click=save_form)

if st.session_state.applied:
    st.success(f"접수: {st.session_state.applied}")

# 🖐️ 직접 해보기: with st.form("apply"): 줄을 지우고 들여쓰기를 풀어 보세요(폼 없이).
#               이름을 한 글자 칠 때마다 아래가 반응합니다. 폼이 막아 주던 것이 무엇인지 보입니다.

st.info(
    "폼 안에서는 위젯을 조작해도 재실행이 안 되므로, **다른 위젯 값에 따라 선택지가 바뀌는 화면**은 "
    "폼으로 만들 수 없습니다. 그런 화면은 폼 대신 콜백을 씁니다."
)

st.divider()
st.subheader("이번 강의 정리")
st.markdown(
    """
- `st.spinner` : 단계 하나짜리 작업 동안 회전 표시
- `st.status` : 여러 단계 진행을 접이식 상자에 기록, 끝나면 `status.update(state="complete")`
- `st.progress` : 개수를 아는 반복의 진행률. 돌려받은 객체의 `.progress()` 로 갱신, `.empty()` 로 치우기
- 콜백(`on_click`/`on_change`) : **재실행보다 먼저** 실행. 값은 `key` 로 `session_state` 에서 읽는다
- `st.form` : 제출할 때까지 재실행을 막는다. `st.form_submit_button` 이 반드시 하나 필요
"""
)
st.markdown("⏭️ **다음 시간**: 부분 재실행 (`교안_01_기초UI/07_부분_재실행.py`)")
